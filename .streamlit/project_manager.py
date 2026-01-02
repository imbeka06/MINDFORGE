import json
import os
import shutil

DATA_DIR = "data"
PROJECTS_FILE = os.path.join(DATA_DIR, "projects.json")

# Ensure data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def load_projects():
    """Load the list of existing projects/units."""
    if not os.path.exists(PROJECTS_FILE):
        return {}
    with open(PROJECTS_FILE, "r") as f:
        return json.load(f)

def save_projects(projects_data):
    """Save the projects state."""
    with open(PROJECTS_FILE, "w") as f:
        json.dump(projects_data, f, indent=4)

def create_project(name):
    """Create a new learning unit."""
    projects = load_projects()
    if name in projects:
        return False, "Project already exists."
    
    # Create a folder for this project's files
    project_path = os.path.join(DATA_DIR, name.replace(" ", "_"))
    os.makedirs(project_path, exist_ok=True)
    
    projects[name] = {
        "created_at": str(os.path.getctime(project_path)),
        "path": project_path,
        "notes": "",
        "resources": []  # List of saved PDFs or Links
    }
    save_projects(projects)
    return True, projects

def update_project_notes(name, notes):
    """Save the scratchpad notes for a project."""
    projects = load_projects()
    if name in projects:
        projects[name]["notes"] = notes
        save_projects(projects)