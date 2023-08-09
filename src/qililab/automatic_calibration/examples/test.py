import networkx as nx

# Create the CalibrationNode instances (as defined in your question)
# ... (code for creating the instances)

# Create the Directed Acyclic Graph (DAG)
calibration_graph = nx.DiGraph()

# List of CalibrationNode instances
nodes = [
    all_xy_node_1,
    rabi_1_node,
    ramsey_coarse_node,
    ramsey_fine_node,
    rabi_2_fine_node,
    rabi_2_coarse_node,
    flipping_node,
    all_xy_node_2
]

# Add nodes and edges to the DAG
for node in nodes:
    # Add the node to the graph
    calibration_graph.add_node(node.node_id)
    
    # Add edges based on the 'children' attribute of the node
    for child in node.children:
        calibration_graph.add_edge(node.node_id, child.node_id)

# Print the nodes and edges in the graph
print("Nodes:", calibration_graph.nodes)
print("Edges:", calibration_graph.edges)