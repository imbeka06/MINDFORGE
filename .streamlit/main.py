import streamlit as st
import os
import arxiv
from duckduckgo_search import DDGS
from project_manager import load_projects, create_project, update_project_notes

# --- Page Config ---
st.set_page_config(page_title="MindForge AI", page_icon="🧠", layout="wide")

# --- Session State Initialization ---
if "current_project" not in st.session_state:
    st.session_state.current_project = None

# --- Sidebar: Project Navigation ---
with st.sidebar:
    st.title("📂 My Learning Units")
    
    # Project Loader
    projects = load_projects()
    project_list = list(projects.keys())
    
    selected = st.selectbox(
        "Select a Unit:", 
        ["Select..."] + project_list,
        index=0 if not st.session_state.current_project else project_list.index(st.session_state.current_project) + 1 if st.session_state.current_project in project_list else 0
    )
    
    if selected != "Select..." and selected != st.session_state.current_project:
        st.session_state.current_project = selected
        st.rerun()

    st.divider()
    
    # Create New Project
    st.subheader("New Unit")
    new_project_name = st.text_input("Unit Name (e.g. Regression)")
    if st.button("Create Unit"):
        if new_project_name:
            success, msg = create_project(new_project_name)
            if success:
                st.success(f"Created {new_project_name}!")
                st.session_state.current_project = new_project_name
                st.rerun()
            else:
                st.error(msg)

# --- Main Area ---
if not st.session_state.current_project:
    # Dashboard View
    st.title("🧠 Welcome to MindForge AI")
    st.markdown("""
    ### Jump back into your learning:
    Select a unit from the sidebar or create a new one to begin.
    """)
    
    if projects:
        st.info(f"You have {len(projects)} active learning units.")
    else:
        st.warning("No learning units found. Create one to get started!")

else:
    # Workspace View (Persistence Enabled)
    project_data = projects[st.session_state.current_project]
    st.title(f"📚 Unit: {st.session_state.current_project}")
    
    # Tabs for Workflow
    tab1, tab2, tab3 = st.tabs(["📝 Workspace & Notes", "🔎 Research & ArXiv", "📂 Files"])

    # 1. Workspace Tab (Notes Persistence)
    with tab1:
        st.subheader("Study Notes")
        # Load existing notes
        current_notes = project_data.get("notes", "")
        
        # Text area that updates state
        new_notes = st.text_area(
            "Your Scratchpad (Auto-saved)", 
            value=current_notes, 
            height=300
        )
        
        if st.button("Save Notes"):
            update_project_notes(st.session_state.current_project, new_notes)
            st.toast("Notes saved successfully!")

    # 2. Research Tab (ArXiv & Search)
    with tab2:
        st.subheader("Find New Resources")
        search_col1, search_col2 = st.columns([1, 3])
        
        with search_col1:
            source_type = st.radio("Source:", ["ArXiv Papers", "General Web"])
        
        with search_col2:
            query = st.text_input("Search topic (e.g. 'Transformer Architecture')")
        
        if st.button("Search"):
            st.divider()
            if source_type == "ArXiv Papers":
                client = arxiv.Client()
                search = arxiv.Search(
                    query=query,
                    max_results=5,
                    sort_by=arxiv.SortCriterion.Relevance
                )
                
                for result in client.results(search):
                    with st.expander(f"📄 {result.title}"):
                        st.write(f"**Published:** {result.published.date()}")
                        st.write(f"**Summary:** {result.summary}")
                        st.markdown(f"[Download PDF]({result.pdf_url})")
                        if st.button(f"Add to Project resources", key=result.entry_id):
                            st.toast("Link saved (Simulation)") # Implementation in next phase

            elif source_type == "General Web":
                results = DDGS().text(query, max_results=5)
                for res in results:
                    with st.expander(f"🔗 {res['title']}"):
                        st.write(res['body'])
                        st.markdown(f"[Go to Site]({res['href']})")

    # 3. Files Tab
    with tab3:
        st.subheader("Uploaded Materials")
        st.write(f"Storage Path: `{project_data['path']}`")
        uploaded_file = st.file_uploader("Upload local PDF", type="pdf")
        if uploaded_file:
            # Save file to project folder
            save_path = os.path.join(project_data['path'], uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Saved {uploaded_file.name}")