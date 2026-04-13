# backend_api/attack_graph_engine/path_analyzer.py
import logging
from typing import List, Tuple, Optional
import networkx as nx

logger = logging.getLogger(__name__)

class PathAnalyzer:
    """
    Analyzes the attack graph to find potential attack paths.
    """

    def __init__(self, graph: nx.DiGraph):
        self.graph = graph

    def find_shortest_path(
        self, source_node_id: str, target_node_id: str
    ) -> Optional[List[str]]:
        """
        Finds the shortest path between two nodes using the edge weights.
        A lower total weight is considered a "shorter" or "easier" path.
        """
        if not self.graph.has_node(source_node_id):
            logger.warning(f"Source node '{source_node_id}' not found in graph.")
            return None
        if not self.graph.has_node(target_node_id):
            logger.warning(f"Target node '{target_node_id}' not found in graph.")
            return None

        try:
            # Use Dijkstra's algorithm, considering the 'weight' of each edge.
            path = nx.shortest_path(
                self.graph,
                source=source_node_id,
                target=target_node_id,
                weight="weight",
            )
            logger.info(f"Found path from '{source_node_id}' to '{target_node_id}': {path}")
            return path
        except nx.NetworkXNoPath:
            logger.info(
                f"No path found between '{source_node_id}' and '{target_node_id}'."
            )
            return None
        except Exception as e:
            logger.error(f"Error finding shortest path: {e}")
            return None

    def find_all_paths(
        self, source_node_id: str, target_node_id: str, cutoff: int = 5
    ) -> List[List[str]]:
        """
        Finds all possible paths up to a certain depth (cutoff).
        This can be useful for identifying multiple ways an attacker could move.
        """
        if not self.graph.has_node(source_node_id) or not self.graph.has_node(
            target_node_id
        ):
            return []

        try:
            paths = list(
                nx.all_simple_paths(
                    self.graph,
                    source=source_node_id,
                    target=target_node_id,
                    cutoff=cutoff,
                )
            )
            return paths
        except Exception as e:
            logger.error(f"Error finding all paths: {e}")
            return []
