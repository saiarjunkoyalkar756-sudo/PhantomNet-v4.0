# backend_api/attack_graph_engine/graph_builder.py
import logging
import time
import networkx as nx
from . import graph_model

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Manages the in-memory attack graph and provides methods to update it based on events.
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        logger.info("GraphBuilder initialized with an empty graph.")

    async def _add_node_if_not_exists(self, node: graph_model.BaseNode):
        """
        Adds a node to the graph if it doesn't already exist.
        Updates the 'last_seen' timestamp if it does.
        """
        if not self.graph.has_node(node.node_id):
            self.graph.add_node(node.node_id, data=node)
            logger.debug(f"Added node: {node.node_id} ({node.node_type})")
        else:
            # Update last_seen timestamp on existing node
            self.graph.nodes[node.node_id]["data"].last_seen = node.last_seen

    async def add_network_connection(self, event: dict):
        """
        Processes a 'packet_metadata' event to update the graph.
        """
        data = event.get("data", {})
        src_ip = data.get("source_ip")
        dst_ip = data.get("destination_ip")
        dst_port = data.get("destination_port")
        
        if not all([src_ip, dst_ip, dst_port]):
            return

        # Create nodes for the source and destination IPs
        src_node = graph_model.IPAddressNode(
            node_id=f"ip:{src_ip}",
            ip_address=src_ip,
            last_seen=event.get("timestamp"),
        )
        dst_node = graph_model.IPAddressNode(
            node_id=f"ip:{dst_ip}",
            ip_address=dst_ip,
            last_seen=event.get("timestamp"),
        )
        await self._add_node_if_not_exists(src_node)
        await self._add_node_if_not_exists(dst_node)

        # Add a 'CONNECTED_TO' edge
        edge_data = graph_model.ConnectedToEdge(
            source=src_node.node_id,
            target=dst_node.node_id,
            port=dst_port,
            protocol=data.get("protocol", "tcp"), # Default to TCP
            last_seen=event.get("timestamp"),
            weight=1.0,  # Base weight, can be adjusted by anomaly detection
        )
        self.graph.add_edge(
            edge_data.source, edge_data.target, data=edge_data
        )
        logger.debug(f"Added edge: {edge_data.source} -> {edge_data.target}")

    async def add_process_execution(self, event: dict):
        """
        Processes a 'process_execution' event to update the graph.
        (This assumes a 'process_execution' event schema)
        """
        data = event.get("data", {})
        hostname = data.get("hostname")
        pid = data.get("pid")
        process_name = data.get("process_name")
        parent_pid = data.get("parent_pid")

        if not all([hostname, pid, process_name]):
            return

        # Create host and process nodes
        host_node = graph_model.HostNode(
            node_id=f"host:{hostname}",
            hostname=hostname,
            last_seen=event.get("timestamp"),
        )
        proc_node = graph_model.ProcessNode(
            node_id=f"process:{hostname}-{pid}",
            process_name=process_name,
            pid=pid,
            command_line=data.get("command_line"),
            last_seen=event.get("timestamp"),
        )
        await self._add_node_if_not_exists(host_node)
        await self._add_node_if_not_exists(proc_node)

        # Add 'EXECUTED' edge from Host to Process
        exec_edge = graph_model.ExecutedEdge(
            source=host_node.node_id,
            target=proc_node.node_id,
            last_seen=event.get("timestamp"),
        )
        self.graph.add_edge(exec_edge.source, exec_edge.target, data=exec_edge)
        
        # If there's a parent process, link it
        if parent_pid:
            parent_node_id = f"process:{hostname}-{parent_pid}"
            if self.graph.has_node(parent_node_id):
                parent_edge = graph_model.ExecutedEdge(
                    source=parent_node_id,
                    target=proc_node.node_id,
                    last_seen=event.get("timestamp"),
                    weight=0.5 # Child process relationships have lower weight
                )
                self.graph.add_edge(parent_edge.source, parent_edge.target, data=parent_edge)

    async def add_vulnerability(self, event: dict):
        """
        Processes a 'vulnerability_scan' event.
        """
        data = event.get("data", {})
        hostname = data.get("hostname")
        cve_id = data.get("cve_id")

        if not all([hostname, cve_id]):
            return
            
        host_node_id = f"host:{hostname}"
        vuln_node = graph_model.VulnerabilityNode(
            node_id=f"cve:{cve_id}",
            cve_id=cve_id,
            severity=data.get("severity", "Unknown"),
            cvss_score=data.get("cvss_score", 0.0),
            last_seen=event.get("timestamp"),
        )

        # Ensure nodes exist before adding the edge
        if self.graph.has_node(host_node_id):
            await self._add_node_if_not_exists(vuln_node)

            # Add 'HAS_VULNERABILITY' edge
            vuln_edge = graph_model.HasVulnerabilityEdge(
                source=host_node_id,
                target=vuln_node.node_id,
                last_seen=event.get("timestamp"),
                # Higher CVSS score means a "cheaper" path for an attacker
                weight=max(0.1, 10.0 - vuln_node.cvss_score) 
            )
            self.graph.add_edge(vuln_edge.source, vuln_edge.target, data=vuln_edge)
