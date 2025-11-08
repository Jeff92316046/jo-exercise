import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from msg_log_server import init_db_pool, close_db_pool, get_message_history # 引入分離的資料庫函數

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await init_db_pool()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db_pool()

@app.get("/history/{channel_id}")
async def read_message_history(
    channel_id: int, 
    limit: int = 100
):
    if channel_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Channel ID 必須為正整數"
        )
    if limit <= 0 or limit > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Limit 必須在 1 到 500 之間"
        )
    
    # 直接呼叫 db.py 中的函數
    history = await get_message_history(channel_id, limit)
    
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"頻道 {channel_id} 沒有找到任何訊息或頻道不存在"
        )
        
    return history

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)