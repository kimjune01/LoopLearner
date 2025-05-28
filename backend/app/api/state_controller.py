from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from ..models.state import SystemState
from ..services.state_manager import StateManager

router = APIRouter(prefix="/state", tags=["state"])


# TODO: Add dependency injection for state manager
async def get_state_manager() -> StateManager:
    raise NotImplementedError("State manager dependency not configured")


@router.get("/", response_model=SystemState)
async def get_current_state(
    state_manager: StateManager = Depends(get_state_manager)
) -> SystemState:
    """Get current system state"""
    try:
        state = await state_manager.load_state()
        if state is None:
            raise HTTPException(status_code=404, detail="No state found")
        return state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_state(
    state_manager: StateManager = Depends(get_state_manager)
) -> Dict[str, Any]:
    """Export system state"""
    try:
        return await state_manager.export_state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_state(
    state_data: Dict[str, Any],
    state_manager: StateManager = Depends(get_state_manager)
) -> dict:
    """Import system state"""
    try:
        success = await state_manager.import_state(state_data)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))