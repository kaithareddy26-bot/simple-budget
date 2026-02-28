# API Documentation

Simple Budget REST API

## Base URL

Production:
https://<your-backend-url>.onrender.com

Local:
http://localhost:8000

---

## Authentication

JWT-based authentication.

Header format:

Authorization: Bearer <token>

---

## Endpoints

### POST /register

Creates a new user.

Request:

{
"email": "user@example.com",
"password": "password123"
}

Response:

{
"message": "User created successfully"
}

---

### POST /login

Returns JWT token.

Response:

{
"access_token": "<jwt-token>",
"token_type": "bearer"
}

---

### POST /budget

Creates a budget.

Requires authentication.

Request:

{
"monthly_budget": 2000
}

---

### POST /expense

Adds an expense.

Request:

{
"amount": 100,
"category": "Food",
"description": "Groceries"
}

---

### GET /summary

Returns financial summary.

Response:

{
"monthly_budget": 2000,
"total_spent": 800,
"remaining_balance": 1200
}

---

## Error Codes

| Code | Meaning               |
| ---- | --------------------- |
| 400  | Invalid request       |
| 401  | Unauthorized          |
| 404  | Not found             |
| 500  | Internal server error |
