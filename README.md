# CollegeFindr

CollegeFindr is an AI-powered college search assistant. This monorepo contains the Flask backend API and the static frontend.

## Project Structure

```text
backend/    Flask + SQLAlchemy API, OpenRouter chat integration, guardrails, tests
frontend/   Static HTML/CSS/JavaScript app and image assets
render.yaml Render blueprint for both services
```

## Run Backend Locally

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

The backend starts on `http://localhost:5000`.

## Run Frontend Locally

```bash
cd frontend
python -m http.server 5500
```

Open `http://localhost:5500`. In local development, the frontend defaults API calls to `http://127.0.0.1:5000`.

## Tests

```bash
cd backend
python tests/test_collegefindr.py
python tests/test_qa_runner.py
```

## Deploy

`render.yaml` defines both Render services:

- `collegefindr-backend`: Python web service from `backend/`
- `collegefindr-frontend`: static site from `frontend/`

Point Render at this repository and apply the blueprint. Keep backend secrets such as `OPENROUTER_API_KEY`, `JWT_SECRET_KEY`, and database settings configured in Render.
