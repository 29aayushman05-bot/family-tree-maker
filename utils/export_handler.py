import json
from utils.pdf_renderer import export_tree_to_pdf_visual, export_tree_to_pdf_list

def export_to_json(tree_data):
    """Export tree as JSON string with positions"""
    clean_data = {
        'nodes': [],
        'edges': tree_data.get('edges', [])
    }
    
    # Export all nodes (person and junction) WITH positions and fixed flag
    for n in tree_data.get('nodes', []):
        if n.get('type') == 'person':
            clean_data['nodes'].append({
                'id': n['id'],
                'name': n['name'],
                'birth_date': n.get('birth_date', ''),
                'death_date': n.get('death_date', ''),
                'photo': n.get('photo'),
                'type': 'person',
                'x': n.get('x', 0),
                'y': n.get('y', 0),
                'level': n.get('level', 0),
                'fixed': n.get('fixed', False)
            })
        elif n.get('type') == 'junction':
            clean_data['nodes'].append({
                'id': n['id'],
                'type': 'junction',
                'x': n.get('x', 0),
                'y': n.get('y', 0),
                'level': n.get('level', 0),
                'fixed': n.get('fixed', False)
            })
    
    return json.dumps(clean_data, indent=2)

def export_to_pdf(tree_data):
    """Export tree as visual PDF"""
    try:
        return export_tree_to_pdf_visual(tree_data)
    except Exception as e:
        print(f"Visual export failed: {e}")
        import traceback
        traceback.print_exc()
        try:
            return export_tree_to_pdf_list(tree_data)
        except:
            return b""
