# Developer Guide

Simple Budget – Technical Documentation

## 1. System Overview

Simple Budget is built using:

Frontend:

- React
- Axios (API communication)

Backend:

- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT Authentication

Hosting:

- Frontend: Vercel
- Backend: Render

---

## 2. Architecture Overview

Client (React)
↓ REST API
FastAPI Backend
↓
PostgreSQL Database

Design Principles:

- RESTful API design
- Separation of concerns
- Stateless authentication (JWT)
- Modular backend structure

---

## 3. Project Structure

simple-budget/
├── backend/
│ ├── app/
│ │ ├── controllers/
│ │ ├── services/
│ │ ├── repositories/
│ │ ├── models/
│ │ ├── schemas/
│ │ ├── utils/
│ │ └── main.py
│ ├── config.py
│ ├── requirements.txt
│ ├── scripts/
│ │ └── export_openapi.py
│ └── tests/
│ └── (test files)
├── .env.example
│── docs
├── README.md
├── requirements.txt (could also be in backend)
└── (possibly other config files)

---

## 4. Local Development Setup

### Backend Setup

Requirements:

- Python 3.10+
- pip

Steps:

1. Navigate to backend directory
2. Create virtual environment
3. Install dependencies:

pip install -r requirements.txt

4. Run server:

uvicorn main:app --reload

Backend runs at:
http://localhost:8000

---

### Frontend Setup

Requirements:

- Node.js 18+

Steps:
npm install
npm start

Frontend runs at:
http://localhost:3000

---

## 5. Running Tests

Backend:
pytest --cov

Frontend:

npm test -- --coverage

---

## 6. Coding Standards

Backend:

- Follow PEP8
- Use type hints
- Keep functions small and single-responsibility

Frontend:

- Follow ESLint rules
- Functional components preferred
- Use React hooks properly

---

## 7. Contribution Guidelines

- Create feature branch
- Write tests for new features
- Ensure no lint errors
- Submit pull request with description
