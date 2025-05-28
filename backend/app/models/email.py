from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class EmailMessage(BaseModel):
    id: str
    subject: str
    body: str
    sender: str
    timestamp: datetime


class DraftReason(BaseModel):
    text: str
    confidence: float


class EmailDraft(BaseModel):
    id: str
    content: str
    reasons: List[DraftReason]


class FeedbackAction(BaseModel):
    action: str  # "accept", "reject", "edit", "ignore"
    reason: Optional[str] = None
    edited_content: Optional[str] = None


class UserFeedback(BaseModel):
    email_id: str
    draft_id: str
    action: FeedbackAction
    reason_ratings: dict[str, bool]  # reason_id -> like/dislike
    timestamp: datetime