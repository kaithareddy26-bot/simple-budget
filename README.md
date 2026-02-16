# simple-budget
Cross-Platform Budgeting Application

A REST API for personal budgeting and financial tracking.

Built with FastAPI, PostgreSQL, and a clean layered architecture, this backend is designed to support a future web-based frontend GUI (not yet implemented).

Overview

Simple Budget enables users to:

Register and authenticate securely

Define monthly budgets

Track income and expenses

Generate monthly financial summaries

Analyze spending by category

The system is designed with strong architectural discipline and deployment readiness in mind.

Architecture

The application follows a layered architecture:

API Layer (FastAPI Controllers)
Service Layer (Business Logic)
Repository Layer (Data Access)
Database (PostgreSQL via SQLAlchemy)

Design principles:

Separation of concerns

Dependency injection

Repository pattern

Standardized error envelope

Contract-driven API design

Versioned schema migrations

Deterministic service-layer unit tests

Technology Stack

Python 3.12

FastAPI

SQLAlchemy

PostgreSQL

JWT authentication

Pydantic v2

Pytest

Flyway (database migrations)

Planned Frontend

This backend is intended to power a web-based GUI (planned future implementation).

The frontend will:

Consume the REST API

Provide dashboards and charts

Visualize monthly summaries

Display category breakdowns

Support responsive UX

The backend API contract is stable and ready for frontend integration.

Core Features
Authentication

Secure user registration

JWT-based login

Protected endpoints via Bearer tokens

Budget Management

Create monthly budgets

Update budget amounts

Retrieve budgets by ID

Income and Expense Tracking

Add income entries

Add expense entries

Category-based grouping

Monthly Reporting

Example response:

{
  "month": "2024-03",
  "totalIncome": "3000.00",
  "totalExpenses": "200.00",
  "net": "2800.00",
  "byCategory": {
    "Groceries": "200.00"
  },
  "generatedAt": "2026-02-16T02:38:52Z"
}

API Conventions

Base path:

/api/v1

Standard Error Envelope

All errors follow a consistent structure:

{
  "timestamp": "2026-02-16T02:28:46Z",
  "status": 401,
  "error": "Unauthorized",
  "errorCode": "AUTH-001",
  "message": "Missing or invalid token",
  "path": "/api/v1/budgets"
}


Validation errors include a "details" array.

Database Migration Strategy

Schema changes are managed via Flyway versioned migrations.

Production flow:

Apply migrations

Start API server

flyway migrate
uvicorn app.main:app


Development mode only:

RUN_DB_INIT=true


Default committed configuration:

RUN_DB_INIT=false


This prevents unintended schema drift in production.

Getting Started
1. Clone the repository
git clone <repo-url>
cd simple-budget/backend

2. Create a virtual environment

PowerShell:

python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt

3. Configure environment

Create a .env file (not committed):

DATABASE_URL=postgresql://budget_user:budget_pass@localhost:5432/budget_db
SECRET_KEY=your-secret-key
RUN_DB_INIT=false

4. Run migrations
flyway migrate

5. Start the server
uvicorn app.main:app --reload


Visit:

http://127.0.0.1:8000/docs

Testing

Run all tests:

pytest -q


The test suite includes:

AuthService credential validation

Budget business rule enforcement

Income and expense validation

Strict month-boundary validation for reporting

Error contract consistency

Deterministic mocking for security functions

All tests pass.

Security Considerations

Passwords are hashed before storage

JWT tokens use configurable secret and expiration

Unauthorized access returns standardized error responses

Business rule validation enforced in service layer

Deployment Considerations

Designed for containerization

Migration-first startup pattern

Environment-driven configuration

Strict error contract for frontend stability

Clear separation between development convenience and production behavior

Project Structure
app/
  controllers/
  services/
  repositories/
  models/
  schemas/
  utils/
  config.py
  main.py

tests/

Status

Backend API complete and production-structured.
Frontend GUI pending implementation.