# CampusBite

CampusBite is a full-stack restaurant ordering and delivery application for campus communities. Customers can browse restaurants and place orders; restaurant owners can manage menus and order progress; delivery partners can manage assigned deliveries.

## Technology

- Frontend: React, Vite, React Router, Axios
- Backend: FastAPI, Pydantic, SQLAlchemy, JWT
- Database: PostgreSQL with Docker Compose; SQLite can be used for local backend development
- AI: OpenAI API for customer order insights

## Features

- Customer, restaurant-owner, and delivery-partner roles
- Registration, login, password hashing, JWT authentication, and role-protected APIs
- Restaurant and menu listing, menu management, and order placement
- Order lifecycle, delivery assignment, dummy payment ledger, refunds, and reviews
- Owner statistics and stale-order reminders
- Customer order-history insights using the OpenAI API

## Configuration and secrets

Copy `.env.example` to `.env` and set values for your environment. Keep `.env` private; it is excluded by `.gitignore`.

Required variables:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Database connection URL. Docker Compose configures the backend to use its PostgreSQL service. |
| `POSTGRES_USER` | PostgreSQL user |
| `POSTGRES_PASSWORD` | PostgreSQL password; replace the development placeholder with a strong value |
| `POSTGRES_DB` | PostgreSQL database name |
| `JWT_SECRET_KEY` | Secret used to sign access tokens; set a strong random value |
| `JWT_ALGORITHM` | JWT signing algorithm (the project defaults to `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime |
| `OPENAI_API_KEY` | Optional server-side key for the AI insights endpoint |

Never commit API keys, real passwords, or other credentials.

## Run the backend with Docker Compose

From the repository root:

```powershell
Copy-Item .env.example .env
```

Edit `.env` with secure values, then start the services:

```powershell
docker compose up --build
```

The API is available at `http://localhost:8000`. Interactive API documentation is at `http://localhost:8000/docs`. Docker Compose creates the database tables when the backend starts.

## Run the frontend locally

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal (normally `http://localhost:5173`). The frontend connects to `http://localhost:8000` by default. To use a different API URL, set `VITE_API_URL` before starting Vite.

Build the frontend for production with:

```powershell
npm run build
```

## Backend development without Docker

Install the backend dependencies and run Uvicorn from the `backend` directory:

```powershell
pip install -r requirements.txt
$env:DATABASE_URL = "sqlite:///./campusbite.db"
$env:JWT_SECRET_KEY = "replace-with-a-strong-local-secret"
uvicorn app.main:app --reload
```

Set `OPENAI_API_KEY` in the backend environment to enable AI insights. Do not put that key in frontend code.
