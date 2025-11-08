import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from msg.msg_log_server import init_db_pool, close_db_pool, get_message_history # 引入分離的資料庫函數
from uuid import UUID

app = FastAPI()

@app.get("/history/{channel_id}")
async def read_message_history(
    channel_id: UUID, 
    limit: int = 100
):
    # 當 FastAPI 將 path 參數自動轉換為 UUID 型別時，
    # 如果路徑中的值不是一個有效的 UUID 格式，FastAPI 會自動返回 422 Unprocessable Entity 錯誤。
    # 因此，我們只需要專注於 limit 的驗證。
    
    # 檢查 limit 參數
    if limit <= 0 or limit > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Limit 必須在 1 到 500 之間"
        )
    
    # 直接呼叫 db.py 中的函數
    # 注意：get_message_history 必須能夠接受 UUID 作為 channel_id
    history = await get_message_history(channel_id, limit)
    
    if not history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"頻道 {channel_id} 沒有找到任何訊息或頻道不存在"
        )
        
    return history

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)