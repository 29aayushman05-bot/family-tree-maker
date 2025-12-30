import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
import json
from datetime import datetime


from components.node_manager import add_root_node, delete_node, add_child, add_sibling, add_spouse, edit_node, add_same_level
from utils.data_handler import initialize_tree, format_date_range
from utils.export_handler import export_to_json, export_to_pdf
from utils.storage_handler import save_to_browser, load_from_browser, clear_browser_storage


st.set_page_config(page_title="Family Tree Maker", layout="wide")


# Initialize
if 'tree_data' not in st.session_state:
    st.session_state.tree_data = initialize_tree()
    st.session_state.loaded_from_storage = False


# Load from browser storage ONCE on first run
if not st.session_state.loaded_from_storage:
    try:
        loaded_data = load_from_browser()
        if loaded_data and 'nodes' in loaded_data and 'edges' in loaded_data:
            st.session_state.tree_data = loaded_data
    except:
        pass
    st.session_state.loaded_from_storage = True


if 'selected_node' not in st.session_state:
    st.session_state.selected_node = None
if 'mode' not in st.session_state:
    st.session_state.mode = 'add'
if 'form_counter' not in st.session_state:
    st.session_state.form_counter = 0

# Initialize search state
if 'highlight_path' not in st.session_state:
    st.session_state.highlight_path = False
if 'highlighted_edges' not in st.session_state:
    st.session_state.highlighted_edges = []
if 'highlighted_node' not in st.session_state:
    st.session_state.highlighted_node = None


# Custom CSS - iOS Dark Mode (Refined + Fixed)
st.markdown("""
<style>
/* ---------- Hide Streamlit Branding ---------- */
# MainMenu {visibility: hidden;}
# footer {visibility: hidden;}
# header {visibility: hidden;}


            
      
            
/* =========================================================
   iOS-Inspired Dark Mode — Unified Canvas + Calm Accent
   ========================================================= */

/* ---------- Design Tokens ---------- */
:root {
    /* Canvas */
    --canvas-bg: #0a0a0a;

    /* Surfaces */
    --surface-1: rgba(255, 255, 255, 0.04);
    --surface-2: rgba(255, 255, 255, 0.07);
    --surface-hover: rgba(255, 255, 255, 0.10);

    /* Text */
    --text-primary: #ffffff;
    --text-secondary: #9a9aa0;

    /* Strokes (iOS-style separators) */
    --stroke-subtle: rgba(255, 255, 255, 0.08);
    --stroke-neutral: rgba(255, 255, 255, 0.18);

    /* Accent (used sparingly) */
    --accent: #0a84ff;
    --accent-soft: rgba(10, 132, 255, 0.35);

    /* Shadows */
    --shadow-soft: 0 2px 10px rgba(0, 0, 0, 0.45);
    --shadow-elevated: 0 6px 20px rgba(0, 0, 0, 0.55);

    /* Radius */
    --radius-sm: 10px;
    --radius-md: 12px;
    --radius-lg: 16px;

    /* Motion */
    --ease-ios: cubic-bezier(0.4, 0, 0.2, 1);
    --t-fast: 150ms var(--ease-ios);
    --t-smooth: 220ms var(--ease-ios);
}

/* ---------- System Font ---------- */
* {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text",
                 "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* ---------- Canvas Background Everywhere ---------- */
.stApp,
.main,
.block-container,
[data-testid="stSidebar"] {
    background-color: var(--canvas-bg);
    color: var(--text-primary);
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    border-right: 1px solid var(--stroke-subtle);
}

/* ---------- Headings ---------- */
h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary);
    font-weight: 600;
    letter-spacing: -0.01em;
    line-height: 1.3;
}

/* ---------- Text ---------- */
p, span, label {
    color: var(--text-primary);
    line-height: 1.6;
}

/* ---------- Buttons - Force Uniform Styling ---------- */
.stButton > button {
    background: var(--surface-1) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--stroke-subtle) !important;
    border-radius: var(--radius-md);
    padding: 10px 20px;
    font-size: 15px;
    font-weight: 500;
    transition: background-color var(--t-smooth),
                border-color var(--t-smooth),
                box-shadow var(--t-smooth);
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    min-height: 42px !important;
    height: 42px !important;
}

.stButton > button:hover {
    background: var(--surface-2) !important;
    border-color: var(--stroke-neutral) !important;
    box-shadow: var(--shadow-soft);
}

.stButton > button[kind="primary"],
.stButton > button[data-baseweb="button"][kind="primary"] {
    background: var(--accent) !important;
    border-color: transparent !important;
    color: #fff !important;
}

.stButton > button[kind="primary"]:hover {
    background: #409cff !important;
}

/* Button Spacing */
.stButton {
    margin-bottom: 8px;
}

/* Ensure buttons in columns have equal width and style */
[data-testid="column"] .stButton > button {
    width: 100%;
    background: var(--surface-1) !important;
    color: var(--text-primary) !important;
}

[data-testid="column"] .stButton > button:hover {
    background: var(--surface-2) !important;
}

/* ---------- Inputs ---------- */
.stTextInput input,
.stNumberInput input {
    background: var(--surface-1);
    color: var(--text-primary);
    border: 1px solid var(--stroke-subtle);
    border-radius: var(--radius-md);
    padding: 10px 14px;
    font-size: 15px;
    transition: border-color var(--t-fast),
                box-shadow var(--t-fast),
                background-color var(--t-fast);
}

.stTextInput input:focus,
.stNumberInput input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-soft);
    background: var(--surface-2);
    outline: none;
}

.stTextInput input::placeholder,
.stNumberInput input::placeholder {
    color: var(--text-secondary);
}

/* ---------- Selectbox (Fixed) ---------- */
.stSelectbox > div > div {
    background: var(--surface-1) !important;
    border: 1px solid var(--stroke-subtle) !important;
    border-radius: var(--radius-md) !important;
    transition: border-color var(--t-fast),
                background-color var(--t-fast);
}

.stSelectbox > div > div:hover {
    background: var(--surface-2) !important;
    border-color: var(--stroke-neutral) !important;
}

.stSelectbox [data-baseweb="select"] {
    background-color: transparent !important;
}

.stSelectbox [data-baseweb="select"] > div {
    background-color: transparent !important;
    color: var(--text-primary) !important;
}

.stSelectbox svg {
    fill: var(--text-secondary) !important;
}

[data-baseweb="popover"] {
    background: var(--surface-1) !important;
    border: 1px solid var(--stroke-subtle) !important;
    border-radius: var(--radius-md) !important;
}

[role="listbox"] {
    background: var(--surface-1) !important;
}

[role="option"] {
    background: transparent !important;
    color: var(--text-primary) !important;
    padding: 10px 14px !important;
}

[role="option"]:hover {
    background: var(--surface-hover) !important;
}

[aria-selected="true"][role="option"] {
    background: var(--surface-2) !important;
    color: var(--accent) !important;
}

/* ---------- File Uploader ---------- */
[data-testid="stFileUploader"] {
    background: var(--surface-1);
    border: 1px dashed var(--stroke-subtle);
    border-radius: var(--radius-md);
    padding: 20px;
    transition: background-color var(--t-fast),
                border-color var(--t-fast);
}

[data-testid="stFileUploader"]:hover {
    background: var(--surface-2);
    border-color: var(--accent);
}

/* ---------- Divider ---------- */
hr {
    border: none;
    border-top: 1px solid var(--stroke-subtle);
    margin: 24px 0;
}

/* ---------- Expanders ---------- */
.streamlit-expanderHeader {
    background: var(--surface-1);
    border: 1px solid var(--stroke-subtle);
    border-radius: var(--radius-md);
    padding: 12px 16px;
    transition: background-color var(--t-fast),
                border-color var(--t-fast);
}

.streamlit-expanderHeader:hover {
    background: var(--surface-2);
    border-color: var(--stroke-neutral);
}

/* ---------- Alerts ---------- */
.stAlert {
    background: var(--surface-1);
    border: 1px solid var(--stroke-subtle);
    border-radius: var(--radius-md);
    padding: 14px 16px;
    min-height: 50px !important;
    display: flex !important;
    align-items: center !important;
}

.stSuccess {
    background-color: rgba(48, 209, 88, 0.1);
    border: 1px solid rgba(48, 209, 88, 0.3);
}

.stInfo {
    background-color: rgba(10, 132, 255, 0.1);
    border: 1px solid rgba(10, 132, 255, 0.3);
}

.stError {
    background-color: rgba(255, 69, 58, 0.1);
    border: 1px solid rgba(255, 69, 58, 0.3);
}

.stWarning {
    background-color: rgba(255, 159, 10, 0.1);
    border: 1px solid rgba(255, 159, 10, 0.3);
}

/* ---------- Slider ---------- */
.stSlider [role="slider"] {
    background: var(--accent);
    box-shadow: var(--shadow-soft);
}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 1px solid var(--stroke-subtle);
}

.stTabs [data-baseweb="tab"] {
    color: var(--text-secondary);
    transition: color var(--t-fast),
                background-color var(--t-fast);
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-primary);
    background: var(--surface-1);
}

.stTabs [aria-selected="true"] {
    color: var(--accent);
    border-bottom: 2px solid var(--accent);
}

/* ---------- Dialog / Modal ---------- */
[data-testid="stDialog"] {
    background: var(--canvas-bg);
    border: 1px solid var(--stroke-subtle);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-elevated);
}

/* ---------- Captions ---------- */
[data-testid="stCaptionContainer"] {
    color: var(--text-secondary);
    font-size: 13px;
}

/* ---------- Scrollbar ---------- */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--canvas-bg);
}

::-webkit-scrollbar-thumb {
    background: var(--surface-2);
    border-radius: 4px;
    transition: background-color var(--t-fast);
}

::-webkit-scrollbar-thumb:hover {
    background: var(--surface-hover);
}

/* ---------- Focus ---------- */
*:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
}

/* ---------- Columns ---------- */
[data-testid="column"] {
    padding: 8px;
}

/* ---------- Block Container ---------- */
.block-container {
    padding-top: 3rem;
    padding-bottom: 3rem;
}

.main .block-container {
    background-color: transparent;
}

/* ---------- Labels ---------- */
label {
    color: var(--text-primary);
    font-weight: 500;
    font-size: 14px;
    margin-bottom: 6px;
}

/* ---------- Number Input Buttons ---------- */
.stNumberInput button {
    background: transparent;
    border: none;
    color: var(--text-secondary);
    transition: color var(--t-fast);
}

.stNumberInput button:hover {
    color: var(--text-primary);
}

/* ---------- Download Button ---------- */
.stDownloadButton > button {
    background: var(--surface-1) !important;
    border: 1px solid var(--stroke-subtle) !important;
}

.stDownloadButton > button:hover {
    background: var(--surface-2) !important;
    border-color: var(--accent) !important;
}
</style>
""", unsafe_allow_html=True)




st.title("Family Tree Maker")


# Function to reset form inputs
def reset_form():
    st.session_state.form_counter += 1


# ==================== SEARCH DIALOG (REMOVABLE BLOCK START) ====================
# DELETE THIS ENTIRE BLOCK TO REMOVE SEARCH FEATURE

# Search Dialog
@st.dialog("Search Family Tree", width="large")
def search_dialog():
    from utils.search_handler import search_nodes, find_path_to_node
    
    query = st.text_input(
        "Search for family member...", 
        placeholder="Type a name...",
        key="search_input",
        label_visibility="collapsed"
    )
    
    # Real-time filtering - starts from 1 character
    if query:
        results = search_nodes(st.session_state.tree_data, query)
        
        if results:
            st.write(f"**Found {len(results)} result(s):**")
            st.divider()
            
            for result in results:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{result['name']}**")
                        st.caption(f"{result['dates']} • Generation {result['level'] + 1}")
                    with col2:
                        if st.button("View", key=f"view_{result['id']}", use_container_width=True):
                            # Find path and highlight
                            path_edges = find_path_to_node(st.session_state.tree_data, result['id'])
                            st.session_state.highlighted_edges = path_edges
                            st.session_state.selected_node = result['id']
                            st.session_state.highlighted_node = result['id']
                            st.session_state.highlight_path = True
                            st.rerun()
                    st.divider()
        else:
            st.info("No results found. Try a different name.")
    else:
        st.caption("Start typing to search...")

# ==================== SEARCH DIALOG (REMOVABLE BLOCK END) ====================


# Sidebar controls
with st.sidebar:
    st.header("Controls")
    
    # Import JSON
    uploaded_file = st.file_uploader("Import Tree (JSON)", type=['json'], key=f"upload_{st.session_state.form_counter}")
    if uploaded_file:
        imported_data = json.load(uploaded_file)
        
        # Preserve positions and fixed flags if they exist
        for node in imported_data.get('nodes', []):
            if 'x' not in node:
                node['x'] = 0
            if 'y' not in node:
                node['y'] = 0
            if 'level' not in node:
                node['level'] = 0
            if 'fixed' not in node:
                node['fixed'] = False
        
        st.session_state.tree_data = imported_data
        save_to_browser(st.session_state.tree_data)
        st.success("Tree imported!")
        reset_form()
        st.rerun()
    
    st.divider()
    
    # Export options
    st.subheader("Export Options")
    col1, col2 = st.columns(2)
    
    with col1:
        json_data = export_to_json(st.session_state.tree_data)
        st.download_button(
            "JSON",
            data=json_data,
            file_name=f"tree_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        pdf_bytes = export_to_pdf(st.session_state.tree_data)
        st.download_button(
            "PDF",
            data=pdf_bytes,
            file_name=f"tree_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    
    st.divider()
    
    # Layout control
    if st.button("Reset Layout", help="Reset to automatic hierarchical layout", use_container_width=True):
        from components.layout_manager import apply_hierarchical_layout
        
        # Unfix all nodes before layout
        for node in st.session_state.tree_data['nodes']:
            if 'fixed' in node:
                node['fixed'] = False
        
        apply_hierarchical_layout(st.session_state.tree_data)
        save_to_browser(st.session_state.tree_data)
        st.success("✓ Layout reset!")
        st.rerun()
    
    if st.button("Clear Browser Cache", help="Clear saved tree from browser", use_container_width=True):
        clear_browser_storage()
        st.session_state.tree_data = initialize_tree()
        st.success("✓ Cache cleared!")
        st.rerun()
    
    # st.info("💡 **Tip:** Enter year (e.g., 1960) or full date (1960-05-15)")
    
    st.divider()
    
    # Node Management
    st.subheader("Manage Nodes")
    
    has_nodes = len(st.session_state.tree_data['nodes']) > 0
    
    if has_nodes:
        # Mode toggle
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Add Mode", use_container_width=True, 
                        type="primary" if st.session_state.mode == 'add' else "secondary"):
                st.session_state.mode = 'add'
                reset_form()
                st.rerun()
        
        with col2:
            if st.button("Edit Mode", use_container_width=True, 
                        type="primary" if st.session_state.mode == 'edit' else "secondary"):
                st.session_state.mode = 'edit'
                st.rerun()
        
        st.divider()
        
        # Node selector
        node_options = {}
        for node in st.session_state.tree_data['nodes']:
            if node.get('type') == 'person':
                birth = node.get('birth_date', node.get('date', ''))
                death = node.get('death_date', '')
                date_str = format_date_range(birth, death)
                display = f"{node['name']} ({date_str})" if date_str else node['name']
                node_options[node['id']] = display
        
        current_index = 0
        if st.session_state.selected_node and st.session_state.selected_node in node_options:
            current_index = list(node_options.keys()).index(st.session_state.selected_node)
        
        selected_id = st.selectbox(
            "Select Node",
            options=list(node_options.keys()),
            format_func=lambda x: node_options[x],
            index=current_index,
            key="node_selector"
        )
        
        st.session_state.selected_node = selected_id
        
        # Get selected node data
        selected_node_data = next((n for n in st.session_state.tree_data['nodes'] 
                                  if n['id'] == st.session_state.selected_node), None)
        
        st.divider()
        
        # EDIT MODE
        if st.session_state.mode == 'edit' and selected_node_data:
            st.write(f"**Editing: {selected_node_data['name']}**")
            
            edit_name = st.text_input("Name", value=selected_node_data['name'], key="edit_name")
            
            # Birth and Death date fields
            edit_birth = st.text_input(
                "Birth Date/Year", 
                value=selected_node_data.get('birth_date', selected_node_data.get('date', '')), 
                key="edit_birth",
                placeholder="e.g., 1960 or 1960-05-15"
            )
            edit_death = st.text_input(
                "Death Date/Year", 
                value=selected_node_data.get('death_date', ''), 
                key="edit_death",
                placeholder="e.g., 2020 or leave blank"
            )
            
            edit_photo = st.file_uploader("New Photo", type=['png', 'jpg', 'jpeg'], key="edit_photo")
            
            st.divider()
            
            # Position Controls
            st.write("**Adjust Position:**")
            
            current_x = int(selected_node_data.get('x', 400))
            current_y = int(selected_node_data.get('y', 50))
            generation = selected_node_data.get('level', 0)
            
            st.caption(f"Generation: {generation} | Current: X={current_x}, Y={current_y}")
            
            # Horizontal Slider (Primary Control) - ALLOWS NEGATIVE
            new_x = st.slider(
                "Horizontal Position (Left ← → Right)",
                min_value=-1500,
                max_value=1500,
                value=current_x,
                step=50,
                key="position_slider",
                help="Drag to adjust horizontal position (negative = far left)"
            )
            
            # Show if position changed
            if new_x != current_x:
                st.info(f"Position will change from {current_x} to {new_x}")
            
            # Advanced Controls (Hidden) - ALLOWS NEGATIVE Y
            with st.expander("Advanced - Fine Tune Position"):
                st.caption("For precise control, adjust X and Y coordinates directly (negative values allowed)")
                col_x, col_y = st.columns(2)
                with col_x:
                    fine_x = st.number_input(
                        "X Position", 
                        value=new_x, 
                        step=10, 
                        key="fine_x",
                        help="Negative = left, Positive = right"
                    )
                with col_y:
                    fine_y = st.number_input(
                        "Y Position", 
                        value=current_y, 
                        step=10, 
                        key="fine_y",
                        help="Negative = up, Positive = down"
                    )
                
                if st.button("Apply Fine Adjustments", key="apply_fine"):
                    selected_node_data['x'] = fine_x
                    selected_node_data['y'] = fine_y
                    selected_node_data['fixed'] = True
                    save_to_browser(st.session_state.tree_data)
                    st.success("✓ Position updated!")
                    st.rerun()
            
            st.divider()
            
            # Save Changes Button
            if st.button("Save Changes", use_container_width=True):
                if edit_name:
                    edit_node(st.session_state.tree_data, st.session_state.selected_node, 
                             edit_name, edit_birth, edit_death, edit_photo)
                    
                    # Update position from slider if changed
                    if new_x != current_x:
                        selected_node_data['x'] = new_x
                        selected_node_data['fixed'] = True
                    
                    save_to_browser(st.session_state.tree_data)
                    st.success(f"✓ Updated {edit_name}!")
                    st.rerun()
            
            if st.button("Delete This Node", use_container_width=True):
                node_name = selected_node_data['name']
                delete_node(st.session_state.tree_data, st.session_state.selected_node)
                st.session_state.selected_node = None
                save_to_browser(st.session_state.tree_data)
                st.success(f"✓ Deleted {node_name}!")
                st.rerun()
        
        # ADD MODE
        elif st.session_state.mode == 'add':
            st.write(f"**Adding to: {selected_node_data['name'] if selected_node_data else 'Selected'}**")
            
            add_name = st.text_input("Name", placeholder="Enter name", key=f"add_name_{st.session_state.form_counter}")
            
            # Birth and Death date fields
            add_birth = st.text_input(
                "Birth Date/Year", 
                key=f"add_birth_{st.session_state.form_counter}",
                placeholder="e.g., 1960 or 1960-05-15"
            )
            add_death = st.text_input(
                "Death Date/Year", 
                key=f"add_death_{st.session_state.form_counter}",
                placeholder="e.g., 2020 or leave blank"
            )
            
            add_photo = st.file_uploader("Photo", type=['png', 'jpg', 'jpeg'], key=f"add_photo_{st.session_state.form_counter}")
            
            st.write("**Add as:**")
            
            # Row 1: Child and Sibling
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Child", use_container_width=True, key="btn_child"):
                    if add_name and st.session_state.selected_node:
                        add_child(st.session_state.tree_data, st.session_state.selected_node, 
                                add_name, add_birth, add_death, add_photo)
                        save_to_browser(st.session_state.tree_data)
                        st.success(f"✓ Added child {add_name}!")
                        reset_form()
                        st.rerun()
                    else:
                        st.error("⚠ Enter name!")
            
            with col2:
                if st.button("Sibling", use_container_width=True, key="btn_sibling"):
                    if add_name and st.session_state.selected_node:
                        add_sibling(st.session_state.tree_data, st.session_state.selected_node, 
                                add_name, add_birth, add_death, add_photo)
                        save_to_browser(st.session_state.tree_data)
                        st.success(f"✓ Added sibling {add_name}!")
                        reset_form()
                        st.rerun()
                    else:
                        st.error("⚠ Enter name!")
            
            # Row 2: Spouse and Same Level
            col3, col4 = st.columns(2)
            
            with col3:
                if st.button("Spouse", use_container_width=True, key="btn_spouse"):
                    if add_name and st.session_state.selected_node:
                        add_spouse(st.session_state.tree_data, st.session_state.selected_node, 
                                add_name, add_birth, add_death, add_photo)
                        save_to_browser(st.session_state.tree_data)
                        st.success(f"✓ Added spouse {add_name}!")
                        reset_form()
                        st.rerun()
                    else:
                        st.error("⚠ Enter name!")
            
            with col4:
                if st.button("Same Level", use_container_width=True, key="btn_same_level"):
                    if add_name and st.session_state.selected_node:
                        add_same_level(st.session_state.tree_data, st.session_state.selected_node, 
                                    add_name, add_birth, add_death, add_photo)
                        save_to_browser(st.session_state.tree_data)
                        st.success(f"✓ Added {add_name} at same level!")
                        reset_form()
                        st.rerun()
                    else:
                        st.error("⚠ Enter name!")

    
    else:
        # No nodes yet - only root option
        st.write("**Create Root Node:**")
        
        root_name = st.text_input("Name", placeholder="Enter name", key=f"root_name_{st.session_state.form_counter}")
        
        # Birth and Death date fields
        root_birth = st.text_input(
            "Birth Date/Year", 
            key=f"root_birth_{st.session_state.form_counter}",
            placeholder="e.g., 1960 or 1960-05-15"
        )
        root_death = st.text_input(
            "Death Date/Year", 
            key=f"root_death_{st.session_state.form_counter}",
            placeholder="e.g., 2020 or leave blank"
        )
        
        root_photo = st.file_uploader("Photo", type=['png', 'jpg', 'jpeg'], key=f"root_photo_{st.session_state.form_counter}")
        
        if st.button("Add Root Node", use_container_width=True):
            if root_name:
                add_root_node(st.session_state.tree_data, root_name, root_birth, root_death, root_photo)
                save_to_browser(st.session_state.tree_data)
                st.success(f"✓ Added {root_name}!")
                reset_form()
                st.rerun()
            else:
                st.error("⚠ Please enter a name!")


# Main graph display
st.write("### Your Family Tree")

# Search button and Clear highlight button (top-right)
col_caption, col_search, col_clear = st.columns([6, 1, 1])
with col_caption:
    st.caption("Select node from dropdown, toggle Add/Edit mode")
with col_search:
    if st.button("Search", use_container_width=True, key="open_search"):
        search_dialog()
with col_clear:
    if st.session_state.highlight_path:
        if st.button("Clear", use_container_width=True, key="clear_highlight"):
            st.session_state.highlight_path = False
            st.session_state.highlighted_edges = []
            st.session_state.highlighted_node = None
            st.rerun()


    
if st.session_state.tree_data['nodes']:
    from components.graph_renderer import render_tree_graph
    
    # Pass highlighted edges and node if search is active
    highlighted_edges = st.session_state.highlighted_edges if st.session_state.get('highlight_path') else []
    highlighted_node = st.session_state.highlighted_node if st.session_state.get('highlight_path') else None
    
    return_value = render_tree_graph(
        st.session_state.tree_data,
        selected_id=st.session_state.selected_node,
        highlighted_edges=highlighted_edges,
        highlighted_node=highlighted_node
    )

else:
    st.info("Add your first node from the sidebar to start building your tree!")
