import streamlit as st
import os
from dotenv import load_dotenv

# --- 1. SETUP ---
load_dotenv()

# Import Custom Modules
from project_manager import load_projects, create_project, update_project_notes
from pdf_processor import process_document, extract_text_from_pdf
from video_processor import process_video
from ai_engine import (
    generate_summary, generate_mind_map, create_vector_db, load_vector_db,
    get_chat_response, generate_quiz, 
    transcribe_audio, text_to_speech
)

st.set_page_config(page_title="MindForge AI", page_icon="🧠", layout="wide")

if not os.getenv("OPENAI_API_KEY"):
    st.error("⚠️ OPENAI_API_KEY not found! Check your .env file.")
    st.stop()

# --- 2. THEME MANAGER ---
def apply_custom_theme(theme_name):
    common_dark_css = """
        h1, h2, h3, h4, h5, h6, p, li, span, div, label { color: #E0E0E0 !important; }
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {
            background-color: #2E303E !important; color: #FFFFFF !important; border: 1px solid #4A4D5A;
        }
        .stSelectbox > div > div > div { background-color: #2E303E !important; color: #FFFFFF !important; }
        .stRadio > div { color: #E0E0E0 !important; }
    """
    if theme_name == "🌙 Dark Mode":
        st.markdown(f"<style>.stApp {{ background-color: #0E1117; }} [data-testid='stSidebar'] {{ background-color: #171923; }} {common_dark_css}</style>", unsafe_allow_html=True)
    elif theme_name == "🌊 Ocean Blue":
        st.markdown(f"<style>.stApp {{ background-color: #0F172A; }} [data-testid='stSidebar'] {{ background-color: #1E293B; }} h1, h2, h3 {{ color: #38BDF8 !important; }} .stButton>button {{ background-color: #3B82F6; color: white; }} {common_dark_css}</style>", unsafe_allow_html=True)

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
    
    # Theme
    selected_theme = st.selectbox("🎨 Theme:", ["☀️ Light Mode", "🌙 Dark Mode", "🌊 Ocean Blue"], index=["☀️ Light Mode", "🌙 Dark Mode", "🌊 Ocean Blue"].index(st.session_state.theme))
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()
    apply_custom_theme(st.session_state.theme)
    st.divider()

    # Project Manager
    projects = load_projects()
    project_list = list(projects.keys())
    
    selected = st.selectbox("📂 Select Unit:", ["Select..."] + project_list, index=0 if not st.session_state.current_project else project_list.index(st.session_state.current_project) + 1 if st.session_state.current_project in project_list else 0)
    
    # --- INTELLIGENT SWITCHING (MEMORY LOAD) ---
    if selected != "Select..." and selected != st.session_state.current_project:
        st.session_state.current_project = selected
        st.session_state.chat_history = []
        st.session_state.last_summary = None
        st.session_state.last_mm = None
        st.session_state.last_quiz = None
        
        # 🧠 TRY TO LOAD MEMORY
        project_path = projects[selected]['path']
        loaded_vs = load_vector_db(project_path)
        if loaded_vs:
            st.session_state.vector_store = loaded_vs
            st.toast(f"🧠 Memory loaded for {selected}!")
        else:
            st.session_state.vector_store = None
        st.rerun()

    # Create Unit
    with st.form("create_unit_form"):
        new_name = st.text_input("New Unit Name")
        if st.form_submit_button("➕ Create Unit") and new_name:
            create_project(new_name)
            st.success(f"Created {new_name}!")
            st.rerun()
    st.divider()

    # Music
    st.markdown("### 🎧 Study Playlist")
    music_choice = st.radio(
        "Vibe:", 
        ["Off", "☕ Lofi Girl", "🎻 Dark Academia", "🎷 60s Jazz/Soul", "🥀 Lana Del Rey", "🖤 Orgavsm"], 
        index=0
    )
    
    if music_choice == "☕ Lofi Girl": st.video("https://www.youtube.com/watch?v=7ccH8u8fj8Y")
    elif music_choice == "🎻 Dark Academia": st.video("https://www.youtube.com/watch?v=D9km3yXmR8k")
    elif music_choice == "🎷 60s Jazz/Soul": st.video("https://www.youtube.com/watch?v=e2A3_111fwc")
    elif music_choice == "🥀 Lana Del Rey": st.video("https://www.youtube.com/watch?v=5XJNg8x89yo")
    elif music_choice == "🖤 Orgavsm": st.video("https://www.youtube.com/watch?v=ZHLL7dPIxPw")
    
    st.divider()
    
    st.markdown("<div style='text-align: center; opacity: 0.7; font-size: 0.8em;'>Architect and Developer<br><strong>IMBEKA MUSA</strong></div>", unsafe_allow_html=True)

# --- 5. MAIN CONTENT ---
if st.session_state.current_project:
    project_data = projects[st.session_state.current_project]
    st.title(f"📚 {st.session_state.current_project}")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📂 Upload", "📝 Notes", "🗺️ Mind Map", "💬 Chat (Voice)", "🎓 Quiz"])

    # --- TAB 1: FILES ---
    with tab1:
        st.info("Upload materials to generate knowledge.")
        upload_type = st.radio("Source:", ["📄 PDF Document", "🎥 YouTube Video"], horizontal=True)
        doc_data = None
        
        if upload_type == "📄 PDF Document":
            uploaded_file = st.file_uploader("Upload PDF", type="pdf")
            if uploaded_file:
                save_path = os.path.join(project_data['path'], uploaded_file.name)
                with open(save_path, "wb") as f: f.write(uploaded_file.getbuffer())
                st.success(f"Saved: {uploaded_file.name}")
                if st.button("🧠 Analyze PDF"):
                    with st.spinner("Processing..."): doc_data = process_document(save_path)

        elif upload_type == "🎥 YouTube Video":
            video_url = st.text_input("Paste Link:")
            if video_url and st.button("🧠 Analyze Video"):
                with st.spinner("Fetching Transcript..."):
                    doc_data = process_video(video_url)
                    if not doc_data: st.error("No captions found.")

        if doc_data:
            summary = generate_summary(doc_data['chunks'][0])
            mm_data = generate_mind_map(doc_data['chunks'][0])
            # 🧠 CREATE AND SAVE MEMORY HERE
            vector_store = create_vector_db(doc_data['chunks'], save_path=project_data['path'])
            
            st.session_state.vector_store = vector_store
            st.session_state.last_summary = summary
            st.session_state.last_mm = mm_data
            st.success("Analysis Complete! Memory Saved.")

    # --- TAB 2: NOTES ---
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Scratchpad")
            notes = st.text_area("Notes", value=project_data.get("notes", ""), height=400)
            if st.button("Save Notes"):
                update_project_notes(st.session_state.current_project, notes)
                st.toast("Saved!")
        with col2:
            st.subheader("AI Summary")
            if st.session_state.last_summary: st.markdown(st.session_state.last_summary)
            else: st.info("No analysis yet.")

    # --- TAB 3: MIND MAP ---
    with tab3:
        if st.session_state.last_mm:
            from streamlit_agraph import agraph, Node, Edge, Config
            nodes, edges, seen_ids = [], [], set()
            data = st.session_state.last_mm
            if "nodes" in data:
                for node in data["nodes"]:
                    if node["id"] not in seen_ids:
                        nodes.append(Node(id=node["id"], label=node["id"], size=25, shape="dot", color="#FF4B4B"))
                        seen_ids.add(node["id"])
            if "edges" in data:
                for edge in data["edges"]:
                    if edge["from"] in seen_ids and edge["to"] in seen_ids:
                        edges.append(Edge(source=edge["from"], target=edge["to"], color="#31333F"))
            config = Config(width=None, height=500, directed=True, physics=True, hierarchical=False)
            if nodes: agraph(nodes=nodes, edges=edges, config=config)
        else: st.info("Analyze content to see map.")

    # --- TAB 4: CHAT ---
    with tab4:
        audio_val = st.audio_input("🎙️ Speak Question")
        if audio_val:
            transcription = transcribe_audio(audio_val)
            prompt = transcription if transcription else None
        else:
            prompt = st.chat_input("Type question...")

        if prompt and st.session_state.vector_store:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.spinner("Thinking..."):
                response_text = get_chat_response(prompt, st.session_state.vector_store)
            st.session_state.chat_history.append({"role": "assistant", "content": response_text})
            audio_response = text_to_speech(response_text)
        
        for i, msg in enumerate(st.session_state.chat_history):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant" and i == len(st.session_state.chat_history) - 1 and 'audio_response' in locals() and audio_response:
                     st.audio(audio_response, format="audio/mp3")

    # --- TAB 5: INTERACTIVE QUIZ ---
    with tab5:
        if st.button("Generate New Quiz"):
            with st.spinner("Drafting..."):
                files = [f for f in os.listdir(project_data['path']) if f.endswith('.pdf')]
                if files:
                    doc_path = os.path.join(project_data['path'], files[0])
                    full_text = extract_text_from_pdf(doc_path)
                    st.session_state.last_quiz = generate_quiz(full_text[:4000])
                else: st.warning("Upload a PDF first.")

        # RENDER INTERACTIVE QUIZ
        if st.session_state.last_quiz and isinstance(st.session_state.last_quiz, list):
            score = 0
            for i, q in enumerate(st.session_state.last_quiz):
                st.markdown(f"**Q{i+1}: {q['question']}**")
                user_choice = st.radio(f"Select Answer:", q['options'], key=f"q_{i}")
                
                if st.button(f"Check Answer {i+1}", key=f"btn_{i}"):
                    if user_choice == q['answer']:
                        st.success("Correct! 🎉")
                        score += 1
                    else:
                        st.error(f"Wrong. Correct answer: {q['answer']}")
                st.divider()
else:
    st.info("👈 Select or Create a Unit to begin.")