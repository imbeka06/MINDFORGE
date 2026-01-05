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

# Helper Functions
def save_chat_history(project_path, history):
    file_path = os.path.join(project_path, "chat_history.json")
    with open(file_path, "w") as f: json.dump(history, f)

def load_chat_history(project_path):
    file_path = os.path.join(project_path, "chat_history.json")
    if os.path.exists(file_path):
        with open(file_path, "r") as f: return json.load(f)
    return []

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
    
    # Theme & Model
    col1, col2 = st.columns(2)
    with col1:
        selected_theme = st.selectbox("🎨 Theme", ["☀️ Light Mode", "🌙 Dark Mode", "🌊 Ocean Blue"], key="theme_final_fix")
        if selected_theme != st.session_state.theme:
            st.session_state.theme = selected_theme
            st.rerun()
    with col2:
        if "model_choice" not in st.session_state: st.session_state.model_choice = "gpt-3.5-turbo"
        st.session_state.model_choice = st.selectbox("🧠 Model", ["gpt-3.5-turbo", "gpt-4-turbo"], key="model_final_fix")
    
    apply_theme(st.session_state.theme)
    st.divider()

    # --- UNIT SELECTION & DELETION ---
    projects = load_projects()
    project_list = sorted(list(projects.keys()))
    
    # We use st.selectbox without a default to ensure a fresh choice
    selected_unit = st.selectbox(
        "📂 Unit Selector:", 
        ["Select..."] + project_list, 
        key="unit_dropdown_final_fix"
    )
    
    if selected_unit != "Select...":
        st.markdown(f"**Target: {selected_unit}**")
        c1, c2 = st.columns(2)
        
        with c1:
            if st.button("🚀 OPEN", type="primary", use_container_width=True, key="btn_open_fix"):
                st.session_state.current_project = selected_unit
                path = projects[selected_unit]['path']
                st.session_state.vector_store = load_vector_db(path)
                st.session_state.chat_history = load_chat_history(path)
                st.rerun()

        with c2:
            if st.button("🗑️ DELETE", type="secondary", use_container_width=True, key="btn_del_fix"):
                # 1. Execute deletion on disk
                delete_project(selected_unit)
                
                # 2. Complete Session Reset
                st.session_state.current_project = None
                st.session_state.vector_store = None
                st.session_state.chat_history = []
                st.session_state.last_summary = None
                st.session_state.last_mm = None
                st.session_state.last_quiz = None
                
                # 3. Toast notification and Hard Rerun to update the dropdown list
                st.toast(f"Deleted {selected_unit}")
                st.rerun() 

    st.divider()
    with st.expander("➕ Create New Unit"):
        with st.form("create_form_final_fix"):
            new_name = st.text_input("Unit Name")
            if st.form_submit_button("Create") and new_name:
                create_project(new_name)
                st.rerun()

    # MUSIC PLAYER
    st.divider()
    music = st.radio("Vibe", ["Off", "☕ Lofi", "🎻 Dark", "🎷 Jazz", "🥀 Lana", "🖤 Orgavsm"], key="music_final_fix")
    links = {
        "☕ Lofi": "https://www.youtube.com/watch?v=7ccH8u8fj8Y",
        "🎻 Dark": "https://www.youtube.com/watch?v=D9km3yXmR8k",
        "🎷 Jazz": "https://www.youtube.com/watch?v=e2A3_111fwc",
        "🥀 Lana": "https://www.youtube.com/watch?v=5XJNg8x89yo",
        "🖤 Orgavsm": "https://www.youtube.com/watch?v=ZHLL7dPIxPw"
    }
    if music != "Off": st.video(links[music])
    
    st.markdown("<div style='text-align:center;font-size:0.8em;opacity:0.7;margin-top:20px'>Architect and Developer<br><strong>IMBEKA MUSA</strong></div>", unsafe_allow_html=True)

# --- 5. MAIN CONTENT ---
if st.session_state.current_project and st.session_state.current_project in projects:
    p_data = projects[st.session_state.current_project]
    st.title(f"📚 {st.session_state.current_project}")
    
    tabs = st.tabs(["📂 Upload/Input", "📝 Notes", "🗺️ Map", "💬 Chat", "🎓 Quiz", "🔍 Research"])

    # TAB 1: UPLOAD
    with tabs[0]:
        st.info(f"Model: {st.session_state.model_choice}")
        input_method = st.radio("Method:", ["📄 File", "📋 Paste", "🎥 YouTube"], horizontal=True, key="method_fix")
        
        doc_data = None
        if input_method == "📄 File":
            f = st.file_uploader("Upload", type=["pdf", "docx", "txt"], key="file_up_fix")
            if f:
                path = os.path.join(p_data['path'], f.name)
                with open(path, "wb") as w: w.write(f.getbuffer())
                if st.button("🧠 Deep Analyze", key="analyze_f_fix"):
                    doc_data = process_document(path)
        
        elif input_method == "📋 Paste":
            raw_text = st.text_area("Paste text:", height=200, key="paste_fix")
            if raw_text and st.button("🧠 Analyze Text", key="analyze_t_fix"):
                 from langchain.text_splitter import RecursiveCharacterTextSplitter
                 chunks = RecursiveCharacterTextSplitter(chunk_size=2000).split_text(raw_text)
                 doc_data = {"filename": "manual.txt", "full_text": raw_text, "chunks": chunks, "chunk_count": len(chunks)}

        elif input_method == "🎥 YouTube":
            url = st.text_input("URL:", key="yt_fix")
            if url and st.button("Analyze Video", key="analyze_v_fix"):
                doc_data = process_video(url)

        if doc_data:
            st.session_state.last_summary = generate_deep_summary(doc_data['chunks'], st.session_state.model_choice)
            st.session_state.last_mm = generate_mind_map(doc_data['chunks'][0], st.session_state.model_choice)
            st.session_state.vector_store = create_vector_db(doc_data['chunks'], p_data['path'])
            st.success("Unit Memory updated!")

    # TAB 2: NOTES
    with tabs[1]:
        c1, c2 = st.columns(2)
        with c1:
            notes = st.text_area("Scratchpad", value=p_data.get("notes",""), height=400, key="notes_fix")
            if st.button("Save", key="save_fix"): update_project_notes(st.session_state.current_project, notes)
        with c2:
            st.subheader("Deep Insight Report")
            if st.session_state.last_summary: st.markdown(st.session_state.last_summary)

    # TAB 4: CHAT
    with tabs[3]:
        audio = st.audio_input("🎙️ Voice Question", key="voice_fix")
        q = transcribe_audio(audio) if audio else st.chat_input("Ask a question...", key="chat_fix")
        if q and st.session_state.vector_store:
            st.session_state.chat_history.append({"role": "user", "content": q})
            ans = get_chat_response(q, st.session_state.vector_store, st.session_state.model_choice)
            st.session_state.chat_history.append({"role": "assistant", "content": ans})
            save_chat_history(p_data['path'], st.session_state.chat_history)
            st.audio(text_to_speech(ans), format="audio/mp3")
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

    # TAB 5: QUIZ
    with tabs[4]:
        if st.button("Generate Mini-Quiz", key="quiz_fix_btn"):
            if st.session_state.last_summary:
                st.session_state.last_quiz = generate_quiz(st.session_state.last_summary, st.session_state.model_choice)
        if st.session_state.last_quiz:
            for i, q in enumerate(st.session_state.last_quiz):
                st.write(f"**Q{i+1}: {q['question']}**")
                ans = st.radio(f"Options {i}", q['options'], key=f"q_opt_fix_{i}")
                if st.button(f"Check {i+1}", key=f"q_chk_fix_{i}"):
                    if ans == q['answer']: st.success("Correct!")
                    else: st.error(f"Wrong. Correct: {q['answer']}")

    # TAB 6: RESEARCH
    with tabs[5]:
        topic = st.text_input("Enter Topic for ArXiv Search:", key="arxiv_fix")
        if st.button("Find Papers", key="arxiv_btn_fix"):
            for r in search_arxiv_papers(topic):
                with st.expander(f"📄 {r['title']}"):
                    st.write(r['summary'])
                    st.markdown(f"[📥 Download PDF]({r['pdf_url']})")

else:
    st.markdown("## 👋 Ready to study?")
    st.info("👈 Use the **Unit Selector** in the sidebar to Open or Delete a learning unit.")