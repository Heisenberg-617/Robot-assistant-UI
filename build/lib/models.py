# models.py
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class State:
    audio_input: Optional[bytes] = None   # raw audio
    user_query: Optional[str] = None       # transcribed text
    retrieved_docs: Optional[List[str]] = None
    response: Optional[str] = None
    conversation_id: Optional[str] = None
