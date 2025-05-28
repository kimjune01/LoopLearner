from fastapi import APIRouter, HTTPException
from typing import List
import requests
import os

router = APIRouter(prefix="/emails", tags=["emails"])

# Django API base URL
DJANGO_API_BASE = os.getenv('DJANGO_API_BASE', 'http://localhost:8000/api')


@router.post("/generate")
async def generate_fake_email(scenario_type: str = "random"):
    """Generate a fake email for testing"""
    try:
        response = requests.post(
            f"{DJANGO_API_BASE}/emails/generate/",
            json={"scenario_type": scenario_type}
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Django API error: {str(e)}")


@router.post("/{email_id}/drafts")
async def generate_drafts(email_id: int):
    """Generate draft responses for an email"""
    try:
        response = requests.post(
            f"{DJANGO_API_BASE}/emails/{email_id}/drafts/generate/"
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Django API error: {str(e)}")


@router.post("/{email_id}/feedback")
async def submit_feedback(email_id: int, feedback_data: dict):
    """Submit user feedback for an email/draft"""
    try:
        response = requests.post(
            f"{DJANGO_API_BASE}/emails/{email_id}/feedback/",
            json=feedback_data
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Django API error: {str(e)}")


@router.get("/")
async def list_emails():
    """List all emails"""
    try:
        response = requests.get(f"{DJANGO_API_BASE}/emails/")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Django API error: {str(e)}")