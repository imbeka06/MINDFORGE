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
    st.error("⚠️ OPENAI_API_KEY not found! Please check your .env file settings on Cloud.")
    st.stop()

# --- 2. HELPER FUNCTIONS ---
def save_chat_history(project_path, history):
    file_path = os.path.join(project_path, "chat_history.json")
    with open(file_path, "w") as f:
        json.dump(history, f)

def load_chat_history(project_path):
    file_path = os.path.join(project_path, "chat_history.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []

# --- 3. THEME MANAGER ---
def apply_theme(theme_name):
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
        st.markdown(f"<style>.stApp {{ background-color: #0E1117; }} [data-testid='stSidebar'] {{ background-color: #171923; }}</style>{base_css}", unsafe_allow_html=True)
    elif theme_name == "🌊 Ocean Blue":
        st.markdown(f"<style>.stApp {{ background-color: #0F172A; }} [data-testid='stSidebar'] {{ background-color: #1E293B; }} h1, h2 {{ color: #38BDF8 !important; }} .stButton > button {{ background-color: #3B82F6; color: white; border: none; font-weight: bold; }}</style>{base_css}", unsafe_allow_html=True)

# --- 4. SESSION STATE ---
if "current_project" not in st.session_state: st.session_state.current_project = None
if "vector_store" not in st.session_state: st.session_state.vector_store = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "last_summary" not in st.session_state: st.session_state.last_summary = None
if "last_mm" not in st.session_state: st.session_state.last_mm = None
if "last_quiz" not in st.session_state: st.session_state.last_quiz = None
if "theme" not in st.session_state: st.session_state.theme = "☀️ Light Mode"
if "model_choice" not in st.session_state: st.session_state.model_choice = "gpt-3.5-turbo"

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/brain--v1.png", width=50)
    st.markdown("## MindForge AI")
    
    col1, col2 = st.columns(2)
    with col1:
        # UNIQUE KEY 1: theme_selector_sidebar
        selected_theme = st.selectbox("🎨 Theme", ["☀️ Light Mode", "🌙 Dark Mode", "🌊 Ocean Blue"], key="theme_selector_sidebar")
        if selected_theme != st.session_state.theme:
            st.session_state.theme = selected_theme
            st.rerun()

    with col2:
        # UNIQUE KEY 2: model_selector_sidebar
        st.session_state.model_choice = st.selectbox("🧠 Model", ["gpt-3.5-turbo", "gpt-4-turbo"], key="model_selector_sidebar")
    
    apply_theme(st.session_state.theme)
    st.divider()

    projects = load_projects()
    project_list = sorted(list(projects.keys()))
    
    # UNIQUE KEY 3: main_unit_dropdown
    selected_unit_option = st.selectbox("📂 Select Unit:", ["Select..."] + project_list, key="main_unit_dropdown")
    
    if selected_unit_option != "Select...":
        st.markdown(f"**Action for: {selected_unit_option}**")
        col_open, col_delete = st.columns(2)
        
        with col_open:
            # UNIQUE KEY 4: btn_open_unit
            if st.button("🚀 OPEN", type="primary", use_container_width=True, key="btn_open_unit"):
                st.session_state.current_project = selected_unit_option
                project_path = projects[selected_unit_option]['path']
                st.session_state.vector_store = load_vector_db(project_path)
                st.session_state.chat_history = load_chat_history(project_path)
                st.toast(f"Unit Loaded: {selected_unit_option}")
                st.rerun()

        with col_delete:
            # UNIQUE KEY 5: btn_delete_unit
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
                    st.error("Could not delete. Folder might be locked.")

    with st.expander("➕ Create New Unit"):
        with st.form("create_unit_form_sidebar"):
            new_unit_name = st.text_input("Unit Name")
            # UNIQUE KEY 6: form_submit_create
            if st.form_submit_button("Create") and new_unit_name:
                create_project(new_unit_name)
                st.success(f"Created {new_unit_name}!")
                st.rerun()

    st.divider()
    st.markdown("### 🎧 Study Playlist")
    # UNIQUE KEY 7: music_player_radio
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
    st.markdown("""<div style="text-align: center; opacity: 0.7; font-size: 0.8em; margin-top: 20px;">Architect and Developer<br><strong>IMBEKA MUSA</strong></div>""", unsafe_allow_html=True)

# --- 6. MAIN CONTENT ---
if st.session_state.current_project and st.session_state.current_project in projects:
    project_data = projects[st.session_state.current_project]
    st.title(f"📚 {st.session_state.current_project}")
    
    tab_upload, tab_images, tab_notes, tab_map, tab_chat, tab_quiz, tab_research = st.tabs([
        "📂 Upload & Input", "🖼️ Image Analysis", "📝 Notes & Report", "🗺️ Mind Map", "💬 AI Chat", "🎓 Interactive Quiz", "🔍 Research (ArXiv)"
    ])

    with tab_upload:
        st.info(f"Currently using model: **{st.session_state.model_choice}**")
        # UNIQUE KEY 8: input_method_selector
        input_method = st.radio("Select Input Method:", ["📄 Upload File", "📋 Paste Text", "🎥 YouTube Video"], horizontal=True, key="input_method_selector")
        doc_data = None
        
        if input_method == "📄 Upload File":
            # UNIQUE KEY 9: main_file_uploader
            uploaded_file = st.file_uploader("Choose file...", type=["pdf", "docx", "txt"], key="main_file_uploader")
            if uploaded_file:
                save_path = os.path.join(project_data['path'], uploaded_file.name)
                with open(save_path, "wb") as f: f.write(uploaded_file.getbuffer())
                # UNIQUE KEY 10: btn_analyze_file
                if st.button("🧠 Deep Analyze File", key="btn_analyze_file"):
                    with st.spinner("Processing..."): doc_data = process_document(save_path)

        elif input_method == "📋 Paste Text":
            # UNIQUE KEY 11: text_paste_area
            pasted_text = st.text_area("Paste notes:", height=300, key="text_paste_area")
            # UNIQUE KEY 12: btn_analyze_text
            if pasted_text and st.button("🧠 Analyze Text", key="btn_analyze_text"):
                 from langchain.text_splitter import RecursiveCharacterTextSplitter
                 text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
                 chunks = text_splitter.split_text(pasted_text)
                 doc_data = {"filename": "manual_notes.txt", "full_text": pasted_text, "chunks": chunks, "chunk_count": len(chunks)}

        elif input_method == "🎥 YouTube Video":
            # UNIQUE KEY 13: youtube_url_input
            video_url = st.text_input("Paste YouTube Link:", key="youtube_url_input")
            # UNIQUE KEY 14: btn_analyze_video
            if video_url and st.button("🧠 Analyze Video", key="btn_analyze_video"):
                with st.spinner("Fetching transcript..."):
                    doc_data = process_video(video_url)

        if doc_data:
            summary = generate_deep_summary(doc_data['chunks'], st.session_state.model_choice)
            mm_data = generate_mind_map(doc_data['chunks'][0], st.session_state.model_choice)
            vector_store = create_vector_db(doc_data['chunks'], save_path=project_data['path'])
            st.session_state.vector_store = vector_store
            st.session_state.last_summary = summary
            st.session_state.last_mm = mm_data
            st.success("✅ Memory Updated.")

    with tab_images:
        st.subheader("🖼️ Visual Study Assistant")
        # UNIQUE KEY 15: image_uploader_tab
        uploaded_image = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'], key="image_uploader_tab")
        if uploaded_image:
            st.image(uploaded_image, width=500)
            # UNIQUE KEY 16: btn_analyze_image
            if st.button("🧠 Extract Knowledge", key="btn_analyze_image"):
                st.info("Analysis simulated (Enable Vision API to activate).")

    with tab_notes:
        col_scratchpad, col_report = st.columns(2)
        with col_scratchpad:
            st.subheader("📝 Your Scratchpad")
            # UNIQUE KEY 17: scratchpad_text_area
            user_notes = st.text_area("Type notes...", value=project_data.get("notes", ""), height=500, key="scratchpad_text_area")
            # UNIQUE KEY 18: btn_save_notes
            if st.button("💾 Save Notes", key="btn_save_notes"):
                update_project_notes(st.session_state.current_project, user_notes)
                st.toast("Notes saved successfully!")
        with col_report:
            st.subheader("📑 AI Executive Report")
            if st.session_state.last_summary: st.markdown(st.session_state.last_summary)
            else: st.info("No analysis generated yet.")

    with tab_map:
        st.subheader("🗺️ Knowledge Graph")
        if st.session_state.last_mm:
            from streamlit_agraph import agraph, Node, Edge, Config
            nodes, edges, seen_ids = [], [], set()
            for node in st.session_state.last_mm.get("nodes", []):
                if node["id"] not in seen_ids:
                    nodes.append(Node(id=node["id"], label=node["id"], size=25, shape="dot", color="#FF4B4B"))
                    seen_ids.add(node["id"])
            for edge in st.session_state.last_mm.get("edges", []):
                if edge["from"] in seen_ids and edge["to"] in seen_ids:
                    edges.append(Edge(source=edge["from"], target=edge["to"], color="#E0E0E0"))
            config = Config(width=None, height=600, directed=True, physics=True, hierarchical=False)
            if nodes: agraph(nodes=nodes, edges=edges, config=config)
            else: st.warning("Mind map empty.")
        else: st.info("Analyze a document first.")

    with tab_chat:
        st.subheader("💬 Chat with your Unit")
        # UNIQUE KEY 19: audio_chat_input
        audio_input = st.audio_input("🎙️ Speak", key="audio_chat_input")
        if audio_input: user_query = transcribe_audio(audio_input)
        else: 
            # UNIQUE KEY 20: text_chat_input
            user_query = st.chat_input("Type here...", key="text_chat_input")

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

    with tab_quiz:
        st.subheader("🎓 Test Your Knowledge")
        # UNIQUE KEY 21: btn_generate_quiz
        if st.button("🎲 Generate Quiz", key="btn_generate_quiz"):
            if st.session_state.last_summary:
                with st.spinner("Drafting..."):
                    st.session_state.last_quiz = generate_quiz(st.session_state.last_summary, st.session_state.model_choice)
            else: st.warning("Analyze document first.")
        
        if st.session_state.last_quiz:
            for i, question in enumerate(st.session_state.last_quiz):
                st.markdown(f"**Q{i+1}: {question['question']}**")
                # UNIQUE KEY 22 (Dynamic): quiz_radio_{i}
                answer = st.radio(f"Select Answer:", question['options'], key=f"quiz_radio_{i}")
                # UNIQUE KEY 23 (Dynamic): btn_check_quiz_{i}
                if st.button(f"Check {i+1}", key=f"btn_check_quiz_{i}"):
                    if answer == question['answer']: st.success("✅ Correct!")
                    else: st.error(f"❌ Wrong. Correct: {question['answer']}")
                st.divider()

    with tab_research:
        st.subheader("🔎 Research (ArXiv)")
        # UNIQUE KEY 24: research_topic_input
        research_topic = st.text_input("Enter topic:", key="research_topic_input")
        # UNIQUE KEY 25: btn_search_arxiv
        if st.button("Search Papers", key="btn_search_arxiv"):
            with st.spinner("Searching..."):
                results = search_arxiv_papers(research_topic)
                for result in results:
                    with st.expander(f"📄 {result['title']}"):
                        st.markdown(f"**Abstract:** {result['summary']}")
                        st.markdown(f"[📥 Download PDF]({result['pdf_url']})")

elif st.session_state.current_project is None:
    st.markdown("## 👋 Welcome to MindForge AI")
    st.info("👈 **Start Here:** Select a Unit from the sidebar and click 'ROCKET OPEN'.")