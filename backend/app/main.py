from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.style_check import router as style_check_router
from backend.app.config import get_settings

app = FastAPI(
    title="Data Structure Code Style Guidance API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(style_check_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str | bool]:
    s = get_settings()
    return {
        "status": "ok",
        "llm_enabled": s.llm_enabled,
        "siliconflow_api_key_configured": bool(s.siliconflow_api_key and s.siliconflow_api_key.strip()),
    }
