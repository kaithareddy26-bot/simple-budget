# simple-budget
Cross-Platform Budgeting Application

A REST API for personal budgeting and financial tracking.

Built with FastAPI and PostgreSQL, this backend provides secure authentication, budget management, income and expense tracking, and monthly financial reporting. It is designed to support a future web-based frontend GUI (not yet implemented).

Live API Documentation

Interactive API documentation is available at:

https://jl7283.github.io/simple-budget/api/

This documentation is automatically generated from the OpenAPI specification via GitHub Actions.

Features

Secure user registration and JWT authentication

Monthly budget creation and updates

Income tracking

Expense tracking with category grouping

Monthly financial summaries

Standardized error envelope

Versioned database migration strategy

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

Contract-driven API design

Centralized error handling

Deterministic unit testing

Technology Stack

Python 3.12

FastAPI

SQLAlchemy

PostgreSQL

Pydantic v2

JWT Authentication

Pytest

Flyway (database migrations)

GitHub Actions (CI + documentation publishing)

Setup Instructions
1. Clone the Repository
git clone https://github.com/jl7283/simple-budget.git
cd simple-budget/backend

2. Create a Virtual Environment

PowerShell:

python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt


Mac/Linux:

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

Environment Configuration

Create a .env file inside the backend directory:

DATABASE_URL=postgresql://budget_user:budget_pass@localhost:5432/budget_db
SECRET_KEY=your-secret-key
RUN_DB_INIT=false
ACCESS_TOKEN_EXPIRE_MINUTES=30


Notes:

RUN_DB_INIT=false is recommended when using Flyway migrations.

Set RUN_DB_INIT=true only for local rapid development without migrations.

Database Setup

Ensure PostgreSQL is running locally.

Create the database:

createdb budget_db

Using Flyway (Recommended)

Run migrations:

flyway migrate

Development Mode (Optional)

If not using Flyway:

RUN_DB_INIT=true


The application will auto-create tables using SQLAlchemy.

Running the Application Locally

From the backend directory:

uvicorn app.main:app --reload


The API will be available at:

http://127.0.0.1:8000


Swagger UI:

http://127.0.0.1:8000/docs


OpenAPI JSON:

http://127.0.0.1:8000/openapi.json

Running Tests

From the backend directory:

pytest -q


The test suite includes:

AuthService validation and credential checks

BudgetService business rule enforcement

Income and Expense validation

ReportService month boundary validation

Error contract verification

All tests should pass before committing changes.

Example API Response

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

CI/CD

GitHub Actions provides:

Automated test execution on push and pull request

Automatic OpenAPI generation

Automatic publishing of Swagger UI documentation to GitHub Pages

API documentation is published at:

https://jl7283.github.io/simple-budget/api/

Deployment Considerations

Environment-driven configuration

Migration-first startup pattern

Strict error contract for frontend compatibility

JWT-based authentication

Designed for containerization

Project Structure
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

Status

Backend API complete and production-structured.
Frontend GUI pending implementation.


