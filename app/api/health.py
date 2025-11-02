from fastapi import APIRouter

# Health router kept prefix-free to expose exactly /health and /health/ready
router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
def health() -> dict:
    """Return a simple OK payload to indicate the app is alive."""
    return {"status": "ok"}


@router.get("/health/ready", summary="Readiness probe")
def ready() -> dict:
    """
    Return a readiness payload.
    NOTE: Tests expect a boolean flag 'ready' set to True.
    Keeping a human-readable 'status' alongside for clarity.
    """
    return {"status": "ready", "ready": True}
