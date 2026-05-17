import logging
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth, files, synthesis

# Show our custom log messages in Heroku logs
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup (dev convenience — use Alembic in prod)."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"WARNING: Could not create tables on startup: {e}")
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — match explicit origins + any *.vercel.app or *.herokuapp.com
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
origin_regex = r"https://[a-z0-9-]+\.vercel\.app|https://[a-z0-9-]+\.herokuapp\.com"
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=origin_regex,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(synthesis.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
