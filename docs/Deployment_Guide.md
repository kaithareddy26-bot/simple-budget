# Deployment Guide

Simple Budget

## Backend Deployment (Render)

1. Push code to GitHub.
2. Log into Render.
3. Create new Web Service.
4. Connect repository.
5. Set build command:

pip install -r requirements.txt

6. Set start command:

uvicorn main:app --host 0.0.0.0 --port 10000

7. Add environment variables:
   - DATABASE_URL
   - SECRET_KEY
   - JWT_SECRET

8. Deploy.

---

## Frontend Deployment (Vercel)

1. Connect GitHub repository.
2. Set build command:

npm run build

3. Set environment variable:
   REACT_APP_API_URL

4. Deploy.

---

## Environment Variables

Backend:

- DATABASE_URL
- SECRET_KEY
- JWT_SECRET
- ACCESS_TOKEN_EXPIRE_MINUTES

Frontend:

- REACT_APP_API_URL

---

## Post-Deployment Testing

After deployment:

- Register user
- Log in
- Create budget
- Add expense
- Verify summary updates
