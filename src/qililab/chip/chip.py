"""Chip class."""


class Chip:
    """Chip representation as a graph."""

    def __init__(self, num_of_nodes):
        self.m_num_of_nodes = num_of_nodes
        self.m_nodes = range(self.m_num_of_nodes)

        self.m_adj_list = {node: set() for node in self.m_nodes}

    def add_edge(self, node1, node2, weight=1):
        """Add edge."""
        self.m_adj_list[node1].add((node2, weight))
        self.m_adj_list[node2].add((node1, weight))

    def print_adj_list(self):
        """Print"""
        for key in self.m_adj_list.keys():
            print("node", key, ": ", self.m_adj_list[key])
