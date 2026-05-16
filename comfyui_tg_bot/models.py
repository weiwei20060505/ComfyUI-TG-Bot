from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WorkflowTarget(BaseModel):
    node_id: str
    input: str


class WorkflowFieldMapping(BaseModel):
    required: bool = False
    target: WorkflowTarget


class AspectRatioSize(BaseModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class WorkflowConfig(BaseModel):
    id: str
    name: str
    description: str = ""
    selection_hint: str = ""
    workflow_file: str
    is_default: bool = False
    fields: dict[str, WorkflowFieldMapping]
    aspect_ratios: dict[str, AspectRatioSize]
    defaults: dict[str, Any] = Field(default_factory=dict)


class GeminiParseResult(BaseModel):
    workflow_id: str
    positive_prompt: str
    negative_prompt: str
    aspect_ratio: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class GenerationJob(BaseModel):
    chat_id: int
    user_id: int
    prompt: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    workflow_id: str | None = None
    parse_result: GeminiParseResult | None = None
