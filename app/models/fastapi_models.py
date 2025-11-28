from typing import List, Dict
from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str
    tools_enabled: List[str] = []
    is_new_thread: bool = True
    thread_id: str = ""