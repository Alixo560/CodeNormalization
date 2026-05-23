from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class CheckMode(str, Enum):
    basic = "basic"
    advanced = "advanced"


class SuggestionType(str, Enum):
    format = "format"
    naming = "naming"
    comment = "comment"
    readability = "readability"
    structure = "structure"


class Severity(str, Enum):
    info = "info"
    warning = "warning"


class SelectedRange(BaseModel):
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)


class RequestContext(BaseModel):
    file_name: str | None = None
    course_stage: str | None = None
    selected_range: SelectedRange | None = None


class UserPreferences(BaseModel):
    ignored_rule_ids: list[str] = Field(default_factory=list)


class StyleCheckRequest(BaseModel):
    code: str = Field(min_length=1)
    lang: Literal["cpp", "c"] = "cpp"
    mode: CheckMode = CheckMode.basic
    context: RequestContext = Field(default_factory=RequestContext)
    user_preferences: UserPreferences = Field(default_factory=UserPreferences)


class Suggestion(BaseModel):
    id: str
    type: SuggestionType
    severity: Severity
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    original: str
    replacement: str | None = None
    reason: str
    course_concept: str | None = None
    apply_safe: bool = False
    confidence: float = Field(ge=0, le=1)


class ResponseMetadata(BaseModel):
    ruleset_version: str
    llm_used: bool
    workflow_engine: str


class StyleCheckResponse(BaseModel):
    status: Literal["clean", "has_suggestions", "partial"]
    message: str
    formatted_code: str | None = None
    suggestions: list[Suggestion] = Field(default_factory=list)
    advanced_tip: str | None = None
    metadata: ResponseMetadata
