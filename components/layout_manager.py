def apply_hierarchical_layout(tree_data):
    """Apply hierarchical layout to tree"""
    nodes = tree_data.get('nodes', [])
    edges = tree_data.get('edges', [])
    
    if not nodes:
        return
    
    # Step 1: Assign levels to all nodes
    assign_levels(nodes, edges)
    
    # Step 2: Group nodes by level
    levels = {}
    for node in nodes:
        if node.get('type') == 'person':
            level = node.get('level', 0)
            if level not in levels:
                levels[level] = []
            levels[level].append(node)
    
    # Step 3: Layout each level
    y_spacing = 150
    x_spacing = 120
    
    for level_num in sorted(levels.keys()):
        level_nodes = levels[level_num]
        y_pos = level_num * y_spacing
        
        # Find couples in this level
        couples = find_couples(level_nodes, edges)
        
        # Position nodes
        x_offset = 0
        positioned = set()
        
        for couple in couples:
            if len(couple) == 2:
                # Couple - position them together with more spacing
                person1, person2 = couple
                person1['x'] = x_offset
                person1['y'] = y_pos
                positioned.add(person1['id'])
                
                person2['x'] = x_offset + x_spacing * 1.0  # Spacing between spouses
                person2['y'] = y_pos
                positioned.add(person2['id'])
                
                # Position junction if exists (FIXED: centered exactly between spouses)
                junction_id = find_junction_between(person1['id'], person2['id'], nodes, edges)
                if junction_id:
                    junction_node = next((n for n in nodes if n['id'] == junction_id), None)
                    if junction_node:
                        # CRITICAL FIX: Junction must be exactly at midpoint of the two people
                        junction_node['x'] = (person1['x'] + person2['x']) / 2.0
                        junction_node['y'] = y_pos
                
                x_offset += x_spacing * 2.2  # Total width for couple
            else:
                # Single person
                person = couple[0]
                person['x'] = x_offset
                person['y'] = y_pos
                positioned.add(person['id'])
                x_offset += x_spacing * 1.2
        
        # Position any remaining nodes
        for node in level_nodes:
            if node['id'] not in positioned:
                node['x'] = x_offset
                node['y'] = y_pos
                positioned.add(node['id'])
                x_offset += x_spacing

# ... rest of functions (assign_levels, find_couples, find_junction_between) remain the same


def assign_levels(nodes, edges):
    """Assign hierarchical levels to all nodes"""
    # Find root nodes (people with no incoming child_to_parent edges)
    children_ids = {e['source'] for e in edges if e.get('type') == 'child_to_parent'}
    
    # Set root level
    for node in nodes:
        if node.get('type') == 'person':
            if node['id'] not in children_ids:
                node['level'] = 0
    
    # Propagate levels downward
    max_iterations = 20
    for _ in range(max_iterations):
        changed = False
        for node in nodes:
            if node.get('type') == 'person' and 'level' in node:
                # Find all children of this person
                for edge in edges:
                    if edge.get('type') == 'child_to_parent':
                        # Check if this node is the parent
                        if edge['target'] == node['id']:
                            # Direct parent-child
                            child_node = next((n for n in nodes if n['id'] == edge['source']), None)
                            if child_node:
                                new_level = node['level'] + 1
                                if child_node.get('level', -1) != new_level:
                                    child_node['level'] = new_level
                                    changed = True
                        else:
                            # Check if this node connects to a junction
                            target_node = next((n for n in nodes if n['id'] == edge['target']), None)
                            if target_node and target_node.get('type') == 'junction':
                                # Check if this person is connected to the junction
                                junction_edges = [e for e in edges 
                                                if e.get('type') == 'parent_to_junction' 
                                                and e['source'] == node['id'] 
                                                and e['target'] == target_node['id']]
                                if junction_edges:
                                    # This person is a parent through junction
                                    child_node = next((n for n in nodes if n['id'] == edge['source']), None)
                                    if child_node:
                                        new_level = node['level'] + 1
                                        if child_node.get('level', -1) != new_level:
                                            child_node['level'] = new_level
                                            changed = True
        
        if not changed:
            break
    
    # Assign level to junctions based on their parents
    for node in nodes:
        if node.get('type') == 'junction':
            parent_edges = [e for e in edges if e.get('type') == 'parent_to_junction' and e['target'] == node['id']]
            if parent_edges:
                parent_id = parent_edges[0]['source']
                parent_node = next((n for n in nodes if n['id'] == parent_id), None)
                if parent_node:
                    node['level'] = parent_node.get('level', 0)

def find_couples(level_nodes, edges):
    """Find couples (spouse pairs) in a level"""
    couples = []
    paired = set()
    
    for node in level_nodes:
        if node['id'] in paired:
            continue
        
        # Look for spouse connection
        spouse_edge = next((e for e in edges 
                          if (e['source'] == node['id'] or e['target'] == node['id']) 
                          and e.get('type') == 'spouse'), None)
        
        if spouse_edge:
            spouse_id = spouse_edge['target'] if spouse_edge['source'] == node['id'] else spouse_edge['source']
            spouse_node = next((n for n in level_nodes if n['id'] == spouse_id), None)
            if spouse_node:
                couples.append([node, spouse_node])
                paired.add(node['id'])
                paired.add(spouse_id)
            else:
                couples.append([node])
                paired.add(node['id'])
        else:
            # Check for junction connection
            junction_edge = next((e for e in edges 
                                if e['source'] == node['id'] 
                                and e.get('type') == 'parent_to_junction'), None)
            if junction_edge:
                junction_id = junction_edge['target']
                # Find other parent
                other_parents = [e['source'] for e in edges 
                               if e['target'] == junction_id 
                               and e.get('type') == 'parent_to_junction' 
                               and e['source'] != node['id']]
                if other_parents:
                    spouse_node = next((n for n in level_nodes if n['id'] == other_parents[0]), None)
                    if spouse_node:
                        couples.append([node, spouse_node])
                        paired.add(node['id'])
                        paired.add(other_parents[0])
                    else:
                        couples.append([node])
                        paired.add(node['id'])
                else:
                    couples.append([node])
                    paired.add(node['id'])
            else:
                couples.append([node])
                paired.add(node['id'])
    
    return couples

def find_junction_between(person1_id, person2_id, nodes, edges):
    """Find junction node between two people"""
    for edge in edges:
        if edge.get('type') == 'parent_to_junction' and edge['source'] == person1_id:
            junction_id = edge['target']
            if any(e['source'] == person2_id and e['target'] == junction_id 
                   and e.get('type') == 'parent_to_junction' for e in edges):
                return junction_id
    return None
