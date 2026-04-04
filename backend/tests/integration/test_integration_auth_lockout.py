"""
Integration tests: DB-backed login lockout (Sprint 3)

These tests verify that lockout state lives in PostgreSQL, not in memory.
Key assertions beyond unit tests:
  - The login_attempts DB row is created on the first failure
  - attempt_count increments correctly per failure
  - locked_until is populated once the threshold is crossed
  - Lockout survives across separate HTTP requests (proves DB persistence)
  - Successful login deletes the row (counter truly resets)
  - Lockout is scoped per email (user B is unaffected by user A's lockout)

Run:
    pytest tests/integration/test_integration_auth_lockout.py -v
Requires:
    docker-compose -f docker-compose.test.yml up -d
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import text
from tests.integration.conftest import register_and_login, auth_headers


class TestDBBackedLockout:
    """
    Core lockout behaviour — verified through both the API response
    and direct DB state inspection.
    """

    EMAIL = "lockout@int.com"
    PASSWORD = "correctpass123"
    WRONG = "wrongpassword999"

    @pytest.fixture(autouse=True)
    def register_user(self, integration_client, db_session):
        """Register the test user; expose db_session for raw SQL checks."""
        integration_client.post(
            "/api/v1/auth/register",
            json={"email": self.EMAIL, "password": self.PASSWORD,
                  "full_name": "Lockout Tester"},
        )
        self.db = db_session

    def _login(self, client, password=None):
        return client.post(
            "/api/v1/auth/login",
            json={"email": self.EMAIL, "password": password or self.WRONG},
        )

    def _row(self):
        """Read the login_attempts row directly from the DB."""
        return self.db.execute(
            text("SELECT * FROM login_attempts WHERE email = :e"),
            {"e": self.EMAIL},
        ).fetchone()

    # ── DB row lifecycle ──────────────────────────────────────────────────────

    def test_first_failure_creates_db_row(self, integration_client):
        """A failed login must insert a row in login_attempts."""
        self._login(integration_client)
        row = self._row()
        assert row is not None, "No row created after first failure"
        assert row.attempt_count == 1

    def test_count_increments_per_failure(self, integration_client):
        """Each additional failure increments attempt_count by exactly 1."""
        for expected in range(1, 5):
            self._login(integration_client)
            assert self._row().attempt_count == expected

    def test_locked_until_set_after_threshold(self, integration_client):
        """locked_until must be populated once 5 failures are recorded."""
        for _ in range(5):
            self._login(integration_client)

        row = self._row()
        assert row is not None
        assert row.locked_until is not None, (
            "locked_until should be set after 5 failures"
        )
        # locked_until must be in the future
        locked_naive = row.locked_until
        if hasattr(locked_naive, "tzinfo") and locked_naive.tzinfo is None:
            locked_naive = locked_naive.replace(tzinfo=timezone.utc)
        assert locked_naive > datetime.now(timezone.utc), (
            "locked_until should be a future timestamp"
        )

    def test_sixth_attempt_blocked_with_lockout_message(self, integration_client):
        """The request immediately after lockout must return 401 with 'Too many'."""
        for _ in range(5):
            self._login(integration_client)

        resp = self._login(integration_client)
        assert resp.status_code == 401
        assert "Too many" in resp.json()["message"], (
            f"Expected lockout message, got: {resp.json()['message']}"
        )

    # ── Persistence across requests ───────────────────────────────────────────

    def test_lockout_persists_across_separate_requests(self, integration_client):
        """
        Three separate HTTP requests all see the same lockout.
        If lockout were in-memory, a simulated 'new process' would not
        see it.  With DB backing, every request queries the same table.
        """
        for _ in range(5):
            self._login(integration_client)

        for i in range(3):
            resp = self._login(integration_client)
            assert resp.status_code == 401, (
                f"Request {i+1} after lockout should still be blocked"
            )

    # ── Success clears the record ─────────────────────────────────────────────

    def test_success_deletes_db_row(self, integration_client):
        """A successful login must delete the login_attempts row."""
        self._login(integration_client)
        self._login(integration_client)

        resp = self._login(integration_client, password=self.PASSWORD)
        assert resp.status_code == 200, f"Login should succeed: {resp.json()}"

        assert self._row() is None, (
            "login_attempts row should be deleted after successful login"
        )

    def test_counter_restarts_after_success(self, integration_client):
        """After success clears the row, failures start counting from 1 again."""
        self._login(integration_client)
        self._login(integration_client)
        self._login(integration_client, password=self.PASSWORD)  # succeed

        self._login(integration_client)  # fail once after reset
        row = self._row()
        assert row is not None
        assert row.attempt_count == 1, (
            f"Counter should restart at 1, got {row.attempt_count}"
        )

    def test_successful_first_login_leaves_no_row(self, integration_client):
        """A user who always succeeds should never have a login_attempts row."""
        resp = self._login(integration_client, password=self.PASSWORD)
        assert resp.status_code == 200
        assert self._row() is None, (
            "Successful login should not create a login_attempts row"
        )

    # ── Per-email isolation ───────────────────────────────────────────────────

    def test_lockout_does_not_affect_other_email(self, integration_client):
        """Locking email A must not affect email B."""
        other_email = "other_lockout@int.com"
        integration_client.post(
            "/api/v1/auth/register",
            json={"email": other_email, "password": self.PASSWORD,
                  "full_name": "Other"},
        )
        # Lock self.EMAIL
        for _ in range(5):
            self._login(integration_client)

        resp = integration_client.post(
            "/api/v1/auth/login",
            json={"email": other_email, "password": self.PASSWORD},
        )
        assert resp.status_code == 200, (
            f"Unrelated user should not be locked out, got {resp.status_code}"
        )


class TestInMemoryMigrationRegression:
    """
    Prove the in-memory dict from Sprint 2 is gone.

    If lockout were still in-memory, failures recorded through the API
    would not be visible via direct DB query.  With the DB implementation,
    they must match exactly.
    """

    def test_api_failures_visible_in_db(self, integration_client, db_session):
        """
        Record 3 failures through the HTTP API.
        Query the DB directly — attempt_count must equal 3.
        If it is 0, the lockout is still in-memory.
        """
        email = "migration_check@int.com"
        integration_client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "correct123", "full_name": "M"},
        )

        for _ in range(3):
            integration_client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "wrong"},
            )

        row = db_session.execute(
            text("SELECT attempt_count FROM login_attempts WHERE email = :e"),
            {"e": email},
        ).fetchone()

        assert row is not None, (
            "No row in login_attempts — lockout may still be in-memory"
        )
        assert row.attempt_count == 3, (
            f"Expected 3 failures in DB, got {row.attempt_count}. "
            "If 0: lockout is still in-memory (Sprint 2 code not replaced)."
        )