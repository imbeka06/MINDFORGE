import streamlit as st
import os
import json
from dotenv import load_dotenv

# --- 1. SETUP ---
load_dotenv()
from project_manager import load_projects, create_project, update_project_notes
from pdf_processor import process_document
from video_processor import process_video
from ai_engine import (
    generate_deep_summary, generate_mind_map, create_vector_db, load_vector_db,
    get_chat_response, generate_quiz, search_arxiv_papers,
    transcribe_audio, text_to_speech
)

st.set_page_config(page_title="MindForge AI", page_icon="🧠", layout="wide")

if not os.getenv("OPENAI_API_KEY"):
    st.error("⚠️ OPENAI_API_KEY not found! Check your .env file.")
    st.stop()

# --- 2. THEME MANAGER (FIXED) ---
def apply_theme(theme_name):
    """
    Applies heavy-duty CSS to force theme changes.
    """
    # Common styles for Dark and Blue modes to ensure text is visible
    common_css = """
        /* Force Text Colors */
        h1, h2, h3, h4, h5, h6, p, li, span, div, label { color: #E0E0E0 !important; }
        
        /* Input Fields (Background & Text) */
        .stTextInput > div > div > input, 
        .stTextArea > div > div > textarea {
            background-color: #2E303E !important;
            color: #FFFFFF !important;
            border: 1px solid #4A4D5A;
        }
        
        /* Dropdowns & Selectboxes */
        .stSelectbox > div > div > div {
            background-color: #2E303E !important;
            color: #FFFFFF !important;
        }
        
        /* Sidebar Text */
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p {
             color: #E0E0E0 !important;
        }
    """

    if theme_name == "🌙 Dark Mode":
        st.markdown(f"""
            <style>
                /* App Background */
                .stApp {{ background-color: #0E1117; }}
                /* Sidebar Background */
                [data-testid="stSidebar"] {{ background-color: #171923; }}
                {common_css}
            </style>
        """, unsafe_allow_html=True)
        
    elif theme_name == "🌊 Ocean Blue":
        st.markdown(f"""
            <style>
                /* App Background */
                .stApp {{ background-color: #0F172A; }}
                /* Sidebar Background */
                [data-testid="stSidebar"] {{ background-color: #1E293B; }}
                /* Header Highlights */
                h1, h2 {{ color: #38BDF8 !important; }}
                /* Buttons */
                .stButton > button {{
                    background-color: #3B82F6;
                    color: white;
                    border: none;
                }}
                {common_css}
            </style>
        """, unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if "current_project" not in st.session_state: st.session_state.current_project = None
if "vector_store" not in st.session_state: st.session_state.vector_store = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "last_summary" not in st.session_state: st.session_state.last_summary = None
if "last_mm" not in st.session_state: st.session_state.last_mm = None
if "last_quiz" not in st.session_state: st.session_state.last_quiz = None 
if "theme" not in st.session_state: st.session_state.theme = "☀️ Light Mode"

# --- 4. SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/brain--v1.png", width=50)
    st.markdown("## MindForge AI")
    
    # Theme & Model
    col1, col2 = st.columns(2)
    with col1:
        # We use a callback logic here to ensure theme applies instantly
        selected_theme = st.selectbox("🎨 Theme", ["☀️ Light Mode", "🌙 Dark Mode", "🌊 Ocean Blue"], index=["☀️ Light Mode", "🌙 Dark Mode", "🌊 Ocean Blue"].index(st.session_state.theme))
        if selected_theme != st.session_state.theme:
            st.session_state.theme = selected_theme
            st.rerun()
            
    with col2:
        model_choice = st.selectbox("🧠 Model", ["gpt-3.5-turbo", "gpt-4-turbo"], index=0)
    
    # APPLY THEME IMMEDIATELY
    apply_theme(st.session_state.theme)
    st.divider()

    # Project Selection
    projects = load_projects()
    project_list = list(projects.keys())
    
    # Smart Selection Logic
    index = 0
    if st.session_state.current_project and st.session_state.current_project in project_list:
        index = project_list.index(st.session_state.current_project) + 1
        
    selected = st.selectbox("📂 Unit:", ["Select..."] + project_list, index=index)
    
    # INTELLIGENT LOAD (MEMORY + CHAT HISTORY)
    if selected != "Select..." and selected != st.session_state.current_project:
        st.session_state.current_project = selected
        path = projects[selected]['path']
        
        # Load Brain
        loaded_vs = load_vector_db(path)
        st.session_state.vector_store = loaded_vs if loaded_vs else None
        
        # Load History
        from main import load_chat_history # Self-import helper
        st.session_state.chat_history = load_chat_history(path)
        st.toast(f"Loaded {selected}")
        st.rerun()

    # Create Unit
    with st.form("new_unit"):
        new_name = st.text_input("Name")
        if st.form_submit_button("➕ New Unit") and new_name:
            create_project(new_name)
            st.rerun()
    
    # Music
    st.divider()
    music = st.radio("🎧 Music", ["Off", "☕ Lofi", "🎻 Dark", "🎷 Jazz", "🥀 Lana", "🖤 Orgavsm"])
    links = {
        "☕ Lofi": "https://www.youtube.com/watch?v=7ccH8u8fj8Y",
        "🎻 Dark": "https://www.youtube.com/watch?v=D9km3yXmR8k",
        "🎷 Jazz": "https://www.youtube.com/watch?v=e2A3_111fwc",
        "🥀 Lana": "https://www.youtube.com/watch?v=5XJNg8x89yo",
        "🖤 Orgavsm": "https://www.youtube.com/watch?v=ZHLL7dPIxPw"
    }
    if music != "Off": st.video(links[music])
    
    st.markdown("<div style='text-align:center;font-size:0.8em;opacity:0.7'>Dev: IMBEKA MUSA</div>", unsafe_allow_html=True)

# Helper Functions (Moved below imports usually, but kept here for logical flow in copy-paste)
def save_chat_history(project_path, history):
    file_path = os.path.join(project_path, "chat_history.json")
    with open(file_path, "w") as f: json.dump(history, f)

def load_chat_history(project_path):
    file_path = os.path.join(project_path, "chat_history.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f: return json.load(f)
    return []

# --- 5. MAIN APP ---
if st.session_state.current_project:
    p_data = projects[st.session_state.current_project]
    st.title(f"📚 {st.session_state.current_project}")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📂 Upload", "📝 Notes", "🗺️ Map", "💬 Chat", "🎓 Quiz", "🔍 Research"])

    # TAB 1: UPLOAD
    with tab1:
        st.info(f"Using {model_choice} for analysis.")
        src = st.radio("Type:", ["📄 File (PDF/DOCX/TXT)", "🎥 YouTube"], horizontal=True)
        doc_data = None
        
        if "File" in src:
            f = st.file_uploader("Upload", type=["pdf", "docx", "txt"])
            if f:
                path = os.path.join(p_data['path'], f.name)
                with open(path, "wb") as w: w.write(f.getbuffer())
                st.success(f"Saved: {f.name}")
                if st.button("🧠 Deep Analyze"):
                    with st.spinner("Reading multiple pages... (This may take 30s)"):
                        doc_data = process_document(path)
        else:
            url = st.text_input("Link:")
            if url and st.button("Analyze Video"):
                with st.spinner("Transcribing..."):
                    doc_data = process_video(url)

        if doc_data:
            # Generate Assets
            summary = generate_deep_summary(doc_data['chunks'], model_choice)
            mm = generate_mind_map(doc_data['chunks'][0], model_choice)
            vs = create_vector_db(doc_data['chunks'], p_data['path'])
            
            st.session_state.vector_store = vs
            st.session_state.last_summary = summary
            st.session_state.last_mm = mm
            st.success("Deep Analysis Complete!")

    # TAB 2: NOTES
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            notes = st.text_area("Scratchpad", value=p_data.get("notes",""), height=400)
            if st.button("Save Notes"): update_project_notes(st.session_state.current_project, notes)
        with c2:
            st.subheader("Executive Report")
            if st.session_state.last_summary: st.markdown(st.session_state.last_summary)

    # TAB 3: MAP
    with tab3:
        if st.session_state.last_mm:
            from streamlit_agraph import agraph, Node, Edge, Config
            nodes, edges, seen = [], [], set()
            for n in st.session_state.last_mm.get("nodes", []):
                if n["id"] not in seen:
                    nodes.append(Node(id=n["id"], label=n["id"], size=20, color="#FF4B4B"))
                    seen.add(n["id"])
            for e in st.session_state.last_mm.get("edges", []):
                if e["from"] in seen and e["to"] in seen:
                    edges.append(Edge(source=e["from"], target=e["to"]))
            agraph(nodes, edges, Config(height=500, directed=True, physics=True))

    # TAB 4: CHAT (PERSISTENT)
    with tab4:
        # Voice Input
        audio = st.audio_input("🎙️ Voice")
        q = transcribe_audio(audio) if audio else st.chat_input("Type...")

        if q and st.session_state.vector_store:
            st.session_state.chat_history.append({"role": "user", "content": q})
            
            with st.spinner("Thinking..."):
                ans = get_chat_response(q, st.session_state.vector_store, model_choice)
            
            st.session_state.chat_history.append({"role": "assistant", "content": ans})
            
            # SAVE HISTORY TO DISK
            save_chat_history(p_data['path'], st.session_state.chat_history)
            
            # TTS
            audio_response = text_to_speech(ans)
            if audio_response: st.audio(audio_response, format="audio/mp3")

        # Display History
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

    # TAB 5: QUIZ
    with tab5:
        if st.button("New Quiz"):
            if st.session_state.last_summary:
                st.session_state.last_quiz = generate_quiz(st.session_state.last_summary, model_choice)
        
        if st.session_state.last_quiz:
            score = 0
            for i, q in enumerate(st.session_state.last_quiz):
                st.write(f"**Q{i+1}: {q['question']}**")
                ans = st.radio(f"Options {i}", q['options'], key=f"q{i}")
                if st.button(f"Check {i+1}", key=f"b{i}"):
                    if ans == q['answer']: st.success("Correct!")
                    else: st.error(f"Wrong. It was {q['answer']}")
                st.divider()

    # TAB 6: RESEARCH
    with tab6:
        st.subheader("🔎 Academic Search (ArXiv)")
        topic = st.text_input("Enter research topic:")
        if st.button("Search Papers"):
            with st.spinner("Searching ArXiv database..."):
                results = search_arxiv_papers(topic)
                for r in results:
                    with st.expander(f"📄 {r['title']} ({r['published']})"):
                        st.write(f"**Abstract:** {r['summary']}")
                        st.markdown(f"[📥 Download PDF]({r['pdf_url']})")

else:
    st.info("👈 Open a Unit to begin.")