import streamlit as st
import os
from dotenv import load_dotenv

# --- 1. FORCE LOAD ENVIRONMENT VARIABLES FIRST ---
# This must happen before we try to use the key
load_dotenv()

# --- 2. IMPORT CUSTOM MODULES ---
from project_manager import load_projects, create_project, update_project_notes
from pdf_processor import process_document
from ai_engine import generate_summary, generate_mind_map, create_vector_db, get_chat_response

# --- 3. PAGE CONFIGURATION ---
st.set_page_config(page_title="MindForge AI", page_icon="🧠", layout="wide")

# --- 4. API KEY CHECK (CRITICAL) ---
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ OPENAI_API_KEY not found! Please check that your .env file exists and is named correctly.")
    st.stop()

# --- 5. SESSION STATE INITIALIZATION ---
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

# --- 6. SIDEBAR: PROJECT MANAGEMENT ---
with st.sidebar:
    st.title("📂 Learning Units")
    projects = load_projects()
    project_list = list(projects.keys())
    
    # Dropdown to select project
    selected = st.selectbox(
        "Select Unit:", 
        ["Select..."] + project_list,
        index=0 if not st.session_state.current_project else project_list.index(st.session_state.current_project) + 1 if st.session_state.current_project in project_list else 0
    )
    
    # Handle switching projects
    if selected != "Select..." and selected != st.session_state.current_project:
        st.session_state.current_project = selected
        # Reset memory when switching units
        st.session_state.vector_store = None 
        st.session_state.chat_history = []
        st.session_state.last_summary = None
        st.session_state.last_mm = None
        st.rerun()

    st.divider()
    
    # Create new project
    new_project_name = st.text_input("New Unit Name")
    if st.button("Create Unit"):
        if new_project_name:
            create_project(new_project_name)
            st.success(f"Created {new_project_name}!")
            st.rerun()

# --- 7. MAIN CONTENT AREA ---
if st.session_state.current_project:
    project_data = projects[st.session_state.current_project]
    st.title(f"📚 Unit: {st.session_state.current_project}")
    
    # Tabs for different features
    tab1, tab2, tab3, tab4 = st.tabs(["📂 Files & AI", "📝 Notes", "🗺️ Mind Map", "💬 Chat with PDF"])

    # --- TAB 1: FILES & AI PROCESSING ---
    with tab1:
        st.subheader("Upload Material")
        uploaded_file = st.file_uploader("Upload PDF", type="pdf")
        
        if uploaded_file:
            # Save the file locally
            save_path = os.path.join(project_data['path'], uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Saved {uploaded_file.name}")
            
            st.divider()
            
            # The "Brain" Button
            if st.button("🧠 Analyze Document"):
                with st.spinner("Reading and Synthesizing... (This may take a moment)"):
                    # 1. Process PDF text
                    doc_data = process_document(save_path)
                    
                    if doc_data:
                        # 2. AI Tasks
                        summary = generate_summary(doc_data['chunks'][0])
                        mm_data = generate_mind_map(doc_data['chunks'][0])
                        vector_store = create_vector_db(doc_data['chunks'])
                        
                        # 3. Store results in Session State
                        st.session_state.vector_store = vector_store
                        st.session_state.last_summary = summary
                        st.session_state.last_mm = mm_data
                        
                        st.success("Analysis Complete! Check the Summary and Chat tabs.")
                    else:
                        st.error("Could not process document. Is it a valid PDF?")

    # --- TAB 2: NOTES & SUMMARY ---
    with tab2:
        col1, col2 = st.columns(2)
        
        # Left: User Notes
        with col1:
            st.subheader("Scratchpad")
            notes = st.text_area("Notes", value=project_data.get("notes", ""), height=400)
            if st.button("Save Notes"):
                update_project_notes(st.session_state.current_project, notes)
                st.toast("Notes saved!")
        
        # Right: AI Summary
        with col2:
            st.subheader("AI Summary")
            if st.session_state.last_summary:
                st.markdown(st.session_state.last_summary)
            else:
                st.info("Upload and Analyze a document in Tab 1 to see the summary here.")

    
    # TAB 3: MIND MAP 
    
    with tab3:
        st.subheader("Concept Map")
        if st.session_state.last_mm:
            from streamlit_agraph import agraph, Node, Edge, Config

            nodes = []
            edges = []
            seen_ids = set()  # <--- NEW: This remembers what we've already added
            
            data = st.session_state.last_mm
            
            # Create Nodes (The bubbles)
            if "nodes" in data:
                for node in data["nodes"]:
                    # CHECK: Have we seen this ID before?
                    if node["id"] not in seen_ids:
                        nodes.append(Node(
                            id=node["id"], 
                            label=node["id"], 
                            size=25, 
                            shape="dot",
                            color="#FF4B4B"
                        ))
                        # Mark as seen so we don't add it again
                        seen_ids.add(node["id"])
            
            # Create Edges (The connecting lines)
            if "edges" in data:
                for edge in data["edges"]:
                    # Safety Check: Ensure both ends of the line actually exist
                    if edge["from"] in seen_ids and edge["to"] in seen_ids:
                        edges.append(Edge(
                            source=edge["from"], 
                            target=edge["to"], 
                            label=edge.get("label", ""),
                            color="#31333F"
                        ))

            config = Config(
                width=None, 
                height=500, 
                directed=True, 
                physics=True, 
                hierarchical=False
            )

            if nodes:
                agraph(nodes=nodes, edges=edges, config=config)
            else:
                st.info("No concepts found to map.")
        else:
            st.info("Analyze a document in Tab 1 to generate a map.")

    # --- TAB 4: CHAT WITH PDF ---
    with tab4:
        st.subheader("Chat with your Document")
        
        if st.session_state.vector_store is None:
            st.warning("Please upload and 'Analyze' a document in Tab 1 first.")
        else:
            # Display chat history
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            
            # Chat Input
            if prompt := st.chat_input("Ask a question about the PDF..."):
                # 1. Display User Message
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # 2. Generate and Display AI Response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = get_chat_response(prompt, st.session_state.vector_store)
                        st.markdown(response)
                
                # 3. Save Assistant Message
                st.session_state.chat_history.append({"role": "assistant", "content": response})

else:
    # Landing Page (No project selected)
    st.info("👈 Select a Unit from the sidebar or create a new one to begin.")