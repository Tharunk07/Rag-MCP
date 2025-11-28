from app import app
import logging
from app.models import ChatRequest
from motor.motor_asyncio import AsyncIOMotorClient
from app.database import set_db
from config import API_PREFIX, MONGO_DB_URI, MONGO_DB
from fastapi.responses import StreamingResponse
from app.tasks import claude_chat_response

_client = AsyncIOMotorClient(MONGO_DB_URI)
_db = _client[MONGO_DB]

logging.info("MongoDB connected successfully.")
set_db(_db) 


@app.post(f"{API_PREFIX}/llm-chat", tags = ["LLM Chat"])
async def llm_chat_endpoint(request_body: ChatRequest):

    try:
        user_query = request_body.question
        tools_enabled = request_body.tools_enabled
        is_new_thread = request_body.is_new_thread
        thread_id = request_body.thread_id

        return StreamingResponse(claude_chat_response(user_query, tools_enabled, is_new_thread, thread_id), media_type="application/json")

    except Exception as e:
        logging.error(f"Error in /llm-chat endpoint: {str(e)}")
        return {"status": "error", "message": str(e)}