import difflib

from backend.app.schemas.style_check import (
    AppliedChange,
    BlockedChange,
    NormalizeCodeRequest,
    NormalizeCodeResponse,
    ResponseMetadata,
    Suggestion,
)
from backend.app.services.deterministic_style_check_service import check_code_style_deterministic
from backend.app.services.structure_detection_service import detect_structure
from backend.app.services.visual_ir_service import build_visual_ir


def normalize_code(request: NormalizeCodeRequest) -> NormalizeCodeResponse:
    """Apply only safe deterministic suggestions and return traceable normalization artifacts."""
    style_result = check_code_style_deterministic(request)
    normalized_code, applied_changes, blocked_changes = _apply_safe_suggestions(
        request.code,
        style_result.suggestions,
    )
    structure_detection = detect_structure(request)
    diff = _build_unified_diff(request.code, normalized_code)
    status = "normalized" if applied_changes else "unchanged"
    message = (
        f"已应用 {len(applied_changes)} 处安全规范化修改。"
        if applied_changes
        else "暂无可自动应用的安全规范化修改。"
    )

    return NormalizeCodeResponse(
        status=status,
        message=message,
        normalized_code=normalized_code,
        diff=diff,
        structure_detection=structure_detection,
        visual_ir=build_visual_ir(normalized_code, structure_detection),
        suggestions=style_result.suggestions,
        applied_changes=applied_changes,
        blocked_changes=blocked_changes,
        metadata=ResponseMetadata(
            ruleset_version="2026-spring-v1",
            llm_used=False,
            workflow_engine="deterministic-normalization",
        ),
    )


def _apply_safe_suggestions(
    code: str,
    suggestions: list[Suggestion],
) -> tuple[str, list[AppliedChange], list[BlockedChange]]:
    normalized_code = code
    applied_changes: list[AppliedChange] = []
    blocked_changes: list[BlockedChange] = []

    for suggestion in suggestions:
        if not suggestion.apply_safe or not suggestion.replacement:
            blocked_changes.append(
                BlockedChange(
                    id=suggestion.id,
                    type=suggestion.type,
                    safety="review_required",
                    reason="该建议需要人工确认，未自动应用。",
                )
            )
            continue

        if suggestion.original not in normalized_code:
            blocked_changes.append(
                BlockedChange(
                    id=suggestion.id,
                    type=suggestion.type,
                    safety="review_required",
                    reason="未在当前代码中找到建议对应的原始片段，未自动应用。",
                )
            )
            continue

        normalized_code = normalized_code.replace(suggestion.original, suggestion.replacement, 1)
        applied_changes.append(
            AppliedChange(
                id=suggestion.id,
                type=suggestion.type,
                safety="safe",
                reason=suggestion.reason,
            )
        )

    return normalized_code, applied_changes, blocked_changes


def _build_unified_diff(original_code: str, normalized_code: str) -> str | None:
    if original_code == normalized_code:
        return None

    diff_lines = difflib.unified_diff(
        original_code.splitlines(),
        normalized_code.splitlines(),
        fromfile="original",
        tofile="normalized",
        lineterm="",
    )
    return "\n".join(diff_lines)
