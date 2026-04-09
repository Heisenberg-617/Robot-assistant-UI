from typing import List, Optional, Union

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from src.services.navigation import NavigationService
from src.services.rag import RAGService

load_dotenv(override=True)


class RetrievalInput(BaseModel):
    query: str = Field(description="User query to search in the knowledge base")


class ResolvedLocationOutput(BaseModel):
    location_name: str = Field(description="Canonical location name")
    category: str = Field(description="Destination category")
    description: str = Field(description="Short description of the destination")
    latitude: float = Field(description="Latitude for navigation")
    longitude: float = Field(description="Longitude for navigation")


class LocationInput(BaseModel):
    location_name: str = Field(description="Name of the place the user wants to go to")


class LLMService:
    def __init__(self, rag_service: RAGService, navigation_service: Optional[NavigationService] = None):
        self.rag = rag_service
        self.navigation_service = navigation_service or NavigationService()

        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_retries=2,
        )

        @tool("document_retriever", args_schema=RetrievalInput)
        def retrieval_tool(query: str) -> str:
            """
            Search the internal knowledge base for relevant documents.
            Use this when answering questions about EMINES school programs, UM6P, or related information.
            """

            docs = self.rag.search(query, k=3)
            if not docs:
                return "No relevant documents found."

            return "\n\n".join(doc.page_content for doc in docs)

        @tool("navigation_tool", args_schema=LocationInput)
        def navigation_tool(location_name: str):
            """
            Resolve the best campus destination for a user request.
            Use this when the user wants to reach a place on campus.
            """

            location = self.navigation_service.prepare_navigation(location_name)
            if not location:
                return "LOCATION_NOT_FOUND"

            return ResolvedLocationOutput(
                location_name=location["location_name"],
                category=location["category"],
                description=location["description"],
                latitude=location["latitude"],
                longitude=location["longitude"],
            )

        tools = [retrieval_tool, navigation_tool]

        base_prompt = """
            You are a professional AI assistant integrated on a navigation robot for the EMINES school.
            Your main tasks are to provide information about the school and its programs, and to assist users in navigating the campus.
            You are friendly, direct, and practical.
            You have to answer in the SAME language as the user's latest message!

            You have access to a RAG tool called `document_retriever` ONLY to be used when the user asks specific factual questions about:
            - EMINES programs
            - UM6P
            - school information
            - admissions
            - academic details
            DO NOT use the tool for greetings, simple chitchat, or standard navigation requests.
            If the information cannot be found, clearly say so.

            If the user asks for directions to a location on campus, use the `navigation_tool` to resolve the best destination.
            The navigation tool can resolve close matches and aliases, so still use it when the user gives an approximate name, synonym, or common alias.
            If the tool returns LOCATION_NOT_FOUND, explain that you could not find the destination and suggest valid options such as Accueil, Administration, Cafétéria, Centre de santé, or Salon Étudiant.
            When using the navigation tool, only provide the place name as input with no extra text.
            Never expose coordinates to the user.
            If a destination is found, tell the user to follow you to the destination and do not describing the route. Do not give coordinates or detailed directions.
        """

        chat_prompt = """
            You are replying in a chat widget.
            Keep answers informative and helpful, but you can be more detailed and use markdown formatting when appropriate.
        """

        voice_prompt = """
            You are speaking through the robot's audio output.
            Keep answers short, natural, and easy to read aloud.
            Prefer one to two short sentences.
            Avoid markdown, long lists, and dense explanations unless the user explicitly asks for detail.
        """

        self.agents = {
            "chat": create_agent(self.llm, tools=tools, system_prompt=f"{base_prompt}\n{chat_prompt}"),
            "voice": create_agent(self.llm, tools=tools, system_prompt=f"{base_prompt}\n{voice_prompt}"),
        }

    def _normalize_history(self, chat_history: Optional[List[Union[BaseMessage, dict]]]) -> List[dict]:
        out = []
        if not chat_history:
            return out

        for message in chat_history:
            if hasattr(message, "type") and hasattr(message, "content"):
                role = "user" if message.type == "human" else "assistant" if message.type == "ai" else getattr(message, "role", None)
                if role is None:
                    role = "user" if message.__class__.__name__.lower().startswith("human") else "assistant"
                out.append({"role": role, "content": message.content})
            elif hasattr(message, "role") and hasattr(message, "content"):
                out.append({"role": message.role, "content": message.content})
            elif isinstance(message, dict) and "role" in message and "content" in message:
                out.append({"role": message["role"], "content": message["content"]})
            else:
                out.append({"role": "user", "content": str(message)})

        return out

    def generate(
        self,
        query: str,
        chat_history: Optional[List[Union[BaseMessage, dict]]] = None,
        tool_inputs: Optional[dict] = None,
        response_mode: str = "chat",
    ) -> str:
        messages = self._normalize_history(chat_history)
        desired_language = self._detect_language(query)
        messages.append(
            {
                "role": "system",
                "content": "Reply in English only." if desired_language == "en" else "Répondez en français uniquement.",
            }
        )
        messages.append({"role": "user", "content": query})

        invoke_payload = {"messages": messages}
        if tool_inputs:
            invoke_payload["tool_inputs"] = tool_inputs

        agent = self.agents.get(response_mode, self.agents["chat"])
        resp = agent.invoke(invoke_payload)

        result_text = ""
        try:
            if isinstance(resp, dict) and "messages" in resp and resp["messages"]:
                last = resp["messages"][-1]
                if hasattr(last, "content"):
                    result_text = last.content
                elif isinstance(last, dict) and "content" in last:
                    result_text = last["content"]
                else:
                    result_text = str(last)
            elif hasattr(resp, "content"):
                result_text = resp.content
            else:
                result_text = str(resp)
        except Exception:
            result_text = str(resp)

        return result_text