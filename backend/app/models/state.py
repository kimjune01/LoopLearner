from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class SystemPrompt(BaseModel):
    content: str
    version: int
    created_at: datetime


class EvaluationSnapshot(BaseModel):
    id: str
    email_id: str
    expected_outcome: str
    prompt_version: int
    performance_score: float
    created_at: datetime


class UserPreference(BaseModel):
    key: str
    value: str
    description: str
    created_at: datetime


class SystemState(BaseModel):
    current_prompt: SystemPrompt
    user_preferences: List[UserPreference]
    evaluation_snapshots: List[EvaluationSnapshot]
    optimization_history: List[Dict[str, Any]]
    confidence_score: float
    last_updated: datetime