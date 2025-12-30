from streamlit_agraph import Node, Edge, Config, agraph
import base64
import os

def get_default_avatar_base64():
    """Load default avatar from assets folder and convert to base64"""
    avatar_path = os.path.join('assets', 'default_avatar.jpg')
    if os.path.exists(avatar_path):
        with open(avatar_path, 'rb') as f:
            avatar_bytes = f.read()
            return base64.b64encode(avatar_bytes).decode('utf-8')
    else:
        return """iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAACXBIWXMAAAsTAAALEwEAmpwYAAABN0lEQVR4nO3YQQ6CMBBAWW7/z3gCvABewRvgBbwCXsAb4AW8gTfwBt7AG3gDb+ANvIE38AbewBt4A2/gDbyBN/AG3sAbKKXU3XU/H8/H8/F8PB/Px/PxfDwfz8fz8Xw8H8/H8/F8PB/Px/PxfDwfz8fz8Xw8H8/H8/F8PB/Px/PxfDwfz8fz8Xw8H8/H8/F8PB/Px/PxfDwfz8fz8Xw8H8/H8/F8PB/Px/PxfDwfz8fz8Xw8H8/H8/F8PB/Px/PxfDwfz8fz8Xw8H8/H8/F8PB/Px/PxfDwfz8fz8Xw8H8/H8/F8PB/Px/PxfDwfz8fz8Xw8H8/H8/F8PB/Px/PxfDwfz8fz8Xw8H8/H8/F8PB/Px/PxfDwfz8fz8Xw8H8/H8/F8PB/Px/PxfDwfz8fz8Xw8H8/H8/F8PB/Px/MBgL/aBdOQN7l7AK/gAAAAAElFTkSuQmCC"""

DEFAULT_AVATAR_B64 = get_default_avatar_base64()

def create_graph_config():
    """Create graph configuration"""
    return Config(
        width="100%",
        height=600,
        directed=False,
        physics=False,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#FFD700",
        collapsible=False
    )

def build_graph_nodes(tree_data, selected_id=None, highlighted_node=None):
    """Build visual nodes for graph with white borders and optional highlighting"""
    from utils.data_handler import format_date_range
    
    nodes = []
    for node in tree_data['nodes']:
        if node.get('type') == 'person':
            node_id = node['id']
            name = node.get('name', 'Unknown')
            
            # Handle both old 'date' field and new 'birth_date'/'death_date' fields
            birth_date = node.get('birth_date', node.get('date', ''))
            death_date = node.get('death_date', '')
            date_display = format_date_range(birth_date, death_date)
            
            # Create label
            label = f"{name}\n{date_display}" if date_display else name
            
            # White border by default, gold for selected, green for search result
            if node_id == highlighted_node:
                border_color = "#00FF00"  # Green for search result
            elif node_id == selected_id:
                border_color = "#FFD700"  # Gold for selected
            else:
                border_color = "#FFFFFF"  # White default
            
            photo_b64 = node.get('photo')
            if photo_b64:
                image_url = f"data:image/jpeg;base64,{photo_b64}"
            else:
                image_url = f"data:image/png;base64,{DEFAULT_AVATAR_B64}"
            
            # Create tooltip with name and dates
            tooltip = f"{name}"
            if date_display:
                tooltip += f"\n{date_display}"
            
            nodes.append(Node(
                id=node_id,
                label=label,
                size=35,
                shape="circularImage",
                image=image_url,
                color=border_color,
                font={'size': 10, 'color': '#FFFFFF', 'strokeWidth': 2, 'strokeColor': '#000000'},
                title=tooltip,
                x=node.get('x', 0),
                y=node.get('y', 0)
            ))

        elif node.get('type') == 'junction':
            nodes.append(Node(
                id=node['id'],
                label="",
                size=2,  # Slightly larger for visibility
                color="#FFFFFF",  # White junction dots
                shape="dot",
                x=node.get('x', 0),
                y=node.get('y', 0)
            ))
    return nodes

def build_graph_edges(tree_data, highlighted_edges=None):
    """Build edges for graph with white lines and optional path highlighting"""
    if highlighted_edges is None:
        highlighted_edges = []
    
    edges = []
    for edge in tree_data['edges']:
        edge_type = edge.get('type', 'spouse')
        
        # Check if this edge is in the highlighted path
        is_highlighted = (edge['source'], edge['target']) in highlighted_edges
        
        if edge_type == 'spouse':
            edges.append(Edge(
                source=edge['source'],
                target=edge['target'],
                color="#00FF00" if is_highlighted else "#FFFFFF",  # Green if highlighted, white default
                width=2.5 if is_highlighted else 1.5,
                smooth=False,
                arrows=""
            ))
        elif edge_type == 'parent_to_junction':
            edges.append(Edge(
                source=edge['source'],
                target=edge['target'],
                color="#00FF00" if is_highlighted else "#FFFFFF",  # Green if highlighted, white default
                width=2.5 if is_highlighted else 1.5,
                smooth=False,
                arrows=""
            ))
        elif edge_type == 'child_to_parent':
            edges.append(Edge(
                source=edge['source'],
                target=edge['target'],
                color="#00FF00" if is_highlighted else "#FFFFFF",  # Green if highlighted, white default
                width=2.5 if is_highlighted else 1.5,
                smooth={'enabled': True, 'type': 'cubicBezier', 'roundness': 0.5},
                arrows=""
            ))
    return edges

def render_tree_graph(tree_data, selected_id=None, highlighted_edges=None, highlighted_node=None):
    """Render tree as interactive graph with search highlighting support"""
    if highlighted_edges is None:
        highlighted_edges = []
    
    nodes = build_graph_nodes(tree_data, selected_id, highlighted_node)
    edges = build_graph_edges(tree_data, highlighted_edges)
    config = create_graph_config()
    
    return agraph(nodes=nodes, edges=edges, config=config)
