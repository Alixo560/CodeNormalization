from fastapi import APIRouter

from backend.app.schemas.style_check import StyleCheckRequest, StyleCheckResponse
from backend.app.services.style_check_service import check_code_style

router = APIRouter(tags=["style-check"])


@router.post("/style-check", response_model=StyleCheckResponse)
def style_check(request: StyleCheckRequest) -> StyleCheckResponse:
    return check_code_style(request)
