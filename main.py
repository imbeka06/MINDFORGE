import streamlit as st
import os
import json
from dotenv import load_dotenv

# --- 1. SETUP ---
load_dotenv()
from project_manager import load_projects, create_project, update_project_notes, delete_project
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

# --- 2. THEME MANAGER ---
def apply_theme(theme_name):
    common_css = """
        h1, h2, h3, h4, h5, h6, p, li, span, div, label { color: #E0E0E0 !important; }
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {
            background-color: #2E303E !important; color: #FFFFFF !important; border: 1px solid #4A4D5A;
        }
        .stSelectbox > div > div > div { background-color: #2E303E !important; color: #FFFFFF !important; }
    """
    if theme_name == "🌙 Dark Mode":
        st.markdown(f"<style>.stApp {{ background-color: #0E1117; }} [data-testid='stSidebar'] {{ background-color: #171923; }} {common_css}</style>", unsafe_allow_html=True)
    elif theme_name == "🌊 Ocean Blue":
        st.markdown(f"<style>.stApp {{ background-color: #0F172A; }} [data-testid='stSidebar'] {{ background-color: #1E293B; }} h1, h2 {{ color: #38BDF8 !important; }} .stButton>button {{ background-color: #3B82F6; color: white; }} {common_css}</style>", unsafe_allow_html=True)

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
    
    # Theme & Model (Added KEYS to prevent DuplicateID error)
    col1, col2 = st.columns(2)
    with col1:
        selected_theme = st.selectbox("🎨 Theme", ["☀️ Light Mode", "🌙 Dark Mode", "🌊 Ocean Blue"], key="sidebar_theme")
        if selected_theme != st.session_state.theme:
            st.session_state.theme = selected_theme
            st.rerun()
    with col2:
        # Saving model to session state to prevent slow switching
        if "model_choice" not in st.session_state: st.session_state.model_choice = "gpt-3.5-turbo"
        st.session_state.model_choice = st.selectbox("🧠 Model", ["gpt-3.5-turbo", "gpt-4-turbo"], key="sidebar_model")
    
    apply_theme(st.session_state.theme)
    st.divider()

    # Project Manager
    projects = load_projects()
    project_list = list(projects.keys())
    
    # Unit Selector (Added KEY)
    idx = 0
    if st.session_state.current_project in project_list:
        idx = project_list.index(st.session_state.current_project) + 1
    
    selected = st.selectbox("📂 Unit:", ["Select..."] + project_list, index=idx, key="sidebar_unit_select")
    
    # Load Unit Logic
    if selected != "Select..." and selected != st.session_state.current_project:
        st.session_state.current_project = selected
        path = projects[selected]['path']
        loaded_vs = load_vector_db(path)
        st.session_state.vector_store = loaded_vs if loaded_vs else None
        
        # Load Chat History
        from main import load_chat_history
        st.session_state.chat_history = load_chat_history(path)
        st.toast(f"Loaded {selected}")
        st.rerun()

    # Create Unit
    with st.expander("➕ New Unit"):
        with st.form("new_unit_form"):
            new_name = st.text_input("Name")
            if st.form_submit_button("Create") and new_name:
                create_project(new_name)
                st.rerun()
                
    # Delete Unit (Red Button)
    if st.session_state.current_project:
        with st.expander("🗑️ Delete Unit"):
            st.warning(f"Delete {st.session_state.current_project}?")
            if st.button("Confirm Delete", type="primary"):
                delete_project(st.session_state.current_project)
                st.session_state.current_project = None
                st.success("Deleted!")
                st.rerun()
    
    st.divider()
    
    # Music (Moved OUTSIDE logic so it never vanishes)
    st.markdown("### 🎧 Study Playlist")
    music = st.radio("Vibe", ["Off", "☕ Lofi", "🎻 Dark", "🎷 Jazz", "🥀 Lana", "🖤 Orgavsm"], key="music_radio")
    
    links = {
        "☕ Lofi": "https://www.youtube.com/watch?v=7ccH8u8fj8Y",
        "🎻 Dark": "https://www.youtube.com/watch?v=D9km3yXmR8k",
        "🎷 Jazz": "https://www.youtube.com/watch?v=e2A3_111fwc",
        "🥀 Lana": "https://www.youtube.com/watch?v=5XJNg8x89yo",
        "🖤 Orgavsm": "https://www.youtube.com/watch?v=ZHLL7dPIxPw"
    }
    if music != "Off": st.video(links[music])
    
    st.markdown("<div style='text-align:center;font-size:0.8em;opacity:0.7'>Dev: IMBEKA MUSA</div>", unsafe_allow_html=True)

# Helper Functions
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
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📂 Upload/Input", "📝 Notes", "🗺️ Map", "💬 Chat", "🎓 Quiz", "🔍 Research"])

    # TAB 1: UPLOAD & INPUT
    with tab1:
        st.info(f"Using {st.session_state.model_choice} for analysis.")
        
        # New Input Types
        input_method = st.radio("Input Method:", ["📄 Upload File", "📋 Paste Text", "🖼️ Upload Image", "🎥 YouTube"], horizontal=True)
        doc_data = None
        
        # 1. File Upload
        if input_method == "📄 Upload File":
            f = st.file_uploader("Upload", type=["pdf", "docx", "txt"])
            if f:
                path = os.path.join(p_data['path'], f.name)
                with open(path, "wb") as w: w.write(f.getbuffer())
                st.success(f"Saved: {f.name}")
                if st.button("🧠 Deep Analyze File"):
                    with st.spinner("Reading file..."):
                        doc_data = process_document(path)
        
        # 2. Paste Text
        elif input_method == "📋 Paste Text":
            raw_text = st.text_area("Paste your notes/text here:", height=300)
            if raw_text and st.button("🧠 Analyze Text"):
                 # We manually package the text to look like a document
                 from langchain.text_splitter import RecursiveCharacterTextSplitter
                 splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
                 chunks = splitter.split_text(raw_text)
                 doc_data = {"filename": "pasted_text.txt", "full_text": raw_text, "chunks": chunks, "chunk_count": len(chunks)}

        # 3. Image Upload (Simple Text Mode)
        elif input_method == "🖼️ Upload Image":
            img_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
            if img_file:
                st.image(img_file, width=300)
                if st.button("🧠 Analyze Image"):
                    st.warning("Note: Image text extraction works best with GPT-4 Vision selected.")
                    # For MVP, we simply acknowledge the image. 
                    # Real OCR would require complex Tesseract install or GPT-4 Vision calls.
                    # We will placeholder this with a "Describe" prompt if we had Vision enabled.
                    st.info("Image uploaded. Switch to 'Paste Text' if OCR fails.")

        # 4. YouTube
        elif input_method == "🎥 YouTube":
            url = st.text_input("Link:")
            if url and st.button("Analyze Video"):
                with st.spinner("Transcribing..."):
                    doc_data = process_video(url)

        # Process Data if found
        if doc_data:
            summary = generate_deep_summary(doc_data['chunks'], st.session_state.model_choice)
            mm = generate_mind_map(doc_data['chunks'][0], st.session_state.model_choice)
            vs = create_vector_db(doc_data['chunks'], p_data['path'])
            
            st.session_state.vector_store = vs
            st.session_state.last_summary = summary
            st.session_state.last_mm = mm
            st.success("Analysis Complete! Memory Saved.")

    # TAB 2: NOTES
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            notes = st.text_area("Scratchpad", value=p_data.get("notes",""), height=400, key="scratchpad_area")
            if st.button("Save Notes", key="save_notes_btn"): update_project_notes(st.session_state.current_project, notes)
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
        else: st.info("Analyze content to see map.")

    # TAB 4: CHAT
    with tab4:
        audio = st.audio_input("🎙️ Voice")
        q = transcribe_audio(audio) if audio else st.chat_input("Type...")

        if q and st.session_state.vector_store:
            st.session_state.chat_history.append({"role": "user", "content": q})
            
            with st.spinner("Thinking..."):
                ans = get_chat_response(q, st.session_state.vector_store, st.session_state.model_choice)
            
            st.session_state.chat_history.append({"role": "assistant", "content": ans})
            save_chat_history(p_data['path'], st.session_state.chat_history)
            
            audio_response = text_to_speech(ans)
            if audio_response: st.audio(audio_response, format="audio/mp3")

        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

    # TAB 5: QUIZ
    with tab5:
        if st.button("New Quiz", key="new_quiz_btn"):
            if st.session_state.last_summary:
                st.session_state.last_quiz = generate_quiz(st.session_state.last_summary, st.session_state.model_choice)
        
        if st.session_state.last_quiz:
            for i, q in enumerate(st.session_state.last_quiz):
                st.write(f"**Q{i+1}: {q['question']}**")
                ans = st.radio(f"Options {i}", q['options'], key=f"quiz_q_{i}")
                if st.button(f"Check {i+1}", key=f"quiz_btn_{i}"):
                    if ans == q['answer']: st.success("Correct!")
                    else: st.error(f"Wrong. It was {q['answer']}")
                st.divider()

    # TAB 6: RESEARCH
    with tab6:
        st.subheader("🔎 Academic Search (ArXiv)")
        topic = st.text_input("Enter research topic:", key="research_input")
        if st.button("Search Papers", key="research_btn"):
            with st.spinner("Searching ArXiv database..."):
                results = search_arxiv_papers(topic)
                for r in results:
                    with st.expander(f"📄 {r['title']} ({r['published']})"):
                        st.write(f"**Abstract:** {r['summary']}")
                        st.markdown(f"[📥 Download PDF]({r['pdf_url']})")

else:
    st.info("👈 Open a Unit to begin.")