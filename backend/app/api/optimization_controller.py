from fastapi import APIRouter, HTTPException
import requests
import os

router = APIRouter(prefix="/optimization", tags=["optimization"])

# Django API base URL
DJANGO_API_BASE = os.getenv('DJANGO_API_BASE', 'http://localhost:8000/api')


@router.post("/trigger")
async def trigger_optimization() -> dict:
    """Trigger prompt optimization cycle"""
    # TODO: Implement optimization trigger through Django API
    raise HTTPException(status_code=501, detail="Optimization trigger not implemented yet")


@router.get("/status")
async def get_optimization_status() -> dict:
    """Get current optimization status"""
    try:
        response = requests.get(f"{DJANGO_API_BASE}/optimization/status/")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Django API error: {str(e)}")