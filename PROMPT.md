# KPI-One API — Project Regeneration Prompt

You are generating a Python FastAPI backend project named **kpi-one**.

Goal: recreate an API service with the same capabilities and structure as the existing kpi-one repo: FastAPI + SQLModel/Postgres + Alembic migrations + PASETO auth + environment-based config that can be overridden by AWS Secrets Manager.

## Tech Stack

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic v2 + pydantic-settings
- SQLModel + SQLAlchemy
- Postgres via psycopg3 (`psycopg[binary]`)
- Alembic
- Password hashing via Argon2 (`argon2-cffi`)
- PASETO tokens (`paseto`)
- Optional AWS Secrets Manager integration (`boto3`)

## Repository Layout (required)

Create the following files and directories:

- `run.py` (custom CLI wrapper around uvicorn)
- `requirements.txt`
- `alembic.ini`
- `alembic/` (standard Alembic env + versions)
- `app/`
  - `__init__.py`
  - `main.py` (FastAPI app instance)
  - `config.py` (settings loader)
  - `models/`
    - `__init__.py`
    - `db_orm.py` (SQLModel engine + session dependency)
    - `users.py` (User table + CRUD helpers)
    - `posts.py` (Posts table + CRUD helpers)
    - `votes.py` (Votes table + CRUD helpers)
  - `routers/`
    - `__init__.py`
    - `auth.py` (login endpoint)
    - `users.py` (user endpoints)
    - `posts.py` (post endpoints)
    - `votes.py` (vote endpoints)
  - `schemas/`
    - `__init__.py`
    - `users.py` (pydantic request/response models)
    - `posts.py`
    - `votes.py`
  - `utils/`
    - `__init__.py`
    - `helpers.py` (AppException + JSONResponse handler; json helpers)
    - `auth.py` (PASETO token creation/verification + current-user dependency)
    - `db_sql.py` (optional direct psycopg3 connection helper)
- `config/`
  - `.env.example`
  - `.env.development` (local-only; should be gitignored)
  - `README.md`
- `data/`
  - `data.json` (optional sample data)
  - `db_config.json` (optional multi-env db settings; avoid plaintext secrets)
- `scripts/`
  - `setup_aws_secrets.py` (helper for creating/updating AWS secret template)

## Runtime Behavior

### App startup

- FastAPI app lives in `app/main.py` as `app`.
- Use lifespan startup to call `create_db_and_tables()` to ensure tables exist.
- Register a custom exception handler for `AppException` returning JSON `{"detail": "..."}`.

### CORS / middleware

- Add `CORSMiddleware`.
- CORS origins come from settings variable `CORS_ORIGINS` (comma-separated), parsed into a list.
- Typical config:
  - allow credentials
  - allow all methods/headers
  - expose `Content-Type` and `Authorization`

### Configuration model

Implement `app/config.py` using `pydantic-settings.BaseSettings`.

Required settings:
- `DATABASE_URL` (no hardcoded defaults)
- `PASETO_SECRET_KEY` (hex string)

Other settings:
- `DATABASE_ECHO` (bool)
- `ACCESS_TOKEN_EXPIRE_MINUTES` (int)
- `APP_ENV` (development/staging/production)
- `DEBUG` (bool)
- `CORS_ORIGINS` (string list)
- AWS Secrets Manager optional:
  - `AWS_SECRETS_ENABLED` (bool)
  - `AWS_SECRET_NAME` (str)
  - `AWS_REGION` (str)

Env loading behavior:
- Load from `config/.env.<APP_ENV>` if it exists, else `config/.env`.
- If `AWS_SECRETS_ENABLED=True`, fetch SecretString JSON from Secrets Manager and override keys:
  - `DATABASE_URL`
  - `PASETO_SECRET_KEY`
  - `ACCESS_TOKEN_EXPIRE_MINUTES`
  - `CORS_ORIGINS`

### Database

- Use SQLModel models.
- Create engine in `app/models/db_orm.py` from `settings.database_url`.
- Provide `get_session()` dependency yielding a SQLModel `Session`.

Tables:
- `user`:
  - id (int pk)
  - username (unique)
  - email (unique)
  - password_hash
  - created_at (server default NOW)
- `posts`:
  - id (int pk)
  - owner_id (fk user.id)
  - title, content
  - published (default true)
  - date (server default NOW)
- `votes`:
  - post_id (fk posts.id) + user_id (fk user.id) composite pk
  - date (server default NOW)

### Authentication

- Use OAuth2 password flow with `OAuth2PasswordBearer(tokenUrl="/auth/login")`.
- Login endpoint: `POST /auth/login` using `OAuth2PasswordRequestForm`.
- Verify password using Argon2.
- Issue PASETO v4 local token with expiration.
- Protected endpoints must depend on `get_current_user()` which:
  - parses the PASETO token
  - extracts username
  - fetches user from DB

### API Endpoints (minimum)

- `GET /` health/welcome
- `POST /auth/login` -> returns `{access_token, token_type, username}`
- Posts:
  - `GET /posts` list with optional `limit`, `skip`, `search`, and include vote counts
  - `GET /posts/{post_id}`
  - `POST /posts` (auth required)
  - `PUT /posts/{post_id}` (auth required; owner only)
  - `DELETE /posts/{post_id}` (auth required; owner only)
- Users:
  - `POST /users` create user
  - `GET /users/{id}` fetch user (auth required)
- Votes:
  - `POST /votes` create or remove vote based on `direction` (0/1) (auth required)

## CLI Runner

`run.py` must:
- parse args: `--env/--environment`, `--host`, `--port`, `--reload`, `--workers`, `--log-level`
- set `APP_ENV` env var before importing uvicorn/app
- run uvicorn on `app.main:app`

## Dependency File

`requirements.txt` must include at least:
- fastapi
- uvicorn[standard]
- pydantic
- pydantic-settings
- python-multipart
- sqlmodel
- psycopg[binary]
- alembic
- paseto
- argon2-cffi
- boto3 (optional/commented or optional dependency)

## Git Hygiene

- Include `.gitignore` ignoring `__pycache__/`, `venv/`, and any real env files (like `config/.env`, `config/.env.development`).
- Do not commit real secrets.

## Deliverable

Generate the full project with the structure above and runnable code that starts successfully when environment variables are provided.

Assume Postgres is available and migrations can be run via `alembic upgrade head`.
