from langgraph.graph import StateGraph, START, END
from src.models import State
from .services.stt import SpeechToTextService
from .services.rag import RAGService
from .services.llm import LLMService
from .services.memory import MemoryService
import uuid


class Workflow:

    def __init__(self, memory_base: str = "./memories"):
        self.stt_service = SpeechToTextService()
        self.rag_service = RAGService()
        self.llm_service = LLMService()
        self.sidekick_id = str(uuid.uuid4())
        self.memory_service = MemoryService(base_path=memory_base)
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        graph = StateGraph(State)

        graph.add_node("stt", self._stt_step)
        graph.add_node("rag", self._rag_step)
        graph.add_node("llm", self._llm_step)

        graph.add_edge(START, "stt")
        graph.add_edge("stt", "rag")
        graph.add_edge("rag", "llm")
        graph.add_edge("llm", END)

        return graph.compile()

    def _stt_step(self, state: State) -> State:
        text = self.stt_service.transcribe(state.audio_input)
        state.user_query = text if text else "Could not transcribe audio."
        return state

    def _rag_step(self, state: State) -> State:
        if not state.user_query:
            state.retrieved_docs = ["No query provided, so no documents retrieved."]
            return state
        docs = self.rag_service.search(state.user_query, k=3)
        state.retrieved_docs = docs
        return state

    def _llm_step(self, state: State) -> State:
        print("--- GENERATING RESPONSE ---")
        # state must have a conversation_id attribute set by run()
        conv_id = getattr(state, "conversation_id", None)

        history = None
        if conv_id:
            # include last N messages, e.g., 10
            history = self.memory_service.get_messages(conv_id, limit=10)

        response = self.llm_service.generate(
            query=state.user_query,
            documents=state.retrieved_docs,
            history=history,
        )
        state.response = response

        # persist to memory if conversation id provided
        if conv_id:
            self.memory_service.add_message(conv_id, "user", state.user_query or "")
            self.memory_service.add_message(conv_id, "assistant", response or "")

        return state

    def run_text(self, text: str, conversation_id: str = None) -> str:
        """Run the workflow for a plain text query (bypasses STT).

        This is useful for local testing and for the Gradio UI so we don't
        require AssemblyAI audio transcription.
        """
        state = State(user_query=text, conversation_id=conversation_id)
        if conversation_id:
            self.memory_service.create(conversation_id)

        # RAG -> LLM sequence
        state = self._rag_step(state)
        state = self._llm_step(state)
        return state.response

    def run(self, audio: bytes, conversation_id: str = None) -> str:
        initial_state = State(audio_input=audio)
        if conversation_id:
            # ensure memory exists for this superrun
            self.memory_service.create(conversation_id)
            setattr(initial_state, "conversation_id", conversation_id)

        # Invoke workflow (langgraph StateGraph compiled without a checkpointer here)
        final_state = self.workflow.invoke(initial_state)
        return final_state.response