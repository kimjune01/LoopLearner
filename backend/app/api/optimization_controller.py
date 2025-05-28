from fastapi import APIRouter, HTTPException, Depends
from ..services.optimizer import PromptOptimizer
from ..models.state import SystemPrompt

router = APIRouter(prefix="/optimization", tags=["optimization"])


# TODO: Add dependency injection for optimizer
async def get_optimizer() -> PromptOptimizer:
    raise NotImplementedError("Optimizer dependency not configured")


@router.post("/trigger")
async def trigger_optimization(
    optimizer: PromptOptimizer = Depends(get_optimizer)
) -> dict:
    """Trigger prompt optimization cycle"""
    # TODO: Implement optimization trigger
    raise HTTPException(status_code=501, detail="Optimization not implemented")


@router.get("/status")
async def get_optimization_status() -> dict:
    """Get current optimization status"""
    # TODO: Implement status check
    return {"status": "not_implemented"}