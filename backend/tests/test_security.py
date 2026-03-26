"""
Sprint 2 — Security hardening tests.

Covers:
  A. Login lockout (per-email, application layer)
  B. Rate limiting on auth endpoints (per-IP, network layer)
  C. CORS headers (method restrictions)
  D. Secret key validation

Run alone:
    pytest tests/test_security.py -v

Run with coverage:
    pytest tests/test_security.py --cov=app --cov-report=term-missing -v
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from tests.conftest import (
    make_user,
    FIXED_USER_ID,
    assert_error_shape,
)
from app.schemas.error_schemas import ErrorCodes


# ===========================================================================
# A. LOGIN LOCKOUT TESTS  (AuthService layer — no HTTP client needed)
# ===========================================================================

class TestLoginLockout:
    """
    Unit tests for the per-email sliding-window lockout in AuthService.
    These test the service directly — no HTTP overhead.
    """

    def setup_method(self):
        """Fresh mock repo + service + cleared attempt state for each test."""
        from app.services.auth_service import AuthService, reset_attempts_for_testing
        self.reset = reset_attempts_for_testing
        self.mock_repo = Mock()
        self.service = AuthService(self.mock_repo)
        self.email = "lockout@example.com"
        reset_attempts_for_testing(self.email)

    def teardown_method(self):
        self.reset(self.email)

    def _make_failing_login(self):
        """Helper: configure repo so login fails (wrong password)."""
        self.mock_repo.get_by_email.return_value = make_user(email=self.email)
        with patch("app.services.auth_service.verify_password", return_value=False):
            with pytest.raises(ValueError):
                self.service.login_user(self.email, "wrongpassword")

    def test_single_failure_does_not_lock(self):
        """One bad attempt should not trigger lockout."""
        self._make_failing_login()
        # Second attempt should still reach credential check, not lockout
        self.mock_repo.get_by_email.return_value = make_user(email=self.email)
        with patch("app.services.auth_service.verify_password", return_value=False):
            with pytest.raises(ValueError) as exc:
                self.service.login_user(self.email, "wrongpassword")
        # Should be invalid credentials, NOT a lockout message
        assert "Too many" not in str(exc.value)

    def test_lockout_triggers_after_max_attempts(self):
        """After MAX_ATTEMPTS failures, next attempt raises lockout error."""
        from app.config import get_settings
        max_attempts = get_settings().LOGIN_LOCKOUT_MAX_ATTEMPTS

        for _ in range(max_attempts):
            self._make_failing_login()

        # This attempt should be blocked before even hitting the DB
        with pytest.raises(ValueError) as exc:
            self.service.login_user(self.email, "anypassword")

        assert "Too many" in str(exc.value)
        assert ErrorCodes.AUTH_INVALID_CREDENTIALS in str(exc.value)
        # Confirm DB was NOT called on the locked-out attempt
        call_count_before = self.mock_repo.get_by_email.call_count
        assert call_count_before == max_attempts  # no extra call

    def test_successful_login_clears_failure_counter(self):
        """A successful login resets the failure count."""
        # Fail twice
        self._make_failing_login()
        self._make_failing_login()

        # Succeed once
        self.mock_repo.get_by_email.return_value = make_user(email=self.email)
        with patch("app.services.auth_service.verify_password", return_value=True):
            with patch("app.services.auth_service.create_access_token", return_value="tok"):
                self.service.login_user(self.email, "correctpassword")

        # Now fail again — counter should be reset, no lockout yet
        self._make_failing_login()
        with patch("app.services.auth_service.verify_password", return_value=False):
            self.mock_repo.get_by_email.return_value = make_user(email=self.email)
            with pytest.raises(ValueError) as exc:
                self.service.login_user(self.email, "wrongpassword")
        assert "Too many" not in str(exc.value)

    def test_lockout_window_expires(self):
        """Attempts older than the window do not count toward lockout."""
        from app.config import get_settings
        from app.services import auth_service as svc_module

        max_attempts = get_settings().LOGIN_LOCKOUT_MAX_ATTEMPTS
        window_minutes = get_settings().LOGIN_LOCKOUT_WINDOW_MINUTES

        # Inject MAX_ATTEMPTS failures that are just outside the window
        old_time = datetime.utcnow() - timedelta(minutes=window_minutes + 1)
        svc_module._failed_attempts[self.email] = [old_time] * max_attempts

        # Next attempt should NOT be locked (old failures have expired)
        self.mock_repo.get_by_email.return_value = make_user(email=self.email)
        with patch("app.services.auth_service.verify_password", return_value=False):
            with pytest.raises(ValueError) as exc:
                self.service.login_user(self.email, "wrongpassword")
        assert "Too many" not in str(exc.value)

    def test_nonexistent_user_still_records_failure(self):
        """Failed lookup (email not found) should record a failure attempt."""
        from app.services import auth_service as svc_module
        self.mock_repo.get_by_email.return_value = None

        with pytest.raises(ValueError):
            self.service.login_user(self.email, "password")

        assert len(svc_module._failed_attempts[self.email]) == 1

    def test_lockout_is_per_email_not_global(self):
        """Locking out one email must not affect a different email."""
        from app.config import get_settings
        other_email = "other@example.com"
        from app.services.auth_service import reset_attempts_for_testing
        reset_attempts_for_testing(other_email)

        max_attempts = get_settings().LOGIN_LOCKOUT_MAX_ATTEMPTS

        # Lock out self.email
        for _ in range(max_attempts):
            self._make_failing_login()

        # other_email should still work
        self.mock_repo.get_by_email.return_value = make_user(email=other_email)
        with patch("app.services.auth_service.verify_password", return_value=True):
            with patch("app.services.auth_service.create_access_token", return_value="tok"):
                token = self.service.login_user(other_email, "correctpassword")
        assert token == "tok"

        reset_attempts_for_testing(other_email)


# ===========================================================================
# B. RATE LIMITING TESTS  (HTTP layer via TestClient)
# ===========================================================================

class TestRateLimiting:
    """
    Integration tests for slowapi rate limiting on auth endpoints.
    These hit the real FastAPI app through TestClient.

    Note: slowapi uses an in-memory counter that persists across requests
    within the same TestClient session. Tests clear the limiter state by
    using a fresh client fixture per test (each fixture call = new app state).
    """

    def test_login_rate_limit_returns_429_after_threshold(self, unauth_client):
        """POST /auth/login allows N requests then returns 429."""
        client = unauth_client["client"]
        svc = unauth_client["auth_service"]
        # Make every login attempt fail so we don't clear the counter
        svc.login_user.side_effect = ValueError(
            f"{ErrorCodes.AUTH_INVALID_CREDENTIALS}:Invalid email or password"
        )

        responses = []
        for _ in range(10):
            resp = client.post(
                "/api/v1/auth/login",
                json={"email": "test@example.com", "password": "wrong"},
            )
            responses.append(resp.status_code)

        # Should see at least one 429 in the list
        assert 429 in responses, (
            f"Expected a 429 after repeated login attempts, got: {responses}"
        )

    def test_register_rate_limit_returns_429_after_threshold(self, unauth_client):
        """POST /auth/register allows N requests then returns 429."""
        client = unauth_client["client"]
        svc = unauth_client["auth_service"]
        svc.register_user.side_effect = ValueError(
            f"{ErrorCodes.USER_EXISTS}:Already exists"
        )

        responses = []
        for _ in range(10):
            resp = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "spam@example.com",
                    "password": "password123",
                    "full_name": "Spam User",
                },
            )
            responses.append(resp.status_code)

        assert 429 in responses, (
            f"Expected a 429 after repeated register attempts, got: {responses}"
        )

    def test_health_endpoint_not_rate_limited(self, unauth_client):
        """GET /health should never return 429 — it has no rate limit decorator."""
        client = unauth_client["client"]
        for _ in range(20):
            resp = client.get("/health")
            assert resp.status_code == 200, (
                f"Health endpoint should not be rate limited, got {resp.status_code}"
            )


# ===========================================================================
# C. CORS HEADER TESTS
# ===========================================================================

class TestCORSHeaders:
    """
    Verify CORS is locked down to specific methods only.
    Tightened in Sprint 2: allow_methods changed from ["*"] to ["GET","POST","PUT"].
    """

    def test_cors_preflight_allows_post(self, unauth_client):
        """OPTIONS preflight for POST should succeed from an allowed origin."""
        client = unauth_client["client"]
        resp = client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        # 200 or 204 means the preflight was accepted
        assert resp.status_code in (200, 204)

    def test_cors_allowed_origin_present_in_response(self, unauth_client):
        """Responses to requests from an allowed origin should carry CORS headers."""
        client = unauth_client["client"]
        svc = unauth_client["auth_service"]
        svc.login_user.side_effect = ValueError(
            f"{ErrorCodes.AUTH_INVALID_CREDENTIALS}:bad creds"
        )

        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "a@example.com", "password": "pass"},
            headers={"Origin": "http://localhost:3000"},
        )
        assert "access-control-allow-origin" in resp.headers

    def test_cors_preflight_rejects_delete(self, unauth_client):
        """
        OPTIONS preflight for DELETE should be rejected — DELETE is not in
        our allow_methods list after Sprint 2 tightening.
        """
        client = unauth_client["client"]
        resp = client.options(
            "/api/v1/expenses",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "DELETE",
            },
        )
        # Either the preflight is rejected (400/403) OR the
        # Allow header does not include DELETE
        if resp.status_code in (200, 204):
            allow = resp.headers.get("access-control-allow-methods", "")
            assert "DELETE" not in allow, (
                "DELETE should not be in CORS allowed methods after Sprint 2"
            )


# ===========================================================================
# D. SECRET KEY VALIDATION
# ===========================================================================

class TestSecretKeyConfig:
    """
    Verify the application does not ship with the old placeholder secret.
    """

    def test_secret_key_is_not_original_placeholder(self):
        """SECRET_KEY must not be the original insecure default from pre-Sprint-2."""
        from app.config import get_settings
        settings = get_settings()
        assert settings.SECRET_KEY != "your-secret-key-change-in-production", (
            "SECRET_KEY is still the original insecure placeholder. "
            "Set a real value in .env."
        )

    def test_secret_key_has_minimum_length(self):
        """SECRET_KEY should be at least 32 characters."""
        from app.config import get_settings
        settings = get_settings()
        assert len(settings.SECRET_KEY) >= 32, (
            f"SECRET_KEY is only {len(settings.SECRET_KEY)} chars — "
            "minimum 32 required for HS256 security."
        )

    def test_algorithm_is_hs256(self):
        """JWT algorithm should be HS256 (as designed)."""
        from app.config import get_settings
        assert get_settings().ALGORITHM == "HS256"