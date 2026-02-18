from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv(override=True)


class LLMService:
    def __init__(self):
        self.llm = ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0.3,
            max_retries=2,
        )

    def generate(self, query: str, documents: list, history: Optional[List[Dict]] = None) -> str:
        """
        Processes documents and optional chat history into a string and generates a response.
        `history` is a list of dicts with keys `role` and `text`.
        """
        # Extract page_content from Document objects if they aren't strings yet
        context_text = "\n\n".join(
            [doc.page_content if hasattr(doc, "page_content") else str(doc) for doc in (documents or [])]
        )

        # Build a history string to help the model remember the conversation
        history_text = "\n".join([
            f"{m.get('role')}: {m.get('text')}" for m in (history or [])
        ])

        # Include history followed by retrieved context
        full_context = "".join([
            (history_text + "\n\n") if history_text else "",
            ("Documents:\n" + context_text) if context_text else "",
        ])

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a professional assistant. Use the conversation history and the following context to answer the user's question. If the answer isn't in the context or history, say you don't know based on the documents, but offer general help if appropriate.",
            ),
            ("human", "Conversation and Context:\n{context}\n\nQuestion: {query}"),
        ])

        chain = prompt | self.llm

        response = chain.invoke({
            "context": full_context,
            "query": query,
        })

        return response.content