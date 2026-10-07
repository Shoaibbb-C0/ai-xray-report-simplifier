"""Main FastAPI application entry point."""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.api.v1.router import router as api_v1_router
from backend.app.services.ml_service import MLServiceError


def create_app() -> FastAPI:
    """Factory creating and configuring the FastAPI instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Backend API for AI X-Ray Patient Support Platform",
    )

    # Cross-Origin Resource Sharing (CORS) setup
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Core health check endpoint
    @app.get("/health", status_code=status.HTTP_200_OK)
    def health_check():
        """Root health endpoint verifying service liveness."""
        return {
            "status": "ok",
            "service": settings.SERVICE_NAME,
        }

    # Mount versioned API routes
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    # Global ML service exception handling
    @app.exception_handler(MLServiceError)
    async def ml_service_exception_handler(request: Request, exc: MLServiceError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(exc), "type": "ml_service_error"},
        )

    # Generic unhandled exception fallback
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred.", "type": "server_error"},
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
