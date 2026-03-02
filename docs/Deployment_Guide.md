# Deployment Guide

Cross-Platform Budgeting Application

## Prerequisites and Dependencies

- GitHub repository with deployable source code
- Backend hosting account (Render or equivalent)
- Frontend hosting account (Vercel or equivalent)
- Managed PostgreSQL database
- Environment secrets prepared for production
- Runtime dependencies installed from:
   - `backend/requirements.txt`
   - `mobile/package.json`

## Backend Deployment (Render)

1. Push code to GitHub.
2. Log into Render.
3. Create new Web Service.
4. Connect repository.
5. Set build command:

pip install -r requirements.txt

6. Set start command:

uvicorn app.main:app --host 0.0.0.0 --port 10000

7. Add environment variables:
   - DATABASE_URL
   - SECRET_KEY
   - JWT_SECRET

8. Deploy.

---

## Frontend Deployment (Vercel)

1. Connect GitHub repository.
2. Set project root to `mobile/`.
3. Set build command:

npx expo export --platform web

4. Set output directory:

dist

5. Deploy.

Note:

- Current frontend components use hardcoded backend URLs (`http://localhost:8000/api/v1/...`).
- Update frontend API base URL handling before production release if backend is hosted remotely.

---

## Environment Variables

Backend:

- DATABASE_URL
- SECRET_KEY
- JWT_SECRET
- ACCESS_TOKEN_EXPIRE_MINUTES

Frontend:

- (No frontend runtime API env var is currently wired in code)

---

## Post-Deployment Testing

After deployment:

- Register user
- Log in
- Create budget
- Add expense
- Verify summary updates
