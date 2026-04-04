# API Documentation

Cross-Platform Budgeting Application REST API

## Base URL

Production:
https://<your-backend-url>.onrender.com/api/v1

Local:
http://localhost:8000/api/v1

---

## Authentication

JWT-based authentication.

Header format:

Authorization: Bearer <token>

Authentication is required for all endpoints except registration and login.

### Auth Protection

Authentication endpoints are protected by two layers:

1. Per-IP throttling on auth routes.
2. Per-email login lockout in the auth service.

Current defaults (configurable via backend environment settings):

- `POST /auth/register`: `3/minute` per IP
- `POST /auth/login`: `5/minute` per IP
- Login lockout: `5` failed attempts within `15` minutes per email

When a throttle is exceeded, the API returns HTTP `429`.

---

## Rate Limiting

The API applies a global default limit and endpoint-specific overrides.

Default limit:

- All routes without a dedicated override: `60/minute` per IP

Endpoint-specific limits:

- `POST /auth/register`: `3/minute` per IP
- `POST /auth/login`: `5/minute` per IP
- `GET /reports/summary`: `10/minute` per IP

Notes:

- Limits are enforced by request source IP.
- Auth login additionally uses per-email lockout to reduce brute-force risk.

---

## Endpoints

### POST /auth/register

Creates a new user.

Request:

```json
{
	"email": "user@example.com",
	"password": "securepassword123",
	"full_name": "Jane Doe"
}
```

Response:

```json
{
	"id": "550e8400-e29b-41d4-a716-446655440000",
	"email": "user@example.com",
	"full_name": "Jane Doe"
}
```

---

### POST /auth/login

Returns JWT token.

Request:

```json
{
	"email": "user@example.com",
	"password": "securepassword123"
}
```

Response:

```json
{
	"access_token": "<jwt-token>",
	"token_type": "bearer"
}
```

---

### POST /budgets

Creates a budget.

Requires authentication.

Request:

```json
{
	"month": "2024-03",
	"amount": 2000
}
```

Response:

```json
{
	"budgetId": "550e8400-e29b-41d4-a716-446655440000",
	"userId": "660e8400-e29b-41d4-a716-446655440000",
	"month": "2024-03",
	"totalAmount": 2000,
	"createdAt": "2024-03-01T00:00:00Z",
	"updatedAt": "2024-03-01T00:00:00Z"
}
```

---

### GET /budgets/current-month

Returns the authenticated user's current month budget.

Requires authentication.

---

### POST /expenses

Adds an expense.

Requires authentication.

Request:

```json
{
	"amount": 100,
	"category": "Food",
	"date": "2024-03-10",
	"note": "Groceries"
}
```

---

### POST /incomes

Adds an income record.

Requires authentication.

Request:

```json
{
	"amount": 3000,
	"source": "Salary",
	"date": "2024-03-01"
}
```

Response:

```json
{
	"incomeId": "550e8400-e29b-41d4-a716-446655440000",
	"userId": "660e8400-e29b-41d4-a716-446655440000",
	"amount": 3000,
	"source": "Salary",
	"date": "2024-03-01",
	"createdAt": "2024-03-01T12:00:00Z"
}
```

---

### GET /expenses/current-month

Returns the authenticated user's expenses for the current month.

Requires authentication.

---

### GET /reports/summary?month=YYYY-MM

Returns financial summary.

Requires authentication.

Response:

```json
{
	"month": "2024-03",
	"totalIncome": 3000,
	"totalExpenses": 800,
	"net": 2200,
	"byCategory": {
		"Food": 300,
		"Transport": 500
	},
	"generatedAt": "2026-02-16T02:38:52Z"
}
```

---

## Error Codes

Error responses include both:

- HTTP status code (for transport-level semantics)
- Domain `errorCode` field in the JSON envelope (for application-level handling)

Typical error envelope:

```json
{
	"timestamp": "2026-03-21T12:00:00Z",
	"status": 401,
	"error": "Unauthorized",
	"errorCode": "AUTH-001",
	"message": "Missing or invalid token",
	"path": "/api/v1/expenses/current-month"
}
```

Validation error example (`400`):

```json
{
	"timestamp": "2026-03-28T10:20:30Z",
	"status": 400,
	"error": "Bad Request",
	"errorCode": "VAL-001",
	"message": "Invalid input data",
	"path": "/api/v1/reports/summary",
	"details": [
		{
			"field": "month",
			"issue": "String should match pattern"
		}
	]
}
```

Auth failure example (`401`):

```json
{
	"timestamp": "2026-03-28T10:21:00Z",
	"status": 401,
	"error": "Unauthorized",
	"errorCode": "AUTH-004",
	"message": "Invalid email or password",
	"path": "/api/v1/auth/login"
}
```

Rate-limit example (`429`):

```json
{
	"timestamp": "2026-03-28T10:21:15Z",
	"status": 429,
	"error": "Too Many Requests",
	"errorCode": "SYS-003",
	"message": "5 per 1 minute",
	"path": "/api/v1/auth/login"
}
```

| Code | Meaning               |
| ---- | --------------------- |
| 400  | Invalid request       |
| 401  | Unauthorized          |
| 403  | Forbidden             |
| 404  | Not found             |
| 409  | Conflict              |
| 429  | Too many requests     |
| 500  | Internal server error |

Common `errorCode` values:

- `AUTH-001`: Missing or invalid token
- `AUTH-004`: Invalid email or password
- `VAL-001`: Invalid input data
- `SYS-003`: Rate limit exceeded
