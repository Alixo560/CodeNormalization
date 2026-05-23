from backend.app.schemas.style_check import (
    ResponseMetadata,
    Severity,
    StyleCheckRequest,
    StyleCheckResponse,
    Suggestion,
    SuggestionType,
)
from backend.app.services.structure_detection_service import detect_structure


def check_code_style_deterministic(request: StyleCheckRequest) -> StyleCheckResponse:
    """Return deterministic MVP suggestions before clang-format and AST checks are wired in."""
    suggestions: list[Suggestion] = []
    lines = request.code.splitlines()

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("int a") or stripped.startswith("int b"):
            suggestions.append(
                Suggestion(
                    id=f"naming_{index:03d}",
                    type=SuggestionType.naming,
                    severity=Severity.info,
                    line_start=index,
                    line_end=index,
                    original=line,
                    replacement=line.replace("int a, b", "int left_value, right_value"),
                    reason="变量名应表达其含义，便于阅读输入数据的用途。",
                    course_concept="变量命名与代码可读性",
                    apply_safe=True,
                    confidence=0.72,
                )
            )

    status = "has_suggestions" if suggestions else "clean"
    message = f"发现 {len(suggestions)} 处可读性建议" if suggestions else "代码风格良好，可读性高。"

    return StyleCheckResponse(
        status=status,
        message=message,
        formatted_code=request.code,
        structure_detection=detect_structure(request),
        suggestions=suggestions,
        advanced_tip=None,
        metadata=ResponseMetadata(
            ruleset_version="2026-spring-v1",
            llm_used=False,
            workflow_engine="deterministic",
        ),
    )
