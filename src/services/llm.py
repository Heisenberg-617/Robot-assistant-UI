from typing import Optional, List, Union
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.documents import Document
from pydantic import BaseModel, Field

from src.services.rag import RAGService
from src.services.navigation import NavigationService

load_dotenv(override=True)

class RetrievalInput(BaseModel):
    query: str = Field(description="User query to search in the knowledge base")
class CoordonatesOutput(BaseModel):
    latitude: float = Field(description="Latitude for navigation")
    longitude: float = Field(description="Longitude for navigation")
class LocationInput(BaseModel):
    location_name: str = Field(description="Name of the place the user wants to go to")

class LLMService:
    def __init__(self, rag_service: RAGService):
        # Initialize RAG service
        self.rag = rag_service

        # Groq model
        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0.3,
            max_retries=3,
        )

        # RAG search as a tool
        @tool("document_retriever", args_schema=RetrievalInput)
        def retrieval_tool(query: str) -> str:
            """
            Search the internal knowledge base for relevant documents.
            Use this when answering questions about EMINES school programs, UM6P or any related information.
            """

            docs = self.rag.search(query, k=3)

            if not docs:
                return "No relevant documents found."

            return "\n\n".join(
                [f"{doc.page_content}" for doc in docs]
            )
    
        @tool("navigation_tool", args_schema=LocationInput)
        def navigation_tool(location_name: str) -> CoordonatesOutput:
            """
            Connect to ROS API and send coordinates of the user-requested location.
            Uses fuzzy matching to handle variations in naming.
            """
            nav_service = NavigationService()
            latitude, longitude = nav_service.get_coordinates(location_name)

            # Placeholder for sending to the ROS API
            # ros_api.send_coordinates(latitude=latitude, longitude=longitude)

            return CoordonatesOutput(latitude=latitude, longitude=longitude)


        tools = [retrieval_tool, navigation_tool]

        # Agent prompt
        system_prompt = """
                        You are a professional AI assistant for the EMINES school.

                        You have access to a RAG tool called `document_retriever` to use whenever a user asks about:
                        - EMINES programs
                        - UM6P
                        - school information
                        - admissions
                        - academic details

                        Always base your answers on retrieved documents when possible.
                        If the information cannot be found, clearly say so.
                        Do not say I don't know something, unless it was specifically asked by the user. In that case, you can say "I don't have that information".

                        If the user asks for directions to a location on campus, use the `navigation_tool` to send coordinates to the robot to trigger the navigation.
                        If the tool return None, none or an error, it means the location was not found. In that case, inform the user that you couldn't find the location and ask them to rephrase or provide a different location. And suggest some valid locations as "Student lounge, cafeteria, administration, Reception or health center."
                        When using the navigation tool, only provide the name of the location as input, and do not include any additional text in the input. For example, if the user says "How can I get to the library?", you should call `navigation_tool(location_name="library")` without any additional text.
                        The output of the navigation tool will be coordinates, but you should not mention these coordinates in your response to the user. Instead, you can say something like "I have sent the directions to the robot" or "Heading towards the location <location_name>" after invoking the navigation tool.
                        """
        self.agent = create_agent(self.llm, tools=tools, system_prompt=system_prompt)

    def _normalize_history(self, chat_history: Optional[List[Union[BaseMessage, dict]]]) -> List[dict]:
        """Return a list of messages as dictionaries with {'role','content'}"""
        out = []
        if not chat_history:
            return out
        for m in chat_history:
            # Accept LangChain message objects
            if hasattr(m, "type") and hasattr(m, "content"):
                # LangChain vX message object
                role = "user" if m.type == "human" else "assistant" if m.type == "ai" else getattr(m, "role", None)
                if role is None:
                    # fallback based on class name
                    role = "user" if m.__class__.__name__.lower().startswith("human") else "assistant"
                out.append({"role": role, "content": m.content})
            elif hasattr(m, "role") and hasattr(m, "content"):
                out.append({"role": m.role, "content": m.content})
            elif isinstance(m, dict) and "role" in m and "content" in m:
                out.append({"role": m["role"], "content": m["content"]})
            else:
                # Best effort: stringify
                out.append({"role": "user", "content": str(m)})
        return out

    def generate(self, query: str, chat_history: Optional[List[Union[BaseMessage, dict]]] = None, tool_inputs: Optional[dict] = None) -> str:
        """
        Generate a textual response from the agent.

        - chat_history: optional list of LangChain message objects (HumanMessage/AIMessage) or dicts
        - tool_inputs: optional dict passed to the agent when invoking tools
        """
        # Normalize chat history into role/content dicts
        messages = self._normalize_history(chat_history)

        # Append current user message
        messages.append({"role": "user", "content": query})

        invoke_payload = {"messages": messages}
        if tool_inputs:
            invoke_payload["tool_inputs"] = tool_inputs

        # The agent.invoke call can return different shapes depending on the langchain version.
        resp = self.agent.invoke(invoke_payload)

        # Try to extract text from response in a few common shapes
        result_text = ""
        try:
            # If resp is a dict containing 'messages' (list)
            if isinstance(resp, dict) and "messages" in resp and resp["messages"]:
                last = resp["messages"][-1]
                # last might be object or dict
                if hasattr(last, "content"):
                    result_text = last.content
                elif isinstance(last, dict) and "content" in last:
                    result_text = last["content"]
                else:
                    result_text = str(last)
            elif hasattr(resp, "content"):
                # maybe a single BaseMessage-like
                result_text = resp.content
            else:
                # fallback to stringifying response
                result_text = str(resp)
        except Exception:
            result_text = str(resp)

        # Ensure we return a plain string
        return result_text
