# simple-budget

Cross-Platform Budgeting Application

A cross-platform budgeting application with a FastAPI backend and an implemented Expo frontend.

Built with FastAPI and PostgreSQL, this backend provides secure authentication, budget management, income and expense tracking, and monthly financial reporting. Frontend GUI is implemented for cross-platform usage.

## Live API Documentation

Interactive API documentation is available at:

https://jl7283.github.io/simple-budget/api/

This documentation is automatically generated from the OpenAPI specification via GitHub Actions.

## Key Features

Secure user registration and JWT authentication

Monthly budget creation and updates

Income tracking

Expense tracking with category grouping

Monthly financial summaries

Standardized error envelope

Versioned database migration strategy

## Architecture

The application follows a layered architecture:

API Layer (FastAPI Controllers)
Service Layer (Business Logic)
Repository Layer (Data Access)
Database (PostgreSQL via SQLAlchemy)

Design principles:

Separation of concerns

Dependency injection

Repository pattern

Contract-driven API design

Centralized error handling

Deterministic unit testing

## Technology Stack

Python 3.12

FastAPI

SQLAlchemy

PostgreSQL

Pydantic v2

JWT Authentication

Pytest

Flyway (database migrations)

GitHub Actions (CI + documentation publishing)

## Quick Start

1. Clone the Repository
   git clone https://github.com/jl7283/simple-budget.git
   cd simple-budget/backend

2. Create a Virtual Environment

PowerShell:

python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements-dev.txt

Mac/Linux:

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

For runtime-only installs (for example, production containers), use:

pip install -r requirements.txt

### Environment Configuration

Create a .env file inside the backend directory:

DATABASE_URL=postgresql://budget_user:budget_pass@localhost:5432/budget_db
SECRET_KEY=your-secret-key
RUN_DB_INIT=false
ACCESS_TOKEN_EXPIRE_MINUTES=30

Notes:

RUN_DB_INIT=false is recommended when using Flyway migrations.

Set RUN_DB_INIT=true only for local rapid development without migrations.

### Database Setup

Ensure PostgreSQL is running locally.

Create the database:

createdb budget_db

#### Using Flyway (Recommended)

Run migrations:

flyway migrate

### Development Mode (Optional)

If not using Flyway:

RUN_DB_INIT=true

The application will auto-create tables using SQLAlchemy.

## Run Locally

From the backend directory:

uvicorn app.main:app --reload

The API will be available at:

http://127.0.0.1:8000

Swagger UI:

http://127.0.0.1:8000/docs

OpenAPI JSON:

http://127.0.0.1:8000/openapi.json

## Running Tests

Backend tests (from the backend directory):

pytest -q

Backend test suite includes:

- [AuthService tests](backend/tests/test_auth_service.py): validates authentication flows and credential handling.
- [BudgetService tests](backend/tests/test_budget_service.py): verifies budget business rule enforcement.
- [ExpenseService tests](backend/tests/test_expense_service.py): validates expense input and service behavior.
- [IncomeService tests](backend/tests/test_income_service.py): validates income input and service behavior.
- [ReportService tests](backend/tests/test_report_service.py): verifies month boundary rules and reporting contract behavior.

Frontend tests (from the mobile directory):

Prerequisite (run once or after dependency changes):

npm install

npm test

Frontend coverage report (from the mobile directory):

npm test -- --coverage

Frontend test suite includes:

- [AddExpenseForm tests](mobile/__tests__/AddExpenseForm.test.tsx): redirects when unauthenticated, validates budget prerequisites, and verifies successful expense submission flow.
- [ExpenseCard tests](mobile/__tests__/ExpenseCard.test.tsx): renders category, amount, and note values correctly.
- [LoginPage tests](mobile/__tests__/LoginPage.test.tsx): verifies successful login behavior (JWT + navigation) and failed login error handling.
- [RegistrationPage tests](mobile/__tests__/RegistrationPage.test.tsx): verifies successful registration navigation and failed registration messaging.
- [WelcomePage tests](mobile/__tests__/WelcomePage.test.tsx): covers unauthenticated redirect, budget setup validation, budget creation, and current-month summary rendering.

All tests should pass before committing changes.

## Example API Response

Monthly summary response:

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

## CI/CD

GitHub Actions provides:

Automated test execution on push and pull request

Automatic OpenAPI generation

Automatic publishing of Swagger UI documentation to GitHub Pages

API documentation is published at:

https://jl7283.github.io/simple-budget/api/

## Deployment Considerations

Environment-driven configuration

Migration-first startup pattern

Strict error contract for frontend compatibility

JWT-based authentication

Designed for containerization

## Project Structure
backend/
app/
controllers/
services/
repositories/
models/
schemas/
utils/
main.py
config.py
scripts/
export_openapi.py
tests/

## Status

Backend API complete and production-structured.
Frontend MVP implementation completed.
