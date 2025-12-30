import base64

def position_new_node(tree_data, new_node_id, parent_id=None, sibling_id=None, spouse_id=None):
    """Smart positioning for new node only - doesn't touch existing or fixed nodes"""
    new_node = next((n for n in tree_data['nodes'] if n['id'] == new_node_id), None)
    if not new_node:
        return
    
    # Skip if node is manually fixed
    if new_node.get('fixed', False):
        return
    
    if parent_id:
        # Child node - position below parent
        parent = next((n for n in tree_data['nodes'] if n['id'] == parent_id), None)
        if parent:
            # Count siblings to space horizontally
            siblings = [n for n in tree_data['nodes'] 
                       if n.get('level') == parent.get('level', 0) + 1 
                       and n.get('type') == 'person']
            offset = len(siblings) * 150
            new_node['x'] = parent.get('x', 400) + offset - 150
            new_node['y'] = parent.get('y', 50) + 200
            new_node['level'] = parent.get('level', 0) + 1
    
    elif sibling_id:
        # Sibling node - position next to sibling
        sibling = next((n for n in tree_data['nodes'] if n['id'] == sibling_id), None)
        if sibling:
            new_node['x'] = sibling.get('x', 400) + 200
            new_node['y'] = sibling.get('y', 50)
            new_node['level'] = sibling.get('level', 0)
    
    elif spouse_id:
        # Spouse node - position next to spouse
        spouse = next((n for n in tree_data['nodes'] if n['id'] == spouse_id), None)
        if spouse:
            new_node['x'] = spouse.get('x', 400) + 200
            new_node['y'] = spouse.get('y', 50)
            new_node['level'] = spouse.get('level', 0)
    
    else:
        # Root node - center position
        new_node['x'] = 400
        new_node['y'] = 50
        new_node['level'] = 0

def add_root_node(tree_data, name, birth_date, death_date, photo_file):
    """Add root node to tree"""
    photo_b64 = None
    if photo_file:
        photo_b64 = base64.b64encode(photo_file.read()).decode()
    
    node_id = f"person_{len(tree_data['nodes'])}"
    node = {
        'id': node_id,
        'name': name,
        'birth_date': birth_date,
        'death_date': death_date,
        'photo': photo_b64,
        'type': 'person',
        'level': 0,
        'x': 0,
        'y': 0,
        'fixed': False
    }
    
    tree_data['nodes'].append(node)
    position_new_node(tree_data, node_id)

def add_child(tree_data, parent_id, name, birth_date, death_date, photo_file):
    """Add child to selected parent"""
    photo_b64 = None
    if photo_file:
        photo_b64 = base64.b64encode(photo_file.read()).decode()
    
    parent = next((n for n in tree_data['nodes'] if n['id'] == parent_id), None)
    if not parent:
        return
    
    child_id = f"person_{len(tree_data['nodes'])}"
    child_node = {
        'id': child_id,
        'name': name,
        'birth_date': birth_date,
        'death_date': death_date,
        'photo': photo_b64,
        'type': 'person',
        'level': parent['level'] + 1,
        'x': 0,
        'y': 0,
        'fixed': False
    }
    
    tree_data['nodes'].append(child_node)
    
    # Find if parent has spouse with junction
    parent_edges = [e for e in tree_data['edges'] if e['source'] == parent_id or e['target'] == parent_id]
    junction_edge = next((e for e in parent_edges if e.get('type') == 'parent_to_junction'), None)
    
    if junction_edge:
        # Junction already exists - connect to it
        junction_id = junction_edge['target']
        tree_data['edges'].append({
            'source': child_id,
            'target': junction_id,
            'type': 'child_to_parent'
        })
    else:
        # Check if parent has a spouse (via 'spouse' edge)
        spouse_edge = next((e for e in parent_edges if e.get('type') == 'spouse'), None)
        
        if spouse_edge:
            # Parent has spouse but no junction yet - CREATE JUNCTION NOW!
            spouse_id = spouse_edge['target'] if spouse_edge['source'] == parent_id else spouse_edge['source']
            
            # Remove the old spouse edge
            tree_data['edges'].remove(spouse_edge)
            
            # Create junction node
            junction_id = f"junction_{len(tree_data['nodes'])}"
            junction_node = {
                'id': junction_id,
                'type': 'junction',
                'level': parent['level'],
                'x': parent.get('x', 0) + 100,
                'y': parent.get('y', 0) + 50,
                'fixed': False
            }
            tree_data['nodes'].append(junction_node)
            
            # Connect both parents to junction
            tree_data['edges'].append({
                'source': parent_id,
                'target': junction_id,
                'type': 'parent_to_junction'
            })
            tree_data['edges'].append({
                'source': spouse_id,
                'target': junction_id,
                'type': 'parent_to_junction'
            })
            
            # Connect child to junction
            tree_data['edges'].append({
                'source': child_id,
                'target': junction_id,
                'type': 'child_to_parent'
            })
        else:
            # No spouse - direct connection to parent
            tree_data['edges'].append({
                'source': child_id,
                'target': parent_id,
                'type': 'child_to_parent'
            })
    
    position_new_node(tree_data, child_id, parent_id=parent_id)
    # === ADD THIS REBALANCING CODE HERE ===
    
    # Find ALL children of this parent
    all_children = []
    for node in tree_data['nodes']:
        if node.get('type') == 'person' and node.get('level') == parent['level'] + 1:
            # Check if this node is connected to parent
            for edge in tree_data['edges']:
                if edge.get('type') == 'child_to_parent' and edge['source'] == node['id']:
                    target = edge['target']
                    # Check if target is parent OR junction connected to parent
                    if target == parent_id:
                        all_children.append(node)
                        break
                    else:
                        # Check if junction connects to parent
                        for p_edge in tree_data['edges']:
                            if (p_edge.get('type') == 'parent_to_junction' and 
                                p_edge['source'] == parent_id and 
                                p_edge['target'] == target):
                                all_children.append(node)
                                break
                        break
    
    # Rebalance children around parent center
    if all_children:
        num_children = len(all_children)
        spacing = 200
        parent_x = parent.get('x', 0)
        parent_y = parent.get('y', 0)
        
        # Calculate spread positions
        if num_children % 2 == 1:  # Odd: -200, 0, 200
            for i, child in enumerate(all_children):
                offset = (i - num_children // 2) * spacing
                child['x'] = parent_x + offset
                child['y'] = parent_y + 150
        else:  # Even: -300, -100, 100, 300
            for i, child in enumerate(all_children):
                offset = (i - num_children / 2 + 0.5) * spacing
                child['x'] = parent_x + offset
                child['y'] = parent_y + 150
    
    

def add_spouse(tree_data, person_id, name, birth_date, death_date, photo_file):
    """Add spouse to selected person"""
    photo_b64 = None
    if photo_file:
        photo_b64 = base64.b64encode(photo_file.read()).decode()
    
    person = next((n for n in tree_data['nodes'] if n['id'] == person_id), None)
    if not person:
        return
    
    spouse_id = f"person_{len(tree_data['nodes'])}"
    spouse_node = {
        'id': spouse_id,
        'name': name,
        'birth_date': birth_date,
        'death_date': death_date,
        'photo': photo_b64,
        'type': 'person',
        'level': person['level'],
        'x': 0,
        'y': 0,
        'fixed': False
    }
    
    tree_data['nodes'].append(spouse_node)
    
    # Check if person already has children
    children = [e for e in tree_data['edges'] 
                if e.get('target') == person_id and e.get('type') == 'child_to_parent']
    
    if children:
        # Create junction node
        junction_id = f"junction_{len(tree_data['nodes'])}"
        junction_node = {
            'id': junction_id,
            'type': 'junction',
            'level': person['level'],
            'x': person.get('x', 0) + 100,
            'y': person.get('y', 0) + 50,
            'fixed': False
        }
        
        tree_data['nodes'].append(junction_node)
        
        # Connect both spouses to junction
        tree_data['edges'].append({
            'source': person_id,
            'target': junction_id,
            'type': 'parent_to_junction'
        })
        tree_data['edges'].append({
            'source': spouse_id,
            'target': junction_id,
            'type': 'parent_to_junction'
        })
        
        # Update children to point to junction
        for edge in children:
            edge['target'] = junction_id
    else:
        # Simple spouse connection
        tree_data['edges'].append({
            'source': person_id,
            'target': spouse_id,
            'type': 'spouse'
        })
    
    position_new_node(tree_data, spouse_id, spouse_id=person_id)

def add_sibling(tree_data, person_id, name, birth_date, death_date, photo_file):
    """Add sibling to selected person"""
    photo_b64 = None
    if photo_file:
        photo_b64 = base64.b64encode(photo_file.read()).decode()
    
    person = next((n for n in tree_data['nodes'] if n['id'] == person_id), None)
    if not person:
        return
    
    sibling_id = f"person_{len(tree_data['nodes'])}"
    sibling_node = {
        'id': sibling_id,
        'name': name,
        'birth_date': birth_date,
        'death_date': death_date,
        'photo': photo_b64,
        'type': 'person',
        'level': person['level'],
        'x': 0,
        'y': 0,
        'fixed': False
    }
    
    tree_data['nodes'].append(sibling_node)
    
    # Find parent connection
    parent_edge = next((e for e in tree_data['edges'] 
                       if e['source'] == person_id and e['type'] == 'child_to_parent'), None)
    
    if parent_edge:
        tree_data['edges'].append({
            'source': sibling_id,
            'target': parent_edge['target'],
            'type': 'child_to_parent'
        })
    
    position_new_node(tree_data, sibling_id, sibling_id=person_id)

def add_same_level(tree_data, reference_node_id, name, birth_date, death_date, photo_file):
    """
    Add a new person at the same generation level as reference node.
    No family relationship - just positioned nearby at same level.
    """
    import uuid
    
    # Find reference node
    ref_node = next((n for n in tree_data['nodes'] if n['id'] == reference_node_id), None)
    if not ref_node:
        return
    
    # Get reference node's level and position
    ref_level = ref_node.get('level', 0)
    ref_x = ref_node.get('x', 0)
    ref_y = ref_node.get('y', 0)
    
    # Create new node ID
    new_id = f"person_{uuid.uuid4().hex[:8]}"
    
    # Process photo if provided
    photo_b64 = None
    if photo_file:
        import base64
        photo_bytes = photo_file.read()
        photo_b64 = base64.b64encode(photo_bytes).decode('utf-8')
    
    # Create new node at same level, offset horizontally
    new_node = {
        'id': new_id,
        'name': name,
        'birth_date': birth_date,
        'death_date': death_date,
        'date': birth_date,  # Keep for backward compatibility
        'photo': photo_b64,
        'type': 'person',
        'level': ref_level,  # Same level as reference
        'x': ref_x + 250,  # Offset 250 pixels to the right
        'y': ref_y,  # Same vertical position
        'fixed': True  # Keep position fixed
    }
    
    tree_data['nodes'].append(new_node)
    
    # No edges added - this is an independent node at same generation


def edit_node(tree_data, node_id, name, birth_date, death_date, photo_file):
    """Edit existing node"""
    node = next((n for n in tree_data['nodes'] if n['id'] == node_id), None)
    if not node:
        return
    
    node['name'] = name
    node['birth_date'] = birth_date
    node['death_date'] = death_date
    
    if photo_file:
        photo_b64 = base64.b64encode(photo_file.read()).decode()
        node['photo'] = photo_b64
    
    # Don't reposition when editing

def delete_node(tree_data, node_id):
    """Delete node and its edges"""
    tree_data['nodes'] = [n for n in tree_data['nodes'] if n['id'] != node_id]
    tree_data['edges'] = [e for e in tree_data['edges'] 
                         if e['source'] != node_id and e['target'] != node_id]
    # Don't reposition remaining nodes
