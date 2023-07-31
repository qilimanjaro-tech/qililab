import networkx as nx
import yaml

G = nx.DiGraph()
G.add_edge(1, 2)
print(nx.nodes(G))
graph_data = nx.node_link_data(G)
with open("./src/qililab/automatic_calibration/calibration_utils/test.yaml", "w") as f:
    yaml.dump(graph_data, f)
