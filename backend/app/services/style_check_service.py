import logging

from backend.app.schemas.style_check import StyleCheckRequest, StyleCheckResponse
from backend.app.services.deterministic_style_check_service import check_code_style_deterministic
from backend.app.services.llm_style_check_service import check_code_style_with_llm

logger = logging.getLogger(__name__)


def check_code_style(request: StyleCheckRequest) -> StyleCheckResponse:
    try:
        return check_code_style_with_llm(request)
    except Exception:
        logger.exception("LLM 风格检查失败，已回退到本地规则；请检查 SILICONFLOW_* 配置、网络与后端日志。")
        return check_code_style_deterministic(request)
