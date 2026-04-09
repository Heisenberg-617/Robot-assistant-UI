from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from src.models import State
from .services.llm import LLMService
from .services.memory import MemoryService
from .services.navigation import NavigationService
from .services.rag import RAGService
from .services.stt import SpeechToTextService
from .services.tts import TTSService


class WorkflowServices:
    def __init__(self, memory_base: str = "./memories"):
        self.stt_service = SpeechToTextService()
        self.rag_service = RAGService()
        self.memory_service = MemoryService(base_path=memory_base)
        self.navigation_service = NavigationService()
        self.tts_service = TTSService()
        self.llm_service = LLMService(
            self.rag_service,
            navigation_service=self.navigation_service,
        )


class BaseWorkflow:
    def __init__(self, services: WorkflowServices, response_mode: str):
        self.services = services
        self.response_mode = response_mode
        self.memory_service = services.memory_service
        self.llm_service = services.llm_service

    def _ensure_conversation(self, conversation_id: str | None) -> None:
        if conversation_id and not self.memory_service.exists(conversation_id):
            self.memory_service.create(conversation_id)

    def _load_chat_history(self, conversation_id: str | None):
        if not conversation_id:
            return []

        chat_history = []
        stored_messages = self.memory_service.get_messages(conversation_id, limit=10)
        for message in stored_messages:
            if message["role"] == "user":
                chat_history.append(HumanMessage(content=message["text"]))
            elif message["role"] == "assistant":
                chat_history.append(AIMessage(content=message["text"]))

        return chat_history

    def _persist_response(self, conversation_id: str | None, user_query: str, response: str) -> None:
        if not conversation_id:
            return

        self.memory_service.add_message(conversation_id, "user", user_query or "")
        self.memory_service.add_message(conversation_id, "assistant", response or "")

    def _llm_step(self, state: State) -> State:
        if state.response and not state.user_query:
            return state

        query = (state.user_query or "").strip()
        if not query:
            state.response = "I did not receive a question."
            return state

        chat_history = self._load_chat_history(state.conversation_id)
        response = self.llm_service.generate(
            query=query,
            chat_history=chat_history,
            tool_inputs={"query": query},
            response_mode=self.response_mode,
        )
        state.response = response
        self._persist_response(state.conversation_id, query, response or "")
        return state

    def _history_as_dicts(self, conversation_id: str | None, fallback_response: str | None = None):
        history = []
        if conversation_id:
            for message in self.memory_service.get_messages(conversation_id):
                history.append({"role": message["role"], "content": message["text"]})

        if not history and fallback_response:
            history.append({"role": "assistant", "content": fallback_response})

        return history

    def _state_value(self, state: State | dict, key: str):
        if isinstance(state, dict):
            return state.get(key)
        return getattr(state, key, None)


class ChatWorkflow(BaseWorkflow):
    def __init__(self, services: WorkflowServices):
        super().__init__(services=services, response_mode="chat")
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        graph = StateGraph(State)
        graph.add_node("llm", self._llm_step)
        graph.add_edge(START, "llm")
        graph.add_edge("llm", END)
        return graph.compile()

    def run(self, text: str, conversation_id: str | None = None) -> State:
        self._ensure_conversation(conversation_id)
        initial_state = State(user_query=text, conversation_id=conversation_id)
        return self.workflow.invoke(initial_state)

    def run_text(self, text: str, conversation_id: str | None = None):
        final_state = self.run(text=text, conversation_id=conversation_id)
        return self._history_as_dicts(
            conversation_id,
            fallback_response=self._state_value(final_state, "response"),
        )


class AudioWorkflow(BaseWorkflow):
    def __init__(self, services: WorkflowServices):
        super().__init__(services=services, response_mode="voice")
        self.stt_service = services.stt_service
        self.tts_service = services.tts_service
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        graph = StateGraph(State)
        graph.add_node("stt", self._stt_step)
        graph.add_node("llm", self._llm_step)
        graph.add_node("tts", self._tts_step)
        graph.add_edge(START, "stt")
        graph.add_edge("stt", "llm")
        graph.add_edge("llm", "tts")
        graph.add_edge("tts", END)
        return graph.compile()

    def _stt_step(self, state: State) -> State:
        if state.audio_input:
            try:
                text = self.stt_service.transcribe(state.audio_input)
                state.transcription = text
                state.user_query = text if text else "Could not transcribe audio."
            except Exception:
                state.transcription = ""
                state.user_query = None
                state.response = "Je n’ai pas pu comprendre l’audio. Veuillez réessayer."
        return state

    def _tts_step(self, state: State) -> State:
        audio_bytes, audio_format = self.tts_service.synthesize(state.response or "")
        state.response_audio = audio_bytes
        state.response_audio_format = audio_format
        return state

    def run(self, audio: bytes | str, conversation_id: str | None = None) -> State:
        self._ensure_conversation(conversation_id)
        initial_state = State(audio_input=audio, conversation_id=conversation_id)
        return self.workflow.invoke(initial_state)


class Workflow:
    def __init__(self, memory_base: str = "./memories"):
        self.services = WorkflowServices(memory_base=memory_base)

        self.stt_service = self.services.stt_service
        self.rag_service = self.services.rag_service
        self.memory_service = self.services.memory_service
        self.navigation_service = self.services.navigation_service
        self.tts_service = self.services.tts_service
        self.llm_service = self.services.llm_service

        self.chat_workflow = ChatWorkflow(self.services)
        self.audio_workflow = AudioWorkflow(self.services)

    def run_text(self, text: str, conversation_id: str | None = None):
        return self.chat_workflow.run_text(text=text, conversation_id=conversation_id)

    def run_audio(self, audio: bytes | str, conversation_id: str | None = None) -> State:
        return self.audio_workflow.run(audio=audio, conversation_id=conversation_id)

    def run(self, audio: bytes | str, conversation_id: str | None = None) -> str:
        final_state = self.run_audio(audio=audio, conversation_id=conversation_id)
        response = self.audio_workflow._state_value(final_state, "response")
        return response or ""
