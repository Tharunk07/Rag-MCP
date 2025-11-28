import anthropic
from config import CLAUDE_API_KEY, GCHAT_WEBHOOK_URL
from datetime import datetime
import logging
import aiohttp

client = anthropic.AsyncAnthropic(api_key=CLAUDE_API_KEY)


CLAUDE_RESPONSE_PROMPT = "You are Assistant, useful for answering user queries in a helpful and informative manner. Provide detailed and accurate responses based on the information available to you. If you do not know the answer, admit it honestly rather than attempting to fabricate a response. Always prioritize user safety and adhere to ethical guidelines in your interactions."


def format_chat_history_as_dicts(chat_data):
    """
    Format completed chat records into a list of dictionaries for LLM input.

    Args:
        chat_data (list[dict]): List of chat entries containing "status", "user_message", and "llm_response".

    Returns:
        list[dict]: Conversation history formatted as dictionaries with "role" ("user" or "assistant")
                    and "content". Curly braces in messages are escaped for template safety.
    """

    chat_history = []
    for chat in chat_data:
        if chat["status"] == "Complete":
            user_message = chat["user_message"].replace("{", "{{{{").replace("}", "}}}}")
            chat_history.append({"role": "user", "content": user_message})
            
            ai_response = chat["llm_response"].replace("{", "{{{{").replace("}", "}}}}")
            if not ai_response or ai_response.strip() == "":
                ai_response = "agent failed to respond"
            chat_history.append({"role": "assistant", "content": ai_response})
    return chat_history



async def mcp_chat_response_generation(history, custom_mcp_tools):

    # mcp = []

    # mcp.append({
    #     "type":"url",
    #     "url": "",
    #     "name": ""
    # })
    
    try:
        now = datetime.now()

        async with client.beta.messages.stream(
            model="claude-3-5-haiku-20241022",
            max_tokens=4096,
            messages=history,
            system=CLAUDE_RESPONSE_PROMPT,
            # mcp_servers=mcp,
            betas=["mcp-client-2025-04-04"],
            temperature=0,
            thinking={"type": "disabled"}
        ) as stream:
            async for event in stream:
                yield event

    except anthropic.APIStatusError as e:
        error_message = f"Anthropic API Error: {e.response.json()['error']['message']}" if e.response.status_code == 400 else f"Anthropic API Error: {str(e)}"
        logging.error(error_message)
        raise

    except Exception as e:
        error_message = f"Unexpected error in Claude call: {str(e)}"
        logging.exception(error_message)
        raise

async def send_google_chat_alert(message: str):
    """Send an alert to Google Chat asynchronously when an error occurs."""
    headers = {"Content-Type": "application/json"}
    payload = {"text": message}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(GCHAT_WEBHOOK_URL, headers=headers, json=payload) as response:
                if response.status != 200:
                    resp_text = await response.text()
                    logging.info(f"Failed to send Google Chat alert: {response.status} - {resp_text}")
    except Exception as e:
        logging.info(f"Error sending Google Chat alert: {e}")