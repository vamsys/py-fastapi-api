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

## Exact APIs By File (names + signatures)

Generate modules with these exact *public* symbols (match names, basic signatures, and intent). Keep behavior aligned with the descriptions below.

### run.py

- `main() -> None`:
  - Uses `argparse` with flags: `--environment/--env`, `--host`, `--port`, `--reload`, `--workers`, `--log-level`.
  - Sets `os.environ['APP_ENV']` before importing `uvicorn`.
  - Calls `uvicorn.run(app='app.main:app', host=..., port=..., log_level=..., reload=..., workers=...)`.

### app/main.py

- `lifespan(app: FastAPI)` (async context manager via `@asynccontextmanager`): calls `create_db_and_tables()` on startup.
- `app = FastAPI(lifespan=lifespan)`
- CORS:
  - `cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]`
  - `app.add_middleware(CORSMiddleware, allow_origins=cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"], expose_headers=["Content-Type", "Authorization"])`
- Error handling: `app.add_exception_handler(AppException, app_exception_handler)`
- Routers are included in this order:
  - `auth_router`, `posts_router`, `users_router`, `votes_router`
- Root endpoint:
  - `@app.get("/")`
  - `async def read_root() -> dict: return {"Hello": "Welcome to KPI One"}`

### app/config.py

- `class Settings(BaseSettings)` with fields:
  - `database_url: str`
  - `database_echo: bool = True`
  - `paseto_secret_key: str`
  - `access_token_expire_minutes: int = 30`
  - `app_env: str = "development"`
  - `debug: bool = True`
  - `cors_origins: str = "http://localhost:3000,http://localhost:8080"`
  - `api_v1_prefix: str = "/api/v1"`
  - `aws_secrets_enabled: bool = False`
  - `aws_secret_name: Optional[str] = None`
  - `aws_region: str = "us-east-1"`
- `load_secrets_from_aws(settings_obj: Settings) -> Settings`:
  - If disabled / missing secret name: return input settings.
  - If enabled: fetch Secrets Manager SecretString JSON and override mapping keys:
    - `DATABASE_URL`, `PASETO_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `CORS_ORIGINS`.
- `get_settings() -> Settings`:
  - choose env file `config/.env.<APP_ENV>` if exists else `config/.env`.
  - instantiate `Settings(_env_file=env_file)`.
  - if `aws_secrets_enabled`: call `load_secrets_from_aws`.
- `settings = get_settings()` (global singleton)

### app/models/db_orm.py

- `engine = create_engine(settings.database_url, echo=settings.database_echo, pool_pre_ping=True)`
- `create_db_and_tables() -> None`: `SQLModel.metadata.create_all(engine)`
- `get_session()` generator yielding `Session(engine, autocommit=False, autoflush=True, expire_on_commit=False)`
- `SessionDep = Annotated[Session, Depends(get_session)]`
- `class BaseModel(SQLModel)`: sets `__table_args__ = {"extend_existing": True}`

### app/models/users.py

- `ph = PasswordHasher()`
- `class BaseModel(SQLModel)` with `__table_args__ = {"extend_existing": True}`
- `class User(BaseModel, table=True)` with `__tablename__ = "user"` and fields:
  - `id: int` primary key
  - `username: str` unique
  - `email: EmailStr` unique
  - `password_hash: str`
  - `created_at: datetime` default now, server_default NOW
- Functions:
  - `hash_password(password: str) -> str`
  - `verify_password(hashed_password: str, plain_password: str) -> bool`
  - `get_user_by_id(user_id: int, session: SessionDep) -> Optional[User]`
  - `get_user_by_username_db(username: str, session: SessionDep) -> Optional[User]`
  - `get_user_by_email_db(email: str, session: SessionDep) -> Optional[User]`
  - `create_new_user_db(user: dict, session: SessionDep) -> Optional[User]` (hash `user["password"]` into `password_hash`)

### app/models/posts.py

- `class Posts(BaseModel, table=True)` with `__tablename__ = "posts"` and fields:
  - `id: int` primary key
  - `owner_id: int` foreign key `user.id`
  - `title: str`
  - `content: str`
  - `published: bool` default true
  - `date: datetime` default now, server_default NOW
  - `owner: Optional["User"] = Relationship()`
- Functions:
  - `get_posts_from_db_by_model(session: SessionDep) -> list[Posts]`
  - `get_posts_response(session: SessionDep) -> list[schemas.posts.Post]`
  - `get_post_from_db_by_model_by_id(post_id: int, session: SessionDep) -> Optional[Posts]`
  - `create_post_in_db_by_model(post: dict, session: SessionDep) -> Optional[Posts]`
  - `delete_post_from_db_by_model(post_id: int, session: SessionDep) -> Optional[Posts]`
  - `update_post_in_db_by_model(post_id: int, post: dict, session: SessionDep) -> Optional[Posts]`
  - `get_post_user_vote(post_id: int, session: SessionDep) -> Optional[schemas.posts.PostOutWithVotes]` (outer join votes, count)

### app/models/votes.py

- `class Votes(BaseModel, table=True)` with `__tablename__ = "votes"` and fields:
  - `post_id: int` fk `posts.id`, primary key
  - `user_id: int` fk `user.id`, primary key
  - `date: datetime` default now, server_default NOW
- Functions:
  - `create_vote_in_db_by_model(vote: dict, session: SessionDep) -> Optional[Votes]`
  - `delete_vote_in_db_by_model(vote: dict, session: SessionDep) -> Optional[Votes]`

### app/models/__init__.py

Re-export these symbols:
- `create_new_user_db`, `get_user_by_email_db`, `get_user_by_id`, `get_user_by_username_db`
- `get_session`
- `Votes`, `Posts`

### app/utils/helpers.py

- Constants/functions:
  - `DATA_DIR = Path(__file__).parent.parent.joinpath("data")` (note: this points under `app/`)
  - `_load_json(name: str) -> Any` (returns `[]` on any exception)
  - `_save_json(name: str, data) -> None` (best-effort)
  - `DATA = _load_json("data.json")`
  - `_find_post_index(post_id: int) -> Optional[int]`
- Exceptions:
  - `class AppException(Exception)` with `status_code: int` and `detail: str`
  - `async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse`

### app/utils/auth.py

- `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")`
- `get_secret_key() -> SymmetricKey`: `bytes.fromhex(settings.paseto_secret_key)` then `SymmetricKey.v4(...)`
- `create_paseto_token(username: str, expires_in_minutes: int | None = None) -> str`:
  - payload includes `username`, `iat`, `exp` (ISO format)
  - `paseto.create(..., purpose="local", exp_seconds=expires_in_minutes * 60)`
- `verify_paseto_token(token: str) -> dict`: `paseto.parse(key=..., token=..., purpose="local")`
- `get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User`:
  - expects `claims["message"].get("username")`
  - fetches user via `get_user_by_username_db`
  - raises `HTTPException(401)` when invalid

### app/utils/db_sql.py

- `DB_CONFIG = _load_json("db_config.json")`
- `_resolve_env_reference(value)`:
  - if string starts with `env:` then reads that environment variable and errors if missing
- `get_db_connection(env: str = "local")` returns `(conn, cur)` from psycopg3
- `__get_cursor(envName: str)` helper
- Raw SQL helpers:
  - `get_posts_from_db()`
  - `get_post_from_db(post_id: int)`
  - `create_post_in_db(post: dict)`
  - `update_post_in_db(post_id: int, post: dict)`
  - `delete_post_from_db(post_id: int)`

### app/routers/auth.py

- `router = APIRouter(prefix="/auth", tags=["auth"])`
- `@router.post("/login", response_model=schemas.users.LoginResponse)`
- `async def login(user_credentials: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)) -> LoginResponse`:
  - loads user by email (uses `username` field of OAuth2 form)
  - verifies Argon2 password
  - creates token via `create_paseto_token(username=user.username, expires_in_minutes=60)`
  - returns `LoginResponse(access_token=..., token_type="Bearer", username=user.username)`

### app/routers/posts.py

- `router = APIRouter(prefix="/posts", tags=["posts"])`
- `@router.get("/", response_model=List[schemas.posts.PostOutWithVotes])`
  - `async def get_posts(session: SessionDep, limit: int = 10, skip: int = 0, search: Optional[str] = "") -> List[PostOutWithVotes]`
  - query does outer join to votes and counts votes per post
- `@router.get("/{post_id}", response_model=PostOutWithVotes)`
  - `async def get_post(post_id: int, session: SessionDep)`
- `@router.post("/", status_code=201, response_model=PostCreate)`
  - `async def create_post(post: PostCreate, current_user: models.users.User = Depends(get_current_user), session: Session = Depends(get_session)) -> PostCreate`
- `@router.delete("/{post_id}", status_code=204)`
  - owner-only delete
- `@router.put("/{post_id}", response_model=PostCreate)`
  - owner-only update

### app/routers/users.py

- `router = APIRouter(prefix="/users", tags=["users"])`
- `@router.post("/", status_code=201, response_model=schemas.users.UserCreateResponse)`
  - `async def create_user(user: schemas.users.UserCreate, session: Session = Depends(get_session)) -> UserCreateResponse`
- `@router.get("/{user_id}", response_model=schemas.users.User)`
  - `async def get_user(user_id: int, current_user: schemas.users.User = Depends(get_current_user), session: Session = Depends(get_session)) -> User`
- `@router.get("/{username}", response_model=schemas.users.User)`
  - `async def get_user_by_username(username: str, current_user: schemas.users.User = Depends(get_current_user), session: Session = Depends(get_session)) -> User`
  - NOTE: This path conflicts with the `/{user_id}` route; preserve as-is for faithful regeneration.

### app/routers/votes.py

- `router = APIRouter(prefix="/votes", tags=["votes"])`
- `@router.post("/", status_code=201, response_model=schemas.votes.VoteResponse)`
- `async def create_vote(vote: schemas.votes.VoteCreate, current_user: schemas.users.User = Depends(utils.get_current_user), session: SessionDep = None) -> VoteResponse`:
  - direction 1: insert vote if not existing else 409
  - direction 0: delete vote if existing else 404
  - NOTE: The session default is `None` in current implementation; preserve signature.

### app/schemas/users.py

Generate these Pydantic models (field names/types must match):
- `User(id: Optional[int] = None, username: str, email: EmailStr)`
- `UserCreate(username: str, email: EmailStr, password: str)`
- `UserCreateResponse(id: int, username: str, email: EmailStr)`
- `UserLogin(email: EmailStr, password: str)`
- `LoginResponse(access_token: str, token_type: str, username: str)`
- `Token(access_token: str, token_type: str)`
- `TokenData(username: Optional[str] = None)`

### app/schemas/posts.py

Generate these Pydantic models:
- `DBConfig(host: str, port: int, dbname: str, user: str, password: str)`
- `Post(id: Optional[int] = None, title: str, content: str, owner_id: int, published: bool = True, date: Optional[datetime] = None)`
- `Posts(posts: List[Post])`
- `PostCreate(title: str, content: str, published: bool = True)`
- `PostUpdate(title: str, content: str, published: bool)`
- `PostOut(Post)` with `owner: users.User`
- `PostOutWithVotes` with fields: `Posts: PostOut` and `votes: int` (note the capitalized `Posts` field name)

### app/schemas/votes.py

Generate these Pydantic models:
- `VoteCreate(post_id: int, direction: Annotated[int, Field(ge=0, le=1)])`
- `VoteResponse(post_id: int, user_id: int, date: Optional[datetime] = None)`

## Faithful Regeneration Notes

- Preserve module names, symbol names, and router prefixes exactly.
- Prefer matching the *current implementation* (even if it has quirks) over “idealized” refactors.
- Do not add extra endpoints or features beyond what’s described here.

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
