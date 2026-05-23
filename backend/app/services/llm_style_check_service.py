import re
from pathlib import Path
from typing import Literal

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import yaml

from backend.app.config import get_settings
from backend.app.schemas.style_check import (
    ResponseMetadata,
    Severity,
    StyleCheckRequest,
    StyleCheckResponse,
    Suggestion,
    SuggestionType,
)


class LLMStyleCheckResult(BaseModel):
    status: Literal["clean", "has_suggestions", "partial"]
    message: str
    suggestions: list[Suggestion] = Field(default_factory=list)
    advanced_tip: str | None = None


def _load_skill_instructions() -> str:
    skills_dir = Path(__file__).resolve().parents[1] / "skills"
    instructions: list[str] = []

    for path in sorted(skills_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except OSError:
            continue

        title = data.get("title")
        llm_instruction = data.get("llm_instruction")
        guidance = data.get("guidance") or {}
        if title and llm_instruction:
            instructions.append(f"- {title}：{llm_instruction.strip()}")
        if guidance.get("principle"):
            instructions.append(f"  原则：{guidance['principle']}")
        if guidance.get("good_example") and guidance.get("bad_example"):
            instructions.append(
                f"  示例：推荐 {guidance['good_example']}，避免 {guidance['bad_example']}"
            )

    return "\n".join(instructions) if instructions else "无额外 skills。"


def _is_whitespace_only_suggestion(suggestion: Suggestion) -> bool:
    if not suggestion.replacement:
        return False

    original_without_space = "".join(suggestion.original.split())
    replacement_without_space = "".join(suggestion.replacement.split())
    return original_without_space == replacement_without_space


def _is_grounded_in_code(suggestion: Suggestion, code: str, line_count: int) -> bool:
    original = suggestion.original.strip()
    if not original:
        return False
    if suggestion.line_start > line_count or suggestion.line_end > line_count:
        return False
    return original in code


def _has_overlapping_original(existing: list[Suggestion], original: str) -> bool:
    normalized_original = "".join(original.split())
    return any("".join(suggestion.original.split()) == normalized_original for suggestion in existing)


def _looks_like_linked_list_skill_suggestion(suggestion: Suggestion) -> bool:
    concept = suggestion.course_concept or ""
    return "链表指针命名" in concept


def _limit_linked_list_skill_suggestions(suggestions: list[Suggestion], max_count: int = 2) -> list[Suggestion]:
    limited: list[Suggestion] = []
    skill_count = 0

    for suggestion in suggestions:
        if _looks_like_linked_list_skill_suggestion(suggestion):
            if skill_count >= max_count:
                continue
            skill_count += 1
        limited.append(suggestion)

    return limited


def _extract_function_body(lines: list[str], start_index: int) -> str:
    body_lines: list[str] = []
    brace_balance = 0

    for line in lines[start_index:]:
        body_lines.append(line)
        brace_balance += line.count("{") - line.count("}")
        if body_lines and brace_balance <= 0:
            break

    return "\n".join(body_lines)


def _infer_function_name(function_name: str, signature: str, body: str) -> str | None:
    if function_name == "f" and "new node" in body and "return" in body:
        return "createLinkedList"
    if function_name == "g" and "cout" in body and "->next" in body:
        return "printList"
    if len(function_name) == 1:
        return "renameToMeaningfulName"
    return None


def _build_function_naming_suggestions(request: StyleCheckRequest, existing: list[Suggestion]) -> list[Suggestion]:
    if request.lang not in {"c", "cpp"}:
        return []

    suggestions: list[Suggestion] = []
    lines = request.code.splitlines()
    signature_pattern = re.compile(
        r"^(\s*(?:[A-Za-z_][\w:<>]*\s+)*(?:[A-Za-z_][\w:<>]*\s*\*?)\s+)([A-Za-z_]\w*)\s*(\([^;]*\)\s*\{)"
    )

    for index, line in enumerate(lines):
        match = signature_pattern.search(line)
        if not match:
            continue

        function_name = match.group(2)
        if function_name == "main" or len(function_name) > 2:
            continue

        body = _extract_function_body(lines, index)
        replacement_name = _infer_function_name(function_name, line, body)
        if not replacement_name:
            continue

        original = line.rstrip()
        if _has_overlapping_original(existing + suggestions, original):
            continue

        replacement = f"{match.group(1)}{replacement_name}{match.group(3)}"
        suggestions.append(
            Suggestion(
                id=f"function_naming_{index + 1}_{function_name}",
                type=SuggestionType.naming,
                severity=Severity.info,
                line_start=index + 1,
                line_end=index + 1,
                original=original,
                replacement=replacement,
                reason=f"函数名 {function_name} 过于简略，建议改为能表达功能的名称。",
                course_concept="有意义的函数命名",
                apply_safe=False,
                confidence=0.88,
            )
        )

        if len(suggestions) >= 1:
            break

    return suggestions


def _build_linked_list_skill_suggestions(request: StyleCheckRequest, existing: list[Suggestion]) -> list[Suggestion]:
    if request.lang not in {"c", "cpp"}:
        return []
    if "->next" not in request.code and ".next" not in request.code:
        return []

    default_role_names = {"h": "head", "p": "cur", "q": "prev", "t": "newNode"}
    suggestions: list[Suggestion] = []
    lines = request.code.splitlines()

    for line_number, line in enumerate(lines, start=1):
        match = re.search(r"\b(?:node|Node)\s*\*\s*(h|p|q|t)\b", line)
        if not match:
            continue

        old_name = match.group(1)
        local_context = "\n".join(lines[line_number - 1 : line_number + 12])
        if old_name == "p" and re.search(r"\bp\s*->\s*next\s*=", local_context):
            new_name = "tail"
        else:
            new_name = default_role_names[old_name]
        original = line.rstrip()
        if _has_overlapping_original(existing + suggestions, original):
            continue

        suggestions.append(
            Suggestion(
                id=f"skill_linked_list_pointer_{line_number}_{old_name}",
                type=SuggestionType.naming,
                severity=Severity.info,
                line_start=line_number,
                line_end=line_number,
                original=original,
                replacement=re.sub(
                    rf"\b{re.escape(old_name)}\b",
                    new_name,
                    original,
                    count=1,
                ),
                reason=(
                    f"链表指针名 {old_name} 过于简略，建议使用 {new_name} 表达它在链表中的角色。"
                ),
                course_concept="链表指针命名规范",
                apply_safe=False,
                confidence=0.86,
            )
        )

        if len(suggestions) >= 2:
            break

    return suggestions


def check_code_style_with_llm(request: StyleCheckRequest) -> StyleCheckResponse:
    settings = get_settings()
    if not settings.llm_enabled or not settings.siliconflow_api_key:
        raise RuntimeError("LLM is disabled or SILICONFLOW_API_KEY is not configured.")

    parser = PydanticOutputParser(pydantic_object=LLMStyleCheckResult)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "你是数据结构课程的编程助教。"
                    "你的任务是帮助学生提升 C/C++ 代码的可读性和规范性。"
                    "你只能提出轻量、局部、教学友好的建议。"
                    "所有自然语言输出必须使用简体中文，包括 message、reason 和 course_concept。"
                    "禁止改变算法逻辑、数据结构、控制流、输入输出协议、时间复杂度或空间复杂度。"
                    "禁止引入新库、替换算法、进行性能优化或完整重写代码。"
                    "不要提出仅仅关于运算符、逗号、括号或分号周围空格的建议；"
                    "例如不要建议把 a+b 改成 a + b，或把 cout<<x 改成 cout << x。"
                    "优先检查函数名、结构体名、关键变量名是否表达了职责，再结合课程 skills 补充建议。"
                    "如果建议添加注释，必须给出具体推荐的注释文本。"
                    "original 必须逐字复制代码中真实存在的片段，不要改写标点、空格或大小写。"
                    "课程 skills 是补充规则，不能替代通用可读性建议。"
                    "如果代码已经规范，请返回 clean 和空 suggestions。"
                ),
            ),
            (
                "human",
                (
                    "请检查下面代码的可读性规范。\n\n"
                    "语言：{lang}\n"
                    "模式：{mode}\n"
                    "文件名：{file_name}\n"
                    "课程阶段：{course_stage}\n\n"
                    "允许的常见缩写：num, cnt, idx, res, tmp, cur, prev, next, head, tail。\n"
                    "建议类型只能是：format, naming, comment, readability, structure。\n"
                    "严重程度只能是：info 或 warning。\n"
                    "最多返回 5 条建议。\n"
                    "建议应覆盖不同问题类型；同一类链表指针命名建议最多返回 2 条，避免挤掉函数命名、结构体命名或注释建议。\n"
                    "所有自然语言字段必须使用简体中文，不要输出英文解释。\n"
                    "不要返回只改变空格、不改变命名、结构或表达含义的建议。\n"
                    "original 必须是代码里真实出现的原文片段。\n"
                    "replacement 必须是局部替换片段；如果不适合自动替换，请设为 null，并将 apply_safe 设为 false。\n"
                    "当 type 为 comment 时，replacement 必须给出建议插入的完整注释文本，或包含该注释的局部代码片段；不要只写 null。\n\n"
                    "课程 skills：\n{skill_instructions}\n\n"
                    "代码：\n```{lang}\n{code}\n```\n\n"
                    "{format_instructions}"
                ),
            ),
        ]
    )

    model = ChatOpenAI(
        model=settings.siliconflow_model,
        api_key=settings.siliconflow_api_key,
        base_url=settings.siliconflow_base_url,
        temperature=0.1,
        timeout=settings.llm_timeout_seconds,
        max_retries=1,
    )

    chain = prompt | model | parser
    result = chain.invoke(
        {
            "lang": request.lang,
            "mode": request.mode.value,
            "file_name": request.context.file_name or "",
            "course_stage": request.context.course_stage or "",
            "code": request.code,
            "skill_instructions": _load_skill_instructions(),
            "format_instructions": parser.get_format_instructions(),
        }
    )

    if not isinstance(result, LLMStyleCheckResult):
        raise RuntimeError("LLM output did not parse to LLMStyleCheckResult.")

    line_count = len(request.code.splitlines()) or 1
    suggestions = [
        suggestion
        for suggestion in result.suggestions
        if not _is_whitespace_only_suggestion(suggestion)
        and _is_grounded_in_code(suggestion, request.code, line_count)
    ]
    suggestions = _limit_linked_list_skill_suggestions(suggestions)
    suggestions.extend(_build_function_naming_suggestions(request, suggestions))
    suggestions.extend(_build_linked_list_skill_suggestions(request, suggestions))
    suggestions = _limit_linked_list_skill_suggestions(suggestions)
    suggestions = suggestions[:5]
    status: Literal["clean", "has_suggestions", "partial"] = "has_suggestions" if suggestions else "clean"
    message = f"发现 {len(suggestions)} 处可读性建议。" if suggestions else "代码整体规范，可读性较好。"

    return StyleCheckResponse(
        status=status,
        message=message,
        formatted_code=request.code,
        suggestions=suggestions,
        advanced_tip=result.advanced_tip,
        metadata=ResponseMetadata(
            ruleset_version="2026-spring-v1",
            llm_used=True,
            workflow_engine="langchain",
        ),
    )
