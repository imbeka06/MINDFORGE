import streamlit as st
import os
from project_manager import load_projects, create_project, update_project_notes
from pdf_processor import process_document
from ai_engine import generate_summary, generate_mind_map, create_vector_db, get_chat_response

# --- Page Config ---
st.set_page_config(page_title="MindForge AI", page_icon="🧠", layout="wide")

# --- Session State ---
if "current_project" not in st.session_state:
    st.session_state.current_project = None
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Sidebar ---
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
        # Clear chat memory when switching units
        st.session_state.vector_store = None 
        st.session_state.chat_history = []
        st.rerun()

    st.divider()
    new_project_name = st.text_input("New Unit Name")
    if st.button("Create Unit"):
        if new_project_name:
            create_project(new_project_name)
            st.success(f"Created {new_project_name}!")
            st.rerun()

# --- Main Area ---
if st.session_state.current_project:
    project_data = projects[st.session_state.current_project]
    st.title(f"📚 Unit: {st.session_state.current_project}")
    
    # TABS
    tab1, tab2, tab3, tab4 = st.tabs(["📂 Files & AI", "📝 Notes", "🗺️ Mind Map", "💬 Chat with PDF"])

    # --- TAB 1: FILES & PROCESSING ---
    with tab1:
        st.subheader("Upload Material")
        uploaded_file = st.file_uploader("Upload PDF", type="pdf")
        
        if uploaded_file:
            save_path = os.path.join(project_data['path'], uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Saved {uploaded_file.name}")
            
            if st.button("🧠 Analyze Document"):
                with st.spinner("Reading and Synthesizing..."):
                    # 1. Process PDF
                    doc_data = process_document(save_path)
                    
                    # 2. Generate Summary
                    summary = generate_summary(doc_data['chunks'][0]) # Summarize first chunk for MVP
                    
                    # 3. Generate Mind Map Data
                    mm_data = generate_mind_map(doc_data['chunks'][0])
                    
                    # 4. Create Chat Index
                    vector_store = create_vector_db(doc_data['chunks'])
                    st.session_state.vector_store = vector_store
                    
                    # Store results in session for other tabs
                    st.session_state['last_summary'] = summary
                    st.session_state['last_mm'] = mm_data
                    
                    st.success("Analysis Complete! Check the Summary, Mind Map, and Chat tabs.")

    # --- TAB 2: NOTES & SUMMARY ---
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Scratchpad")
            notes = st.text_area("Notes", value=project_data.get("notes", ""), height=400)
            if st.button("Save Notes"):
                update_project_notes(st.session_state.current_project, notes)
        with col2:
            st.subheader("AI Summary")
            if 'last_summary' in st.session_state:
                st.markdown(st.session_state['last_summary'])
            else:
                st.info("Upload and Analyze a document to see the summary here.")

    # --- TAB 3: MIND MAP ---
    with tab3:
        st.subheader("Concept Map")
        if 'last_mm' in st.session_state:
            st.json(st.session_state['last_mm']) # JSON for now, Visualization next
        else:
            st.info("Analyze a document to generate a map.")

    # --- TAB 4: CHAT ---
    with tab4:
        st.subheader("Chat with your Document")
        
        if st.session_state.vector_store is None:
            st.warning("Please upload and 'Analyze' a document in Tab 1 first.")
        else:
            # Chat Interface
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            
            if prompt := st.chat_input("Ask a question about the PDF..."):
                # User Message
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # AI Response
                with st.chat_message("assistant"):
                    response = get_chat_response(prompt, st.session_state.vector_store)
                    st.markdown(response)
                
                st.session_state.chat_history.append({"role": "assistant", "content": response})

else:
    st.info("👈 Select or Create a Unit to begin.")