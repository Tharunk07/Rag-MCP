from app import app, mcp
import logging
from app.models import ChatRequest
from motor.motor_asyncio import AsyncIOMotorClient
from app.database import set_db
from config import API_PREFIX, MONGO_DB_URI, MONGO_DB, VECTOR_SEARCH_API_URL, DOCUMENT_COLLECTION, IMAGE_COLLECTION, VIDEO_COLLECTION 
from fastapi.responses import StreamingResponse
from app.tasks import claude_chat_response
import requests

_client = AsyncIOMotorClient(MONGO_DB_URI)
_db = _client[MONGO_DB]

logging.info("MongoDB connected successfully.")
set_db(_db) 

@mcp.tool(description="This tool is used to search through RAG video knowledge base.")
async def rag_search_video_kb(query: str):
    try:
        collection_name = VIDEO_COLLECTION

        logging.info(f"RAG Video KB Search Tool called with query: {query}")
        
        url = f"{VECTOR_SEARCH_API_URL}?collection_name={collection_name}&query={query}"
        
        response = requests.post(url, headers={"accept": "application/json"}, data="")
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
                    video_results = [
                        {
                            "text": item["text"],
                            "sourceURL": item["sourceURL"],
                            "start_time": item["start_time"],
                            "end_time": item["end_time"],
                            "distance": item["distance"]
                        }
                        for item in data["data"]
                        if item["sourceURL"].endswith(".mp4")
                    ]
                    return {"status": "success", "video_results": video_results}
                else:
                    logging.error("Unexpected response structure from RAG search API.")
                    return {"status": "error", "message": "Unexpected response structure from RAG search API."}
                
            except Exception as e:
                logging.error(f"Failed to parse JSON response: {str(e)}")
                return {"status": "error", "message": "Failed to parse JSON response."}
        else:
            logging.error(f"RAG search API returned an error: {response.status_code} - {response.text}")
            return {"status": "error", "message": f"RAG search API error: {response.status_code}"}
        
    except Exception as e: 
        logging.error(f"Error in RAG video KB search tool: {str(e)}")
        return {"status": "error", "message": str(e)}
   
    
@mcp.tool(description="This tool is used to search through RAG document knowledge base.")
async def rag_search_document_kb(query: str):
    try:
        collection_name = DOCUMENT_COLLECTION

        logging.info(f"RAG Document KB Search Tool called with query: {query}")
        
        url = f"{VECTOR_SEARCH_API_URL}?collection_name={collection_name}&query={query}"
        
        response = requests.post(url, headers={"accept": "application/json"}, data="")
        
        if response.status_code == 200:
            try:
                # Ensure the response is parsed as JSON
                response_data = response.json()
                
                # Check if the response contains the expected "data" key
                if "data" in response_data and isinstance(response_data["data"], list):
                    document_results = [
                        {
                            "text": item["text"],
                            "sourceURL": item["sourceURL"],
                            "distance": item["distance"]
                        }
                        for item in response_data["data"]
                        if not item["sourceURL"].endswith(".mp4")
                    ]
                    return {"status": "success", "document_results": document_results}
                else:
                    logging.error("Unexpected response structure from RAG search API.")
                    return {"status": "error", "message": "Unexpected response structure from RAG search API."}
            except Exception as e:
                logging.error(f"Failed to parse JSON response: {str(e)}")
                return {"status": "error", "message": "Failed to parse JSON response."}
        else:
            logging.error(f"RAG search API returned an error: {response.status_code} - {response.text}")
            return {"status": "error", "message": f"RAG search API error: {response.status_code}"}
        
    except Exception as e: 
        logging.error(f"Error in RAG document KB search tool: {str(e)}")
        return {"status": "error", "message": str(e)}
    

@mcp.tool(description="This tool is used to search through RAG image knowledge base.")
async def rag_search_image_kb(query: str):
    try:
        collection_name = IMAGE_COLLECTION

        logging.info(f"RAG Image KB Search Tool called with query: {query}")
        
        url = f"{VECTOR_SEARCH_API_URL}?collection_name={collection_name}&query={query}"
        
        response = requests.post(url, headers={"accept": "application/json"}, data="")
        
        if response.status_code == 200:
            try:
                # Ensure the response is parsed as JSON
                response_data = response.json()
                
                # Check if the response contains the expected "data" key
                if isinstance(response_data, dict) and "data" in response_data and isinstance(response_data["data"], list):
                    image_results = [
                        {
                            "text": item["text"],
                            "sourceURL": item["sourceURL"],
                            "distance": item["distance"]
                        }
                        for item in response_data["data"]
                    ]
                    return {"status": "success", "image_results": image_results}
                else:
                    logging.error("Unexpected response structure from RAG search API.")
                    return {"status": "error", "message": "Unexpected response structure from RAG search API."}
            except Exception as e:
                logging.error(f"Failed to parse JSON response: {str(e)}")
                return {"status": "error", "message": "Failed to parse JSON response."}
        else:
            logging.error(f"RAG search API returned an error: {response.status_code} - {response.text}")
            return {"status": "error", "message": f"RAG search API error: {response.status_code}"}
        
    except Exception as e: 
        logging.error(f"Error in RAG image KB search tool: {str(e)}")
        return {"status": "error", "message": str(e)}
    

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