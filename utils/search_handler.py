def search_nodes(tree_data, query):
    """
    Fuzzy search for nodes by name - real-time filtering from first character
    Returns list of matching nodes with metadata
    """
    if not query:
        return []
    
    query = query.lower().strip()
    person_nodes = [n for n in tree_data.get('nodes', []) if n.get('type') == 'person']
    
    results = []
    for node in person_nodes:
        name = node.get('name', '').lower()
        
        # Exact match (highest priority)
        if query == name:
            score = 100
        # Starts with
        elif name.startswith(query):
            score = 90
        # Contains
        elif query in name:
            score = 70
        # Word boundary match
        elif any(word.startswith(query) for word in name.split()):
            score = 80
        else:
            continue
        
        # Format dates
        from utils.data_handler import format_date_range
        birth = node.get('birth_date', '')
        death = node.get('death_date', '')
        date_display = format_date_range(birth, death) or "Unknown dates"
        
        results.append({
            'id': node['id'],
            'name': node['name'],
            'dates': date_display,
            'level': node.get('level', 0),
            'score': score,
            'x': node.get('x', 0),
            'y': node.get('y', 0)
        })
    
    # Sort by score (highest first)
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:10]  # Top 10 results


def find_path_to_node(tree_data, target_node_id):
    """
    Find path from root node to target node using BFS
    Returns list of edge tuples that form the path
    """
    nodes = tree_data.get('nodes', [])
    edges = tree_data.get('edges', [])
    
    # Find root node (level 0)
    root_node = next((n for n in nodes if n.get('level', 0) == 0 and n.get('type') == 'person'), None)
    if not root_node or root_node['id'] == target_node_id:
        return []
    
    # Build bidirectional adjacency graph (handles all edge types)
    graph = {}  # node_id -> list of connected node_ids
    
    for edge in edges:
        source = edge['source']
        target = edge['target']
        
        # Add both directions for traversal
        if source not in graph:
            graph[source] = []
        if target not in graph:
            graph[target] = []
        
        graph[source].append(target)
        graph[target].append(source)
    
    # BFS from root to target
    from collections import deque
    queue = deque([(root_node['id'], [root_node['id']])])
    visited = {root_node['id']}
    
    while queue:
        current, path = queue.popleft()
        
        # Found target
        if current == target_node_id:
            # Convert path nodes to edge tuples
            path_edges = []
            for i in range(len(path) - 1):
                node_a = path[i]
                node_b = path[i + 1]
                # Add both directions to ensure highlighting works
                path_edges.append((node_a, node_b))
                path_edges.append((node_b, node_a))
            return path_edges
        
        # Explore neighbors
        for neighbor in graph.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    # No path found
    return []
