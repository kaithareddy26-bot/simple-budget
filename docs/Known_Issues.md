# Known Issues & Limitations

Cross-Platform Budgeting Application

## P0 (Critical)

None currently known.

---

## P1 (Major)

1. No rate limiting on API endpoints.
2. No password reset email functionality.
3. No centralized/structured production observability stack.

Workarounds:

- Use WAF/API gateway throttling rules at the edge until app-level rate limiting is added.
- Handle password resets manually through administrator support workflow.
- Configure external log aggregation (for example, platform logs + alert rules) for operational visibility.

---

## P2 (Minor)

1. UI spacing inconsistencies on smaller mobile screens.
2. Error messages could be more user-friendly in some cases.
3. No data export functionality (CSV/PDF).

Workarounds:

- Use device rotation or desktop viewport for improved layout on small screens.
- Rely on API error responses and form validation hints when troubleshooting failed actions.
- Use API-based extraction scripts for temporary reporting needs.

---

## P3 (Trivial)

1. Minor UI alignment inconsistencies.
2. No dark mode support.

Workarounds:

- Use standard/light theme for consistent visual behavior.

---

## Security Limitations

- No multi-factor authentication.
- No brute-force protection on login.
- Basic CORS configuration.

Workarounds:

- Restrict origin allowlist by environment.
- Add reverse-proxy request throttling and temporary IP blocking for repeated failed logins.

---

## Performance Limitations

- No load testing under high concurrency.
- No caching implemented.
- No database indexing optimization documented.

Workarounds:

- Scale service instances vertically/horizontally based on observed load.
- Add targeted indexes for slow queries identified in database metrics.

---

## Future Enhancements

- Budget visualization charts
- Email notifications
- Rate limiting
- Monitoring dashboard
- Data export features
