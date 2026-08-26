# Mastercard AI Defense Lab — Fixed Full Stack

This build has one consistent API contract between React and Flask.

## What is connected

- Create Account -> POST /auth/register
- Sign In -> POST /auth/login
- Current user -> GET /auth/me
- Blue Team model -> POST /predict
- Red Team generator + model -> POST /run-red-team
- Metrics -> GET /metrics

Prediction, Red Team and metrics require a signed Bearer token.

## Required model files

Already included in this project under `models/`:

- behavioral_fraud_model_v4.json
- behavioral_model_columns_v4.pkl

The application uses those V4 files.

## Run backend

Open terminal 1 in the project root:

```bat
py -3.12 -m pip install -r requirements.txt
py -3.12 app.py
```

Verify:

http://127.0.0.1:5000/health

Expected:

```json
{
  "authentication": "enabled",
  "model_loaded": true,
  "status": "ok"
}
```

## Run frontend

Open terminal 2:

```bat
cd frontend
npm install
npm run dev
```

Open:

http://localhost:5173

## Important after replacing your old project

Your old browser may contain an old token.

Open DevTools -> Application -> Local Storage and delete:
- mastercard_token
- mastercard_user

Or simply click Logout and sign in again.

## Security note

The local build uses an HMAC-signed JWT and SQLite users for a simple working prototype.
Before public production deployment, set a strong `JWT_SECRET_KEY`, use HTTPS, and move authentication to secure httpOnly cookies / a production identity service.
