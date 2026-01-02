import streamlit as st
import os
from dotenv import load_dotenv

# --- 1. SETUP ---
load_dotenv()

# Import Custom Modules
from project_manager import load_projects, create_project, update_project_notes
from pdf_processor import process_document, extract_text_from_pdf
from ai_engine import generate_summary, generate_mind_map, create_vector_db, get_chat_response, generate_quiz

# Page Config
st.set_page_config(page_title="MindForge AI", page_icon="🧠", layout="wide")

# API Key Check
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ OPENAI_API_KEY not found! Please check your .env file.")
    st.stop()

# --- 2. SESSION STATE ---
if "current_project" not in st.session_state:
    st.session_state.current_project = None
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_summary" not in st.session_state:
    st.session_state.last_summary = None
if "last_mm" not in st.session_state:
    st.session_state.last_mm = None
if "last_quiz" not in st.session_state:
    st.session_state.last_quiz = None

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
        # Reset memory when switching units
        st.session_state.vector_store = None 
        st.session_state.chat_history = []
        st.session_state.last_summary = None
        st.session_state.last_mm = None
        st.session_state.last_quiz = None
        st.rerun()

    st.divider()
    new_project_name = st.text_input("New Unit Name")
    if st.button("Create Unit"):
        if new_project_name:
            create_project(new_project_name)
            st.success(f"Created {new_project_name}!")
            st.rerun()

# --- 4. MAIN CONTENT ---
if st.session_state.current_project:
    project_data = projects[st.session_state.current_project]
    st.title(f"📚 Unit: {st.session_state.current_project}")
    
    # TABS
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📂 Files & AI", "📝 Notes", "🗺️ Mind Map", "💬 Chat with PDF", "🎓 Quiz"])

    # --- TAB 1: FILES & PROCESSING ---
    with tab1:
        st.subheader("Upload Material")
        uploaded_file = st.file_uploader("Upload PDF", type="pdf")
        
        if uploaded_file:
            save_path = os.path.join(project_data['path'], uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Saved {uploaded_file.name}")
            
            st.divider()
            if st.button("🧠 Analyze Document"):
                with st.spinner("Reading and Synthesizing..."):
                    doc_data = process_document(save_path)
                    
                    if doc_data:
                        # Generate AI Content
                        summary = generate_summary(doc_data['chunks'][0])
                        mm_data = generate_mind_map(doc_data['chunks'][0])
                        vector_store = create_vector_db(doc_data['chunks'])
                        
                        # Save to State
                        st.session_state.vector_store = vector_store
                        st.session_state.last_summary = summary
                        st.session_state.last_mm = mm_data
                        
                        st.success("Analysis Complete! Check the other tabs.")
                    else:
                        st.error("Could not process document.")

    # --- TAB 2: NOTES ---
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Scratchpad")
            notes = st.text_area("Notes", value=project_data.get("notes", ""), height=400)
            if st.button("Save Notes"):
                update_project_notes(st.session_state.current_project, notes)
                st.toast("Notes saved!")
        with col2:
            st.subheader("AI Summary")
            if st.session_state.last_summary:
                st.markdown(st.session_state.last_summary)
            else:
                st.info("Analyze a document in Tab 1 first.")

    # --- TAB 3: MIND MAP ---
    with tab3:
        st.subheader("Concept Map")
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
                st.warning("No concepts found to map.")
        else:
            st.info("Analyze a document in Tab 1 first.")

    # --- TAB 4: CHAT ---
    with tab4:
        st.subheader("Chat with your Document")
        if not st.session_state.vector_store:
            st.warning("Please Analyze a document in Tab 1 first.")
        else:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            
            if prompt := st.chat_input("Ask a question..."):
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = get_chat_response(prompt, st.session_state.vector_store)
                        st.markdown(response)
                
                st.session_state.chat_history.append({"role": "assistant", "content": response})

    # --- TAB 5: QUIZ (NEW) ---
    with tab5:
        st.subheader("Knowledge Check")
        if st.button("Generate New Quiz"):
            with st.spinner("Drafting questions..."):
                # Find the most recent PDF file in the project folder
                files = [f for f in os.listdir(project_data['path']) if f.endswith('.pdf')]
                if files:
                    doc_path = os.path.join(project_data['path'], files[0])
                    full_text = extract_text_from_pdf(doc_path)
                    
                    if full_text:
                        quiz_content = generate_quiz(full_text[:4000])
                        st.session_state.last_quiz = quiz_content
                    else:
                        st.error("Could not read text from file.")
                else:
                    st.error("No PDF files found in this unit. Upload one in Tab 1.")

        if st.session_state.last_quiz:
            st.markdown("### 📝 Practice Questions")
            st.markdown(st.session_state.last_quiz)
            with st.expander("Show Answers"):
                st.info("The answers are listed at the bottom of each question block above.")

else:
    st.info("👈 Select or Create a Unit to begin.")