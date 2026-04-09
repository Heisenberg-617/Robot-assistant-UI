import re
import uuid
from datetime import datetime

import streamlit as st

from src.components.voice_assistant import voice_assistant_orb
from src.components.voice_bridge import VoiceBridgeServer
from src.workflow import Workflow


st.set_page_config(
    page_title="Navigateur Robot Universitaire",
    page_icon="🧭",
    layout="wide",
)


DEFAULT_ASSISTANT_GREETING = (
    "Bonjour, je suis le robot d'accueil. Comment puis-je vous aider ? "
    "Où voulez-vous aller ou que souhaitez-vous savoir ?"
)

CATEGORY_STYLES = {
    "Administratif": ("#f3e8ff", "#7c3aed"),
    "Santé": ("#dcfce7", "#15803d"),
    "Laboratoire": ("#dbeafe", "#2563eb"),
    "Alimentation": ("#fef3c7", "#b45309"),
    "Média": ("#fee2e2", "#dc2626"),
    "Détente": ("#e0f2fe", "#0369a1"),
    "Clubs": ("#ede9fe", "#6d28d9"),
    "Services": ("#cffafe", "#0f766e"),
    "Autre": ("#e2e8f0", "#334155"),
}


CATEGORY_ICONS = {
    "administratif": "&#128188;",
    "santÃ©": "&#127973;",
    "laboratoire": "&#129514;",
    "alimentation": "&#127860;",
    "mÃ©dia": "&#127897;",
    "dÃ©tente": "&#127918;",
    "clubs": "&#128101;",
    "services": "&#128295;",
    "autre": "&#128205;",
}


CATEGORY_PALETTE = {
    "administratif": ("#f3e8ff", "#7c3aed"),
    "sante": ("#dcfce7", "#15803d"),
    "laboratoire": ("#dbeafe", "#2563eb"),
    "alimentation": ("#fef3c7", "#b45309"),
    "media": ("#fee2e2", "#dc2626"),
    "detente": ("#e0f2fe", "#0369a1"),
    "clubs": ("#ede9fe", "#6d28d9"),
    "services": ("#cffafe", "#0f766e"),
    "autre": ("#e2e8f0", "#334155"),
}


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top center, rgba(255, 255, 255, 0.62), transparent 28%),
                linear-gradient(180deg, #dfe8fb 0%, #dfe7f7 100%);
        }

        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 8rem;
            max-width: 1640px;
        }

        .hero-wrap {
            text-align: center;
            padding: 0.25rem 0 1.35rem 0;
        }

        .hero-title {
            color: #0f172a;
            font-size: 2.95rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin: 0;
        }

        .hero-subtitle {
            color: #475569;
            font-size: 1.08rem;
            margin-top: 0.75rem;
        }

        .hero-icon {
            color: #2563eb;
            margin-right: 0.55rem;
        }

        .st-key-search_panel,
        .st-key-destination_panel,
        .st-key-status_panel,
        .st-key-selected_panel,
        .st-key-floating_chat_panel,
        .st-key-floating_voice_panel,
        .st-key-chat_widget_panel,
        .st-key-voice_widget_panel,
        .st-key-assistant_dock {
            background: rgba(255, 255, 255, 0.98);
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 24px;
            box-shadow:
                0 16px 30px rgba(15, 23, 42, 0.05),
                0 3px 10px rgba(15, 23, 42, 0.03);
        }

        .st-key-search_panel,
        .st-key-destination_panel,
        .st-key-status_panel,
        .st-key-selected_panel {
            padding: 1.15rem 1.2rem 2rem 1.2rem;
        }

        .section-title {
            color: #0f172a;
            font-size: 1.08rem;
            font-weight: 800;
            margin-bottom: 0.15rem;
        }

        .section-subtitle {
            color: #64748b;
            font-size: 0.96rem;
            margin-bottom: 0.9rem;
        }

        .search-title-row {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            margin-bottom: 0.9rem;
            color: #0f172a;
            font-size: 1.08rem;
            font-weight: 800;
        }

        .status-grid {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 0.95rem 0.8rem;
            align-items: center;
        }

        .status-label {
            color: #475569;
            font-size: 0.98rem;
        }

        .status-value {
            color: #0f172a;
            font-size: 1.02rem;
            font-weight: 700;
            text-align: right;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            padding: 0.18rem 0.68rem;
            font-size: 0.88rem;
            font-weight: 700;
            background: #f8fafc;
            color: #0f172a;
            border: 1px solid #e2e8f0;
        }

        [class*="st-key-destination_card_"] {
            border: 1px solid #e2e8f0;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.98);
            padding: 1rem 1rem 0.95rem 1rem;
            transition: background 160ms ease, border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
        }

        [class*="st-key-destination_card_"]:hover {
            background: #f8fafc;
            border-color: #cbd5e1;
            box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
            transform: translateY(-1px);
        }

        [class*="st-key-destination_card_selected_"] {
            border: 2px solid #2563eb;
            background: #f8fbff;
            box-shadow: 0 14px 26px rgba(37, 99, 235, 0.10);
        }

        .destination-title-row {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 0.9rem;
            margin-bottom: 0.5rem;
        }

        .destination-name-row {
            display: inline-flex;
            align-items: center;
            gap: 0.55rem;
            min-width: 0;
        }

        .destination-name-icon {
            width: 2rem;
            height: 2rem;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #eff6ff;
            color: #2563eb;
            font-size: 1rem;
            flex-shrink: 0;
        }

        .destination-name {
            color: #0f172a;
            font-size: 1.02rem;
            font-weight: 800;
            line-height: 1.35;
        }

        .destination-description {
            color: #64748b;
            font-size: 0.93rem;
            line-height: 1.5;
            margin-bottom: 0.75rem;
            min-height: 2.8rem;
        }

        .destination-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-bottom: 0.85rem;
        }

        .meta-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            border-radius: 999px;
            padding: 0.22rem 0.62rem;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            color: #475569;
            font-size: 0.84rem;
            font-weight: 700;
        }

        .meta-chip.accessible {
            background: #f0fdf4;
            color: #16a34a;
            border-color: #bbf7d0;
        }

        .category-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.28rem 0.72rem;
            font-size: 0.82rem;
            font-weight: 800;
            white-space: nowrap;
        }

        [class*="st-key-destination_card_"] button {
            min-height: 2.75rem;
            border-radius: 14px;
            font-weight: 700;
            border: 1px solid #dbe4f0;
            background: #ffffff;
            color: #0f172a;
        }

        [class*="st-key-destination_card_"] button:hover {
            border-color: #94a3b8;
            background: #f8fafc;
        }

        .empty-state {
            border: 1px dashed rgba(148, 163, 184, 0.35);
            border-radius: 18px;
            padding: 1rem;
            color: #64748b;
            background: rgba(248, 250, 252, 0.84);
        }

        .selected-destination {
            color: #0f172a;
            font-size: 1.28rem;
            font-weight: 800;
            margin-bottom: 0.55rem;
        }

        .selected-description {
            color: #475569;
            font-size: 0.98rem;
            line-height: 1.65;
            margin-bottom: 1rem;
        }

        .selected-details {
            display: grid;
            gap: 0.85rem;
            padding: 0.2rem 0 1rem 0;
            border-bottom: 1px solid #e2e8f0;
            margin-bottom: 1rem;
        }

        .selected-detail {
            display: flex;
            align-items: center;
            gap: 0.7rem;
            color: #334155;
            font-size: 0.98rem;
        }

        .selected-detail-icon {
            width: 1.5rem;
            text-align: center;
            color: #64748b;
        }

        .selected-detail.accessible {
            color: #16a34a;
            font-weight: 700;
        }

        .st-key-nav_action_button button {
            min-height: 3.25rem;
            border-radius: 16px;
            background: #0f172a;
            color: #ffffff;
            border: 1px solid #0f172a;
            font-size: 0.98rem;
            font-weight: 800;
        }

        .st-key-nav_action_button button:hover {
            background: #020617;
            border-color: #020617;
            color: #ffffff;
        }

        .assist-copy {
            color: #0f172a;
            font-size: 0.96rem;
            font-weight: 800;
            margin-bottom: 0.32rem;
        }

        .assist-subcopy {
            color: #64748b;
            font-size: 0.85rem;
            margin-bottom: 0.78rem;
            line-height: 1.5;
        }

        .typing {
            display: inline-flex;
            gap: 0.22rem;
            align-items: center;
            padding: 0.25rem 0.1rem;
        }

        .typing span {
            width: 7px;
            height: 7px;
            border-radius: 999px;
            background: #94a3b8;
            display: inline-block;
            animation: blink 1.1s infinite ease-in-out;
        }

        .typing span:nth-child(2) { animation-delay: 0.15s; }
        .typing span:nth-child(3) { animation-delay: 0.30s; }

        @keyframes blink {
            0%, 80%, 100% { opacity: 0.28; transform: translateY(0); }
            40% { opacity: 1; transform: translateY(-1px); }
        }

        .st-key-assistant_dock {
            position: fixed;
            right: 1.3rem;
            bottom: 1.1rem;
            width: 19rem;
            z-index: 999;
            padding: 0.95rem;
            box-shadow: 0 24px 52px rgba(15, 23, 42, 0.16);
        }

        .st-key-assistant_dock button {
            min-height: 3rem;
            border-radius: 999px;
            font-size: 0.98rem;
            font-weight: 800;
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            border: 1px solid rgba(148, 163, 184, 0.22);
            color: #0f172a;
        }

        .st-key-assistant_dock button:hover {
            border-color: rgba(37, 99, 235, 0.35);
            color: #2563eb;
        }

        .st-key-floating_chat_panel,
        .st-key-floating_voice_panel {
            position: fixed;
            right: 1.1rem;
            bottom: -0.2rem;
            width: min(28.5rem, calc(100vw - 1rem));
            z-index: 998;
            padding: 1rem 1rem 1.1rem 1rem;
            border-bottom-left-radius: 0;
            border-bottom-right-radius: 0;
            box-shadow: 0 28px 62px rgba(15, 23, 42, 0.22);
        }

        .st-key-chat_widget_panel,
        .st-key-voice_widget_panel {
            background: transparent;
            border: none;
            box-shadow: none;
            padding: 0;
        }

        .widget-header-title {
            color: #0f172a;
            font-size: 1.06rem;
            font-weight: 800;
            padding-top: 0.1rem;
        }

        [class*="st-key-widget_icon_button_"] button {
            min-height: 2.6rem;
            width: 2.6rem;
            border-radius: 50%;
            padding: 0;
            background: linear-gradient(135deg, #ffffff, #f0f4ff);
            color: #1e293b;
            border: none;
            font-weight: 700;
            font-size: 1.1rem;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
            transition: all 0.2s ease-in-out;
        }

        [class*="st-key-widget_icon_button_"] button:hover {
            background: linear-gradient(135deg, #dbeafe, #93c5fd);
            color: #1e40af;
            transform: scale(1.1);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .voice-panel-note {
            color: #64748b;
            font-size: 0.92rem;
            text-align: center;
            margin-top: 0rem;
            margin-bottom: 1.5rem;
        }

        @media (max-width: 960px) {
            .hero-title {
                font-size: 2rem;
            }

            .st-key-assistant_dock,
            .st-key-floating_chat_panel,
            .st-key-floating_voice_panel {
                width: calc(100vw - 1rem);
                right: 0.5rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_assistant() -> Workflow:
    if "_assistant" not in st.session_state:
        st.session_state._assistant = Workflow()
    return st.session_state._assistant


def get_voice_bridge() -> VoiceBridgeServer:
    if "_voice_bridge" not in st.session_state:
        st.session_state._voice_bridge = VoiceBridgeServer()
    return st.session_state._voice_bridge


def init_session_state(assistant: Workflow) -> None:
    if "chat_conversation_id" not in st.session_state:
        st.session_state.chat_conversation_id = str(uuid.uuid4())
        assistant.memory_service.create(st.session_state.chat_conversation_id)

    if "audio_conversation_id" not in st.session_state:
        st.session_state.audio_conversation_id = str(uuid.uuid4())
        assistant.memory_service.create(st.session_state.audio_conversation_id)

    st.session_state.setdefault("selected_destination", None)
    st.session_state.setdefault("robot_status", "Prêt")
    st.session_state.setdefault("last_navigation_command", None)
    st.session_state.setdefault("last_voice_error", None)
    st.session_state.setdefault("last_voice_response", "")
    st.session_state.setdefault("last_voice_transcription", "")
    st.session_state.setdefault("last_voice_event_nonce", None)
    st.session_state.setdefault("last_playback_nonce", None)
    st.session_state.setdefault("chat_panel_open", False)
    st.session_state.setdefault("voice_panel_open", False)
    st.session_state.setdefault("pending_chat_prompt", None)
    st.session_state.setdefault("chat_processing", False)
    st.session_state.setdefault("voice_reset_token", str(uuid.uuid4()))


def state_value(result, key: str, default=None):
    if isinstance(result, dict):
        return result.get(key, default)
    return getattr(result, key, default)


def load_history(assistant: Workflow, conversation_id: str) -> list[dict]:
    return [
        {"role": message["role"], "content": message["text"]}
        for message in assistant.memory_service.get_messages(conversation_id)
    ]


def new_chat_conversation(assistant: Workflow) -> None:
    st.session_state.chat_conversation_id = str(uuid.uuid4())
    assistant.memory_service.create(st.session_state.chat_conversation_id)
    st.session_state.pending_chat_prompt = None
    st.session_state.chat_processing = False


def new_audio_conversation(assistant: Workflow) -> None:
    st.session_state.audio_conversation_id = str(uuid.uuid4())
    assistant.memory_service.create(st.session_state.audio_conversation_id)
    st.session_state.last_voice_error = None
    st.session_state.last_voice_response = ""
    st.session_state.last_voice_transcription = ""
    st.session_state.last_voice_event_nonce = None
    st.session_state.last_playback_nonce = None
    st.session_state.voice_reset_token = str(uuid.uuid4())
    st.session_state.robot_status = "Prêt"


def open_chat_panel() -> None:
    st.session_state.chat_panel_open = True
    st.session_state.voice_panel_open = False


def open_voice_panel() -> None:
    st.session_state.voice_panel_open = True
    st.session_state.chat_panel_open = False


def close_chat_panel() -> None:
    st.session_state.chat_panel_open = False


def close_voice_panel() -> None:
    st.session_state.voice_panel_open = False


def select_destination(location_name: str) -> None:
    st.session_state.selected_destination = location_name
    st.session_state.robot_status = "Destination sélectionnée"


def get_destination_details(assistant: Workflow, location_name: str | None):
    if not location_name:
        return None

    for location in assistant.navigation_service.list_locations():
        if location.location_name == location_name:
            return location

    return assistant.navigation_service.resolve_location(location_name)


def format_timestamp(timestamp: str | None) -> str:
    if not timestamp:
        return "Heure inconnue"
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return timestamp


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def short_description(text: str, limit: int = 82) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[: limit - 1].rstrip()}…"


def category_badge(category: str) -> str:
    key = normalize_category_key(category)
    background, foreground = CATEGORY_PALETTE.get(key, ("#e2e8f0", "#334155"))
    return (
        f'<span class="category-pill" style="background:{background};color:{foreground};">'
        f"{category}</span>"
    )


def normalize_category_key(category: str) -> str:
    value = (category or "").strip().lower()
    if "admin" in value:
        return "administratif"
    if "labor" in value:
        return "laboratoire"
    if "aliment" in value or "caf" in value or "food" in value:
        return "alimentation"
    if "club" in value:
        return "clubs"
    if "service" in value:
        return "services"
    if "sant" in value or "health" in value or "med" in value:
        return "sante"
    if "dia" in value or "media" in value:
        return "media"
    if "tent" in value or "lounge" in value or "relax" in value:
        return "detente"
    return "autre"


def category_icon(category: str) -> str:
    key = normalize_category_key(category)
    icon = {
        "administratif": "&#128188;",
        "sante": "&#127973;",
        "laboratoire": "&#129514;",
        "alimentation": "&#127860;",
        "media": "&#127897;",
        "detente": "&#127918;",
        "clubs": "&#128101;",
        "services": "&#128295;",
        "autre": "&#128205;",
    }.get(key, "&#128205;")
    return f'<span class="destination-name-icon" aria-hidden="true">{icon}</span>'


def build_destination_meta(location) -> str:
    chips = []
    if location.building:
        chips.append(f'<span class="meta-chip">🏢 {location.building}</span>')
    if location.floor:
        chips.append(f'<span class="meta-chip">📍 {location.floor}</span>')
    if location.accessible:
        chips.append('<span class="meta-chip accessible">♿ Accessible</span>')
    return "".join(chips)


def render_header() -> None:
    st.markdown(
        """
        <div class="hero-wrap">
            <h1 class="hero-title"><span class="hero-icon">➤</span>Navigateur Robot Universitaire</h1>
            <div class="hero-subtitle">Sélectionnez une destination et notre robot intelligent vous y guidera</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_search_panel(assistant: Workflow):
    categories = ["Toutes les catégories", *assistant.navigation_service.get_categories()[1:]]

    with st.container(key="search_panel"):
        st.markdown(
            '<div class="search-title-row"><span>🔎</span><span>Trouvez votre destination</span></div>',
            unsafe_allow_html=True,
        )

        cols = st.columns([5.1, 1.45], gap="medium")
        with cols[0]:
            query = st.text_input(
                "Recherche",
                placeholder="Rechercher par mot-clé dans le titre…",
                label_visibility="collapsed",
            )
        with cols[1]:
            category = st.selectbox(
                "Catégorie",
                categories,
                index=0,
                label_visibility="collapsed",
            )
    return query, category


def render_destination_card(location, is_selected: bool) -> None:
    slug = slugify(location.location_name)
    key_prefix = f"destination_card_selected_{slug}" if is_selected else f"destination_card_{slug}"

    with st.container(key=key_prefix):
        st.markdown(
            f"""
            <div class="destination-title-row">
                <div class="destination-name-row">
                    {category_icon(location.category)}
                    <div class="destination-name">{location.location_name}</div>
                </div>
                {category_badge(location.category)}
            </div>
            <div class="destination-description">{short_description(location.description)}</div>
            <div class="destination-meta">{build_destination_meta(location)}</div>
            """,
            unsafe_allow_html=True,
        )
        st.button(
            "Sélectionné" if is_selected else "Sélectionner",
            key=f"select_{slug}",
            use_container_width=True,
            on_click=select_destination,
            args=(location.location_name,),
        )


def render_destination_panel(assistant: Workflow, query: str, category: str) -> None:
    results = assistant.navigation_service.search_locations(query=query, category=category)

    with st.container(key="destination_panel"):
        st.markdown('<div class="section-title">🏢 Emplacements disponibles</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="section-subtitle">{len(results)} emplacement(s) trouvé(s)</div>',
            unsafe_allow_html=True,
        )

        if not results:
            st.markdown(
                '<div class="empty-state">Aucun emplacement ne correspond à votre recherche actuelle.</div>',
                unsafe_allow_html=True,
            )
            return

        list_box = st.container(height=640)
        with list_box:
            for index in range(0, len(results), 2):
                row = st.columns(2, gap="medium")
                for column, location in zip(row, results[index:index + 2]):
                    with column:
                        render_destination_card(
                            location,
                            is_selected=st.session_state.selected_destination == location.location_name,
                        )


def render_status_panel(assistant: Workflow) -> None:
    current_position = "Station de recharge"
    battery = "100%"
    if st.session_state.robot_status.startswith("Navigation") and st.session_state.last_navigation_command:
        battery = "90%"
        current_position = st.session_state.last_navigation_command["location_name"]

    with st.container(key="status_panel"):
        st.markdown('<div class="section-title"> Statut du robot</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">État opérationnel en direct</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="status-grid">
                <div class="status-label">Statut:</div>
                <div class="status-value"><span class="status-pill">{st.session_state.robot_status}</span></div>
                <div class="status-label">Batterie:</div>
                <div class="status-value">{battery}</div>
                <div class="status-label">Position actuelle:</div>
                <div class="status-value">{current_position}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_selected_panel(assistant: Workflow) -> None:
    destination = get_destination_details(assistant, st.session_state.selected_destination)

    with st.container(key="selected_panel"):
        st.markdown('<div class="section-title">📌 Destination sélectionnée</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Détails de la zone choisie</div>', unsafe_allow_html=True)

        if not destination:
            st.markdown(
                '<div class="empty-state">Cliquez sur une destination à gauche pour afficher sa description ici.</div>',
                unsafe_allow_html=True,
            )
            return

        st.markdown(f'<div class="selected-destination">{destination.location_name}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="selected-description">{destination.description}</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="selected-details">
                <div class="selected-detail"><span class="selected-detail-icon">🏢</span><span>Bâtiment: {destination.building or 'Non précisé'}</span></div>
                <div class="selected-detail"><span class="selected-detail-icon">📍</span><span>Étage: {destination.floor or 'Non précisé'}</span></div>
                <div class="selected-detail {'accessible' if destination.accessible else ''}"><span class="selected-detail-icon">♿</span><span>{'Accessible fauteuil roulant' if destination.accessible else 'Accessibilité non précisée'}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(key="nav_action_button"):
            if st.button("➜ Démarrer la navigation robot", use_container_width=True):
                payload = assistant.navigation_service.start_navigation(
                    destination.location_name,
                    requested_by="streamlit_ui",
                )
                if payload:
                    st.session_state.last_navigation_command = payload
                    st.session_state.robot_status = f"Navigation vers {payload['location_name']}"
                    dispatch_status = payload.get("dispatch", {}).get("status", "queued")
                    st.success(
                        f"Navigation demandée vers {payload['location_name']} ({dispatch_status})."
                    )


def render_chat_messages(assistant: Workflow, pending_prompt: str | None = None) -> None:
    history = load_history(assistant, st.session_state.chat_conversation_id)

    if not history and not pending_prompt:
        with st.chat_message("assistant"):
            st.write(DEFAULT_ASSISTANT_GREETING)

    for message in history[-12:]:
        with st.chat_message("assistant" if message["role"] == "assistant" else "user"):
            st.write(message["content"])

    if pending_prompt:
        with st.chat_message("user"):
            st.write(pending_prompt)
        with st.chat_message("assistant"):
            st.markdown(
                '<div class="typing"><span></span><span></span><span></span></div>',
                unsafe_allow_html=True,
            )


def render_chat_widget(assistant: Workflow) -> None:
    pending_prompt = st.session_state.pending_chat_prompt

    with st.container(key="chat_widget_panel"):
        top_cols = st.columns([6.5, 0.9, 0.9])
        with top_cols[0]:
            st.markdown('<div class="widget-header-title">Assistant chat</div>', unsafe_allow_html=True)
        with top_cols[1]:
            with st.container(key="widget_icon_button_chat_new"):
                if st.button("+", key="new_chat_widget", use_container_width=True):
                    new_chat_conversation(assistant)
                    st.rerun(scope="fragment")
        with top_cols[2]:
            with st.container(key="widget_icon_button_chat_close"):
                if st.button("×", key="close_chat_widget", use_container_width=True):
                    close_chat_panel()
                    st.rerun(scope="fragment")

        message_box = st.container(height=360)
        with message_box:
            render_chat_messages(assistant, pending_prompt=pending_prompt)

        with st.form("chat_widget_form", clear_on_submit=True):
            input_cols = st.columns([6.2, 0.9], gap="small")
            with input_cols[0]:
                prompt = st.text_input(
                    "Message",
                    placeholder="Ecrivez votre message...",
                    label_visibility="collapsed",
                )
            with input_cols[1]:
                submitted = st.form_submit_button(">", use_container_width=True)

        if submitted and prompt.strip():
            st.session_state.pending_chat_prompt = prompt.strip()
            st.session_state.chat_processing = True
            st.rerun(scope="fragment")

    if pending_prompt and st.session_state.chat_processing:
        assistant.run_text(
            pending_prompt,
            conversation_id=st.session_state.chat_conversation_id,
        )
        st.session_state.pending_chat_prompt = None
        st.session_state.chat_processing = False
        st.rerun(scope="fragment")


def render_voice_widget(assistant: Workflow, bridge: VoiceBridgeServer) -> None:
    with st.container(key="voice_widget_panel"):
        top_cols = st.columns([6.5, 0.9, 0.9])
        with top_cols[0]:
            st.markdown('<div class="widget-header-title">Assistant vocal</div>', unsafe_allow_html=True)
        with top_cols[1]:
            with st.container(key="widget_icon_button_voice_new"):
                if st.button("+", key="new_audio_widget", use_container_width=True):
                    new_audio_conversation(assistant)
                    st.rerun(scope="fragment")
        with top_cols[2]:
            with st.container(key="widget_icon_button_voice_close"):
                if st.button("×", key="close_audio_widget", use_container_width=True):
                    close_voice_panel()
                    st.rerun(scope="fragment")

        st.markdown(
            '<div class="voice-panel-note">Parlez au robot, puis attendez sa réponse vocale automatique.</div>',
            unsafe_allow_html=True,
        )

        component_result = voice_assistant_orb(
            key="voice_assistant_orb_component",
            data={
                "api_port": bridge.port,
                "conversation_id": st.session_state.audio_conversation_id,
                "reset_token": st.session_state.voice_reset_token,
            },
        )

        voice_result = state_value(component_result, "voice_result")
        if voice_result:
            nonce = voice_result.get("nonce")
            if nonce != st.session_state.last_voice_event_nonce:
                st.session_state.last_voice_event_nonce = nonce
                st.session_state.last_voice_response = voice_result.get("response", "") or ""
                st.session_state.last_voice_transcription = voice_result.get("transcription", "") or ""
                st.session_state.last_voice_error = None
                st.session_state.robot_status = "Réponse vocale en cours"
                st.rerun(scope="fragment")

        playback_finished = state_value(component_result, "playback_finished")
        if playback_finished and playback_finished != st.session_state.last_playback_nonce:
            st.session_state.last_playback_nonce = playback_finished
            st.session_state.robot_status = "Prêt"
            st.rerun(scope="fragment")

        voice_error = state_value(component_result, "error")
        if voice_error:
            st.session_state.last_voice_error = voice_error
            st.session_state.robot_status = "Erreur vocale"

        if st.session_state.last_voice_error:
            st.caption(f"Statut vocal: {st.session_state.last_voice_error}")


def render_assistant_dock() -> None:
    if st.session_state.chat_panel_open or st.session_state.voice_panel_open:
        return

    with st.container(key="assistant_dock"):
        st.markdown('<div class="assist-copy">Besoin d’aide ?</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="assist-subcopy">Discutez avec le robot ou lancez une interaction vocale pour trouver votre destination.</div>',
            unsafe_allow_html=True,
        )

        dock_cols = st.columns(2, gap="small")
        with dock_cols[0]:
            st.button(
                "💬 Chat",
                key="chat_dock_button",
                use_container_width=True,
                on_click=open_chat_panel,
            )
        with dock_cols[1]:
            st.button(
                "🎤 Voix",
                key="voice_dock_button",
                use_container_width=True,
                on_click=open_voice_panel,
            )


@st.fragment
def render_navigation_fragment(assistant: Workflow) -> None:
    query, category = render_search_panel(assistant)

    main_left, main_right = st.columns([2.15, 1.0], gap="large")
    with main_left:
        render_destination_panel(assistant, query, category)
    with main_right:
        render_selected_panel(assistant)
        st.write("")
        render_status_panel(assistant)


@st.fragment
def render_assistant_fragment(assistant: Workflow, bridge: VoiceBridgeServer) -> None:
    if st.session_state.chat_panel_open:
        with st.container(key="floating_chat_panel"):
            render_chat_widget(assistant)
        return

    if st.session_state.voice_panel_open:
        with st.container(key="floating_voice_panel"):
            render_voice_widget(assistant, bridge)
        return

    render_assistant_dock()


def main() -> None:
    inject_styles()
    assistant = get_assistant()
    bridge = get_voice_bridge()
    init_session_state(assistant)

    render_header()
    render_navigation_fragment(assistant)
    render_assistant_fragment(assistant, bridge)


if __name__ == "__main__":
    main()
