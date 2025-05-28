from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..models.email import EmailMessage, EmailDraft, UserFeedback
from ..services.email_generator import EmailGenerator
from ..services.llm_provider import LLMProvider

router = APIRouter(prefix="/emails", tags=["emails"])


# TODO: Add dependency injection for services
async def get_email_generator() -> EmailGenerator:
    raise NotImplementedError("Email generator dependency not configured")


async def get_llm_provider() -> LLMProvider:
    raise NotImplementedError("LLM provider dependency not configured")


@router.post("/generate", response_model=EmailMessage)
async def generate_fake_email(
    scenario_type: str = "random",
    email_generator: EmailGenerator = Depends(get_email_generator)
) -> EmailMessage:
    """Generate a fake email for testing"""
    try:
        email = await email_generator.generate_synthetic_email(scenario_type)
        return email
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{email_id}/drafts", response_model=List[EmailDraft])
async def generate_drafts(
    email_id: str,
    llm_provider: LLMProvider = Depends(get_llm_provider)
) -> List[EmailDraft]:
    """Generate draft responses for an email"""
    # TODO: Implement draft generation
    raise HTTPException(status_code=501, detail="Draft generation not implemented")


@router.post("/{email_id}/feedback")
async def submit_feedback(
    email_id: str,
    feedback: UserFeedback
) -> dict:
    """Submit user feedback for an email/draft"""
    # TODO: Implement feedback processing
    raise HTTPException(status_code=501, detail="Feedback processing not implemented")