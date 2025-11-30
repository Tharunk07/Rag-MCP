from app.database import insert_one_data, find_data
import logging
import json
import uuid
from app.database.mongo_connection import claude_usage_data
from app.utils import format_chat_history_as_dicts, mcp_chat_response_generation
from app.utils.claude_utils import send_google_chat_alert
from datetime import datetime

async def claude_usage_alert(today_date: str):
    try:

        claude_usage = await claude_usage_data(today_date)
        logging.info(f"Claude usage for {today_date}: {claude_usage} tokens")

        if claude_usage >= 50000:
            alert_message = f"Claude usage alert: Total Claude tokens used today ({today_date}) is {claude_usage}"
            await send_google_chat_alert(alert_message)

    except Exception as e:
        logging.error(f"Claude usage alert failed: {e}", exc_info=True)
        
async def claude_chat_response(user_query, tools_enabled, is_new_thread, thread_id  ):
    try:
        history = []
        llm_response = ""
        usage = []


        if is_new_thread:
            yield json.dumps({"type":"threadID", "content": str(uuid.uuid4())}) + "\n\n"
            history = [{"role":"user", "content": user_query}]

        else:
            past_chats = await find_data("chat_storage", {"thread_id": thread_id})
            history = format_chat_history_as_dicts(past_chats)
            history.append({"role":"user", "content": user_query})

        async for event in mcp_chat_response_generation(history, tools_enabled):
            if event.type == "content_block_delta":
                if hasattr(event, "delta") and hasattr(event.delta, "text"):
                    llm_response += event.delta.text
                    yield json.dumps({"type": "text", "content": event.delta.text}) + "\n\n"
                
            elif event.type == "message_delta":
                usage_data = {
                    "type": "text_generation",
                    "model": "claude",
                    "total_tokens": (event.usage.input_tokens or 0) + (event.usage.output_tokens or 0),
                }
                usage.append(usage_data)
        yield "END"
        
        await insert_one_data("chat_storage", {
            "thread_id": thread_id,
            "user_message": user_query,
            "llm_response": llm_response,
            "status": "Complete",
            "usage": usage,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

        await claude_usage_alert(datetime.utcnow().strftime("%Y-%m-%d"))

        logging.info(f"Chat response stored successfully for thread_id: {thread_id}")

    except Exception as e:
        logging.error(f"Error in claude_chat_response task: {str(e)}")
        yield json.dumps({"type": "text", "content": "API Key Error"}) + "\n\n"