import streamlit as st
import os
import json
from dotenv import load_dotenv

# --- 1. SETUP & CONFIGURATION ---
load_dotenv()

# Import Custom Modules
from project_manager import load_projects, create_project, update_project_notes, delete_project
from pdf_processor import process_document
from video_processor import process_video
from ai_engine import (
    generate_deep_summary, generate_mind_map, create_vector_db, load_vector_db,
    get_chat_response, generate_quiz, search_arxiv_papers,
    transcribe_audio, text_to_speech
)

# Set Page Config
st.set_page_config(page_title="MindForge AI", page_icon="🧠", layout="wide")

# Check for API Key
if not os.getenv("OPENAI_API_KEY"):
    st.error("⚠️ OPENAI_API_KEY not found! Please check your .env file.")
    st.stop()

# --- 2. HELPER FUNCTIONS ---
def save_chat_history(project_path, history):
    """Saves the chat history list to a JSON file."""
    file_path = os.path.join(project_path, "chat_history.json")
    with open(file_path, "w") as f:
        json.dump(history, f)

def load_chat_history(project_path):
    """Loads the chat history list from a JSON file."""
    file_path = os.path.join(project_path, "chat_history.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []

# --- 3. THEME MANAGER ---
def apply_theme(theme_name):
    """
    Applies strict CSS styling for Light, Dark, and Ocean Blue themes.
    """
    base_css = """
    <style>
        h1, h2, h3, h4, h5, h6, p, li, span, div, label { color: #E0E0E0 !important; }
        .stTextInput > div > div > input { background-color: #2E303E !important; color: #FFFFFF !important; border: 1px solid #4A4D5A; }
        .stTextArea > div > div > textarea { background-color: #2E303E !important; color: #FFFFFF !important; border: 1px solid #4A4D5A; }
        .stSelectbox > div > div > div { background-color: #2E303E !important; color: #FFFFFF !important; }
        [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
    </style>
    """

    if theme_name == "🌙 Dark Mode":
        st.markdown(f"""
            <style>
                .stApp {{ background-color: #0E1117; }}
                [data-testid="stSidebar"] {{ background-color: #171923; }}
            </style>
            {base_css}
        """, unsafe_allow_html=True)

    elif theme_name == "🌊 Ocean Blue":
        st.markdown(f"""
            <style>
                .stApp {{ background-color: #0F172A; }}
                [data-testid="stSidebar"] {{ background-color: #1E293B; }}
                h1, h2 {{ color: #38BDF8 !important; }}
                .stButton > button {{ background-color: #3B82F6; color: white; border: none; font-weight: bold; }}
            </style>
            {base_css}
        """, unsafe_allow_html=True)

# --- 4. SESSION STATE INITIALIZATION ---
if "current_project" not in st.session_state: st.session_state.current_project = None
if "vector_store" not in st.session_state: st.session_state.vector_store = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "last_summary" not in st.session_state: st.session_state.last_summary = None
if "last_mm" not in st.session_state: st.session_state.last_mm = None
if "last_quiz" not in st.session_state: st.session_state.last_quiz = None
if "theme" not in st.session_state: st.session_state.theme = "☀️ Light Mode"
if "model_choice" not in st.session_state: st.session_state.model_choice = "gpt-3.5-turbo"

# --- 5. SIDEBAR INTERFACE ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/brain--v1.png", width=50)
    st.markdown("## MindForge AI")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_theme = st.selectbox("🎨 Theme", ["☀️ Light Mode", "🌙 Dark Mode", "🌊 Ocean Blue"], key="theme_selector_sidebar")
        if selected_theme != st.session_state.theme:
            st.session_state.theme = selected_theme
            st.rerun()

    with col2:
        st.session_state.model_choice = st.selectbox("🧠 Model", ["gpt-3.5-turbo", "gpt-4-turbo"], key="model_selector_sidebar")
    
    apply_theme(st.session_state.theme)
    st.divider()

    # --- UNIT MANAGER ---
    projects = load_projects()
    project_list = sorted(list(projects.keys()))
    
    selected_unit_option = st.selectbox("📂 Select Unit:", ["Select..."] + project_list, key="main_unit_dropdown")
    
    if selected_unit_option != "Select...":
        st.markdown(f"**Action for: {selected_unit_option}**")
        col_open, col_delete = st.columns(2)
        
        with col_open:
            if st.button("🚀 OPEN", type="primary", use_container_width=True, key="btn_open_unit"):
                st.session_state.current_project = selected_unit_option
                project_path = projects[selected_unit_option]['path']
                st.session_state.vector_store = load_vector_db(project_path)
                st.session_state.chat_history = load_chat_history(project_path)
                st.toast(f"Unit Loaded: {selected_unit_option}")
                st.rerun()

        with col_delete:
            if st.button("🗑️ DELETE", type="secondary", use_container_width=True, key="btn_delete_unit"):
                success = delete_project(selected_unit_option)
                if success:
                    st.session_state.current_project = None
                    st.session_state.vector_store = None
                    st.session_state.chat_history = []
                    st.session_state.last_summary = None
                    st.session_state.last_mm = None
                    st.session_state.last_quiz = None
                    st.success(f"Deleted {selected_unit_option}")
                    st.rerun()
                else:
                    st.error("Could not delete. Folder might be open elsewhere.")

    with st.expander("➕ Create New Unit"):
        with st.form("create_unit_form_sidebar"):
            new_unit_name = st.text_input("Unit Name")
            if st.form_submit_button("Create") and new_unit_name:
                create_project(new_unit_name)
                st.success(f"Created {new_unit_name}!")
                st.rerun()

    st.divider()

    # --- MUSIC PLAYER ---
    st.markdown("### 🎧 Study Playlist")
    music_vibe = st.radio("Select Vibe:", ["Off", "☕ Lofi Girl", "🎻 Dark Academia", "🎷 60s Jazz/Soul", "🥀 Lana Del Rey", "🖤 Orgavsm"], key="music_player_radio")
    music_links = {
        "☕ Lofi Girl": "https://www.youtube.com/watch?v=7ccH8u8fj8Y",
        "🎻 Dark Academia": "https://www.youtube.com/watch?v=D9km3yXmR8k",
        "🎷 60s Jazz/Soul": "https://www.youtube.com/watch?v=e2A3_111fwc",
        "🥀 Lana Del Rey": "https://www.youtube.com/watch?v=5XJNg8x89yo",
        "🖤 Orgavsm": "https://www.youtube.com/watch?v=ZHLL7dPIxPw"
    }
    if music_vibe != "Off": st.video(music_links[music_vibe])

    st.divider()
    st.markdown(
        """<div style="text-align: center; opacity: 0.7; font-size: 0.8em; margin-top: 20px;">
            Architect and Developer<br><strong>IMBEKA MUSA</strong>
        </div>""", unsafe_allow_html=True
    )

# --- 6. MAIN APPLICATION CONTENT ---
if st.session_state.current_project and st.session_state.current_project in projects:
    project_data = projects[st.session_state.current_project]
    st.title(f"📚 {st.session_state.current_project}")
    
    # DEFINING TABS - (Mind Map is included here)
    tab_upload, tab_images, tab_notes, tab_map, tab_chat, tab_quiz, tab_research = st.tabs([
        "📂 Upload & Input", 
        "🖼️ Image Analysis",
        "📝 Notes & Report", 
        "🗺️ Mind Map", 
        "💬 AI Chat", 
        "🎓 Interactive Quiz", 
        "🔍 Research (ArXiv)"
    ])

    # --- TAB 1: UPLOAD & INPUT ---
    with tab_upload:
        st.info(f"Currently using model: **{st.session_state.model_choice}**")
        input_method = st.radio("Select Input Method:", ["📄 Upload File (PDF/DOCX/TXT)", "📋 Paste Text", "🎥 YouTube Video"], horizontal=True, key="input_method_selector")
        doc_data = None
        
        if input_method == "📄 Upload File (PDF/DOCX/TXT)":
            uploaded_file = st.file_uploader("Choose a file...", type=["pdf", "docx", "txt"], key="main_file_uploader")
            if uploaded_file:
                save_path = os.path.join(project_data['path'], uploaded_file.name)
                with open(save_path, "wb") as f: f.write(uploaded_file.getbuffer())
                st.success(f"File Saved: {uploaded_file.name}")
                if st.button("🧠 Deep Analyze File", key="btn_analyze_file"):
                    with st.spinner("Processing document..."): doc_data = process_document(save_path)

        elif input_method == "📋 Paste Text":
            pasted_text = st.text_area("Paste your study notes here:", height=300, key="text_paste_area")
            if pasted_text and st.button("🧠 Analyze Text", key="btn_analyze_text"):
                 from langchain.text_splitter import RecursiveCharacterTextSplitter
                 text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
                 chunks = text_splitter.split_text(pasted_text)
                 doc_data = {"filename": "manual_notes.txt", "full_text": pasted_text, "chunks": chunks, "chunk_count": len(chunks)}

        elif input_method == "🎥 YouTube Video":
            video_url = st.text_input("Paste YouTube Link:", key="youtube_url_input")
            if video_url and st.button("🧠 Analyze Video", key="btn_analyze_video"):
                with st.spinner("Fetching transcript..."):
                    doc_data = process_video(video_url)
                    if not doc_data: st.error("Could not retrieve transcript.")

        if doc_data:
            summary = generate_deep_summary(doc_data['chunks'], st.session_state.model_choice)
            mm_data = generate_mind_map(doc_data['chunks'][0], st.session_state.model_choice)
            vector_store = create_vector_db(doc_data['chunks'], save_path=project_data['path'])
            st.session_state.vector_store = vector_store
            st.session_state.last_summary = summary
            st.session_state.last_mm = mm_data
            st.success("✅ Analysis Complete! Memory Updated.")

    # --- TAB 2: IMAGE ANALYSIS ---
    with tab_images:
        st.subheader("🖼️ Visual Study Assistant")
        uploaded_image = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'], key="image_uploader_tab")
        if uploaded_image:
            st.image(uploaded_image, width=500)
            if st.button("🧠 Extract Knowledge", key="btn_analyze_image"):
                st.info("Analysis simulated (Enable Vision API to activate).")

    # --- TAB 3: NOTES & REPORT ---
    with tab_notes:
        col_scratchpad, col_report = st.columns(2)
        with col_scratchpad:
            st.subheader("📝 Your Scratchpad")
            user_notes = st.text_area("Type your personal notes here...", value=project_data.get("notes", ""), height=500, key="scratchpad_text_area")
            if st.button("💾 Save Notes", key="btn_save_notes"):
                update_project_notes(st.session_state.current_project, user_notes)
                st.toast("Notes saved successfully!")
        with col_report:
            st.subheader("📑 AI Executive Report")
            if st.session_state.last_summary: st.markdown(st.session_state.last_summary)
            else: st.info("No analysis generated yet.")

    # --- TAB 4: MIND MAP (RESTORED) ---
    with tab_map:
        st.subheader("🗺️ Knowledge Graph")
        if st.session_state.last_mm:
            from streamlit_agraph import agraph, Node, Edge, Config
            nodes, edges, seen_ids = [], [], set()
            
            # Parse Nodes
            for node in st.session_state.last_mm.get("nodes", []):
                if node["id"] not in seen_ids:
                    nodes.append(Node(id=node["id"], label=node["id"], size=25, shape="dot", color="#FF4B4B"))
                    seen_ids.add(node["id"])
            
            # Parse Edges
            for edge in st.session_state.last_mm.get("edges", []):
                if edge["from"] in seen_ids and edge["to"] in seen_ids:
                    edges.append(Edge(source=edge["from"], target=edge["to"], color="#E0E0E0"))
            
            config = Config(width=None, height=600, directed=True, physics=True, hierarchical=False)
            if nodes:
                agraph(nodes=nodes, edges=edges, config=config)
            else:
                st.warning("Mind map data was empty. Try analyzing a simpler document.")
        else:
            st.info("Analyze a document in the 'Upload' tab to generate a Mind Map.")

    # --- TAB 5: CHAT ---
    with tab_chat:
        st.subheader("💬 Chat with your Unit")
        audio_input = st.audio_input("🎙️ Speak your question", key="audio_chat_input")
        if audio_input: user_query = transcribe_audio(audio_input)
        else: user_query = st.chat_input("Type your question here...", key="text_chat_input")

        if user_query and st.session_state.vector_store:
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            with st.spinner("Thinking..."):
                ai_response = get_chat_response(user_query, st.session_state.vector_store, st.session_state.model_choice)
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            save_chat_history(project_data['path'], st.session_state.chat_history)
            audio_response = text_to_speech(ai_response)
            if audio_response: st.audio(audio_response, format="audio/mp3")

        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]): st.markdown(message["content"])

    # --- TAB 6: QUIZ ---
    with tab_quiz:
        st.subheader("🎓 Test Your Knowledge")
        if st.button("🎲 Generate New Quiz", key="btn_generate_quiz"):
            if st.session_state.last_summary:
                with st.spinner("Drafting questions..."):
                    st.session_state.last_quiz = generate_quiz(st.session_state.last_summary, st.session_state.model_choice)
            else: st.warning("Please analyze a document first.")
        
        if st.session_state.last_quiz:
            for i, question in enumerate(st.session_state.last_quiz):
                st.markdown(f"**Question {i+1}: {question['question']}**")
                answer = st.radio(f"Select Answer for Q{i+1}:", question['options'], key=f"quiz_radio_{i}")
                if st.button(f"Check Answer {i+1}", key=f"btn_check_quiz_{i}"):
                    if answer == question['answer']: st.success("✅ Correct!")
                    else: st.error(f"❌ Wrong. Correct: {question['answer']}")
                st.divider()

    # --- TAB 7: RESEARCH ---
    with tab_research:
        st.subheader("🔎 Academic Research (ArXiv)")
        research_topic = st.text_input("Enter a research topic:", key="research_topic_input")
        if st.button("Search Papers", key="btn_search_arxiv"):
            with st.spinner("Searching ArXiv Database..."):
                results = search_arxiv_papers(research_topic)
                for result in results:
                    with st.expander(f"📄 {result['title']} ({result['published']})"):
                        st.markdown(f"**Abstract:** {result['summary']}")
                        st.markdown(f"[📥 Download PDF]({result['pdf_url']})")

elif st.session_state.current_project is None:
    st.markdown("## 👋 Welcome to MindForge AI")
    st.info("👈 **Start Here:** Select a Unit from the sidebar and click 'ROCKET OPEN'.")