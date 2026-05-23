from fastapi import APIRouter

from backend.app.schemas.style_check import (
    NormalizeCodeRequest,
    NormalizeCodeResponse,
    StyleCheckRequest,
    StyleCheckResponse,
)
from backend.app.services.normalization_service import normalize_code
from backend.app.services.style_check_service import check_code_style

router = APIRouter(tags=["style-check"])


@router.post("/style-check", response_model=StyleCheckResponse)
def style_check(request: StyleCheckRequest) -> StyleCheckResponse:
    return check_code_style(request)


@router.post("/normalize-code", response_model=NormalizeCodeResponse)
def normalize_code_endpoint(request: NormalizeCodeRequest) -> NormalizeCodeResponse:
    return normalize_code(request)
