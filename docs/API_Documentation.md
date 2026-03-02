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

---

## Endpoints

### POST /auth/register

Creates a new user.

Request:

{
"email": "user@example.com",
"password": "securepassword123",
"full_name": "Jane Doe"
}

Response:

{
"id": "550e8400-e29b-41d4-a716-446655440000",
"email": "user@example.com",
"full_name": "Jane Doe"
}

---

### POST /auth/login

Returns JWT token.

Request:

{
"email": "user@example.com",
"password": "securepassword123"
}

Response:

{
"access_token": "<jwt-token>",
"token_type": "bearer"
}

---

### POST /budgets

Creates a budget.

Requires authentication.

Request:

{
"month": "2024-03",
"amount": 2000
}

Response:

{
"budgetId": "550e8400-e29b-41d4-a716-446655440000",
"userId": "660e8400-e29b-41d4-a716-446655440000",
"month": "2024-03",
"totalAmount": 2000,
"createdAt": "2024-03-01T00:00:00Z",
"updatedAt": "2024-03-01T00:00:00Z"
}

---

### GET /budgets/current-month

Returns the authenticated user's current month budget.

Requires authentication.

---

### POST /expenses

Adds an expense.

Requires authentication.

Request:

{
"amount": 100,
"category": "Food",
"date": "2024-03-10",
"note": "Groceries"
}

---

### POST /incomes

Adds an income record.

Requires authentication.

Request:

{
"amount": 3000,
"source": "Salary",
"date": "2024-03-01"
}

Response:

{
"incomeId": "550e8400-e29b-41d4-a716-446655440000",
"userId": "660e8400-e29b-41d4-a716-446655440000",
"amount": 3000,
"source": "Salary",
"date": "2024-03-01",
"createdAt": "2024-03-01T12:00:00Z"
}

---

### GET /expenses/current-month

Returns the authenticated user's expenses for the current month.

Requires authentication.

---

### GET /reports/summary?month=YYYY-MM

Returns financial summary.

Requires authentication.

Response:

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

---

## Error Codes

| Code | Meaning               |
| ---- | --------------------- |
| 400  | Invalid request       |
| 401  | Unauthorized          |
| 403  | Forbidden             |
| 404  | Not found             |
| 409  | Conflict              |
| 500  | Internal server error |
