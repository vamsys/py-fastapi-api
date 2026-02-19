from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .models.db_orm import create_db_and_tables
from .routers import auth_router, posts_router, users_router, votes_router
from .utils.helpers import AppException, app_exception_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    yield
    # Shutdown (optional cleanup code here)


app = FastAPI(lifespan=lifespan)

cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

app.add_middleware(
	CORSMiddleware,
	allow_origins=cors_origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
	expose_headers=["Content-Type", "Authorization"],
)

app.add_exception_handler(AppException, app_exception_handler)
app.include_router(auth_router)
app.include_router(posts_router)
app.include_router(users_router)
app.include_router(votes_router)
@app.get("/")
async def read_root():
	"""Return a simple welcome message.

	This is the root endpoint, useful for sanity checking that the
	application is up and running.
	"""
	return {"Hello": "Welcome to KPI One"}