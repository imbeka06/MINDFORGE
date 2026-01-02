import streamlit as st
import os
from dotenv import load_dotenv

# --- 1. SETUP ---
load_dotenv()

# Import Custom Modules
from project_manager import load_projects, create_project, update_project_notes
from pdf_processor import process_document, extract_text_from_pdf
from video_processor import process_video  # <--- NEW
from ai_engine import (
    generate_summary, generate_mind_map, create_vector_db, 
    get_chat_response, generate_quiz, 
    transcribe_audio, text_to_speech # <--- NEW IMPORTS
)

st.set_page_config(page_title="MindForge AI", page_icon="🧠", layout="wide")

# API Key Check
if not os.getenv("OPENAI_API_KEY"):
    st.error("⚠️ OPENAI_API_KEY not found! Check your .env file.")
    st.stop()

# --- 2. SESSION STATE ---
if "current_project" not in st.session_state: st.session_state.current_project = None
if "vector_store" not in st.session_state: st.session_state.vector_store = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "last_summary" not in st.session_state: st.session_state.last_summary = None
if "last_mm" not in st.session_state: st.session_state.last_mm = None
if "last_quiz" not in st.session_state: st.session_state.last_quiz = None

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("📂 Learning Units")
    projects = load_projects()
    project_list = list(projects.keys())
    
    selected = st.selectbox(
        "Select Unit:", 
        ["Select..."] + project_list,
        index=0 if not st.session_state.current_project else project_list.index(st.session_state.current_project) + 1 if st.session_state.current_project in project_list else 0
    )
    
    if selected != "Select..." and selected != st.session_state.current_project:
        st.session_state.current_project = selected
        st.session_state.vector_store = None 
        st.session_state.chat_history = []
        st.session_state.last_summary = None
        st.session_state.last_mm = None
        st.session_state.last_quiz = None
        st.rerun()

    st.divider()
    if st.button("➕ Create New Unit"):
        new_name = st.text_input("Unit Name", "New Unit")
        if new_name and new_name != "New Unit":
            create_project(new_name)
            st.success(f"Created {new_name}!")
            st.rerun()

# --- 4. MAIN CONTENT ---
if st.session_state.current_project:
    project_data = projects[st.session_state.current_project]
    st.title(f"📚 Unit: {st.session_state.current_project}")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📂 Files & AI", "📝 Notes", "🗺️ Mind Map", "💬 Chat (Voice)", "🎓 Quiz"])

    # --- TAB 1: FILES (PDF & VIDEO) ---
    with tab1:
        st.subheader("Add Learning Material")
        
        # Choice: PDF or YouTube
        upload_type = st.radio("Source Type:", ["📄 PDF Document", "🎥 YouTube Video"], horizontal=True)
        
        doc_data = None
        
        if upload_type == "📄 PDF Document":
            uploaded_file = st.file_uploader("Upload PDF", type="pdf")
            if uploaded_file:
                save_path = os.path.join(project_data['path'], uploaded_file.name)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"Saved PDF: {uploaded_file.name}")
                
                if st.button("🧠 Analyze PDF"):
                    with st.spinner("Processing PDF..."):
                        doc_data = process_document(save_path)

        elif upload_type == "🎥 YouTube Video":
            video_url = st.text_input("Paste YouTube Link:")
            if video_url and st.button("🧠 Analyze Video"):
                with st.spinner("Downloading Transcript..."):
                    doc_data = process_video(video_url)
                    if not doc_data:
                        st.error("Could not fetch transcript. Video might not have captions.")

        # Common AI Processing for both PDF and Video
        if doc_data:
            summary = generate_summary(doc_data['chunks'][0])
            mm_data = generate_mind_map(doc_data['chunks'][0])
            vector_store = create_vector_db(doc_data['chunks'])
            
            st.session_state.vector_store = vector_store
            st.session_state.last_summary = summary
            st.session_state.last_mm = mm_data
            st.success("Analysis Complete! Check tabs.")

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
            if st.session_state.last_summary:
                st.markdown(st.session_state.last_summary)
            else:
                st.info("Analyze content in Tab 1 first.")

    # --- TAB 3: MIND MAP ---
    with tab3:
        if st.session_state.last_mm:
            from streamlit_agraph import agraph, Node, Edge, Config
            nodes = []
            edges = []
            seen_ids = set()
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
            if nodes:
                agraph(nodes=nodes, edges=edges, config=config)
            else:
                st.warning("No concepts mapped.")
        else:
            st.info("Analyze content first.")

    # --- TAB 4: CHAT (VOICE ENABLED) ---
    with tab4:
        st.subheader("Chat with your Content")
        
        # 1. Voice Input (New)
        audio_val = st.audio_input("🎙️ Record Voice Question")
        
        if audio_val:
            # Transcribe
            with st.spinner("Listening..."):
                transcription = transcribe_audio(audio_val)
                if transcription:
                    st.info(f"You said: '{transcription}'")
                    # Auto-submit as prompt
                    prompt = transcription
                else:
                    prompt = None
        else:
            prompt = st.chat_input("Or type your question...")

        if not st.session_state.vector_store:
            st.warning("Please Analyze content in Tab 1 first.")
        
        elif prompt:
            # User Message
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # AI Response
            with st.spinner("Thinking..."):
                response_text = get_chat_response(prompt, st.session_state.vector_store)
            
            st.session_state.chat_history.append({"role": "assistant", "content": response_text})
            
            # Text-to-Speech Generation
            audio_response = text_to_speech(response_text)
        
        # Display History
        for i, msg in enumerate(st.session_state.chat_history):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                # Play audio for the latest assistant message
                if msg["role"] == "assistant" and i == len(st.session_state.chat_history) - 1:
                     if 'audio_response' in locals() and audio_response:
                         st.audio(audio_response, format="audio/mp3")

    # --- TAB 5: QUIZ ---
    with tab5:
        if st.button("Generate New Quiz"):
            with st.spinner("Drafting..."):
                # Use whatever text is in the first chunk of the vector store
                if st.session_state.vector_store:
                     # Hack: we re-analyze the last processed chunk stored in memory would be better,
                     # but for MVP we will assume the user just analyzed something.
                     # We will pull from the document logic in a real app, but here:
                     if st.session_state.last_summary: 
                         # Use the summary context to generate quiz if full text isn't handy
                         # Ideally, we pass text. For now, let's ask user to re-analyze for quiz or use cached text.
                         st.info("Using recent context for quiz...")
                         # In this simple MVP, we need the text. 
                         # Let's prompt user to re-analyze if we lost the text variable.
                         pass
                
                # Simplified: Just grab the file again
                files = [f for f in os.listdir(project_data['path']) if f.endswith('.pdf')]
                if files:
                    doc_path = os.path.join(project_data['path'], files[0])
                    full_text = extract_text_from_pdf(doc_path)
                    st.session_state.last_quiz = generate_quiz(full_text[:4000])
                else:
                    # Check for video text? 
                    # For MVP, let's just say "Please upload PDF for Quiz" or expand logic later.
                    st.warning("Quiz currently supports PDFs. Video quiz coming soon.")

        if st.session_state.last_quiz:
            st.markdown(st.session_state.last_quiz)

else:
    st.info("👈 Select a Unit to begin.")