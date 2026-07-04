from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from core.limiter import limiter
from services.events import bus
from core.logging import EventLoggingSubscriber, RequestResponseMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title="Resume-Libre API", version="2.1.0")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ─── CORS ────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://localhost:5173",
            "https://resume-libre.vercel.app",
            "https://resume-libre-emaadansaris-projects.vercel.app",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Request/Response logging middleware ────────────
    app.add_middleware(RequestResponseMiddleware)

    # ─── Register event logging subscriber ──────────────
    EventLoggingSubscriber.register(bus)

    # ─── Include routers ────────────────────────────────
    from routers import health, generation, export, resumes, templates, debug

    app.include_router(health.router)
    app.include_router(generation.router)
    app.include_router(export.router)
    app.include_router(resumes.router)
    app.include_router(templates.router)
    app.include_router(debug.router)

    return app
