import uvicorn
from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from msg.msg_log_server import  get_message_history
from uuid import UUID

router = APIRouter(
    prefix="/message/history",
    tags=["message"],
)

@router.get("/")
async def read_message_history(
    channel_id: UUID
):
    history = await get_message_history(channel_id)
    
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"頻道 {channel_id} 沒有找到任何訊息或頻道不存在"
        )
        
    return history