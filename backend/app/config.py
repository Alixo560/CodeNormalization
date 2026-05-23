import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

# 从仓库根目录或 backend 目录加载 .env，避免仅依赖进程 cwd（从子目录启动 uvicorn 时 cwd 可能不是仓库根）。
_repo_root = Path(__file__).resolve().parents[2]
_backend_root = Path(__file__).resolve().parents[1]
load_dotenv(_repo_root / ".env")
load_dotenv(_backend_root / ".env")
load_dotenv()


class Settings(BaseModel):
    llm_enabled: bool = os.getenv("LLM_ENABLED", "1") != "0"
    siliconflow_api_key: str | None = os.getenv("SILICONFLOW_API_KEY")
    siliconflow_base_url: str = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
    siliconflow_model: str = os.getenv("SILICONFLOW_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    llm_timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
