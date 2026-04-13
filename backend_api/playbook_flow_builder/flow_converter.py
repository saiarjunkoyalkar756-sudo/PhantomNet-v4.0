from typing import List, Dict, Any, Optional
from .flow_schema import PlaybookFlow, Node, Edge

class FlowConversionError(Exception):
    """Custom exception for errors during flow conversion."""
    pass

def convert_flow_to_steps(flow: PlaybookFlow) -> List[Dict[str, Any]]:
    """
    Converts a PlaybookFlow object into a linear list of playbook steps.
    This is a simplified converter. A more robust version would handle complex
    branching, loops, and parallel execution.
    """
    steps = []
    
    # Find the start node
    start_nodes = [node for node in flow.nodes if node.type == "start"]
    if not start_nodes:
        raise FlowConversionError("No 'start' node found in the playbook flow.")
    if len(start_nodes) > 1:
        raise FlowConversionError("Multiple 'start' nodes found in the playbook flow. Only one is allowed.")
    
    current_node_id = start_nodes[0].id
    visited_nodes = set()

    while current_node_id:
        if current_node_id in visited_nodes:
            # This indicates a loop or incorrect flow, for simplicity we'll break.
            # A full implementation would detect loops and handle them (e.g., allow specific loop nodes).
            print(f"Warning: Detected a loop or re-visiting node {current_node_id}. Terminating conversion.")
            break
        visited_nodes.add(current_node_id)

        current_node = next((node for node in flow.nodes if node.id == current_node_id), None)
        if not current_node:
            raise FlowConversionError(f"Node with ID '{current_node_id}' not found.")

        # Process the current node
        if current_node.type == "action":
            action_data = current_node.data.get("action", {})
            if not action_data:
                raise FlowConversionError(f"Action node {current_node.id} has no 'action' data.")
            steps.append(action_data)
        elif current_node.type == "approval":
            approval_data = current_node.data.get("approval", {})
            if not approval_data:
                raise FlowConversionError(f"Approval node {current_node.id} has no 'approval' data.")
            # For the soar_playbook_engine, an approval might be a special action
            steps.append({"action": "await_human_approval", "parameters": approval_data})
        elif current_node.type == "condition":
            condition_data = current_node.data.get("condition", {})
            if not condition_data:
                raise FlowConversionError(f"Condition node {current_node.id} has no 'condition' data.")
            
            # For linear conversion, we'll try to follow a 'true' path first, or the first available path
            # A full engine would evaluate this at runtime.
            true_edge = next((edge for edge in flow.edges if edge.source == current_node.id and edge.label == "true"), None)
            if true_edge:
                steps.append({"action": "evaluate_condition", "parameters": condition_data, "next_step_on_true": true_edge.target})
                # For simplicity, we are not actually branching here in the linear list
                # This needs to be handled by the execution engine, not the conversion
                # The conversion simply records the condition, the execution will make the decision
            else:
                steps.append({"action": "evaluate_condition", "parameters": condition_data})

        elif current_node.type == "end":
            current_node_id = None # End the traversal
            continue
        elif current_node.type == "start":
            pass # Start node just indicates the beginning, no step generated

        # Find the next node
        outgoing_edges = [edge for edge in flow.edges if edge.source == current_node.id]
        
        if len(outgoing_edges) == 1:
            current_node_id = outgoing_edges[0].target
        elif len(outgoing_edges) > 1:
            # If there's a condition node, we might have multiple outgoing edges with labels.
            # This simplified converter will just pick the first non-conditional path
            # if explicit condition handling is not fully built out.
            # For conditional nodes, the execution engine needs to interpret the condition.
            # Here, we follow one path for conversion.
            # Priority: "true" -> "false" -> any other
            next_edge = None
            for edge in outgoing_edges:
                if current_node.type == "condition":
                    if edge.label == "true":
                        next_edge = edge
                        break
                    elif edge.label == "false" and next_edge is None: # Only if true path not found
                        next_edge = edge
                if next_edge is None: # For non-condition nodes or if no labeled edge
                    next_edge = edge
                    break # Take the first one if no specific label or not a condition node
            
            if next_edge:
                current_node_id = next_edge.target
            else:
                current_node_id = None # No path to follow
        else:
            current_node_id = None # No outgoing edges, end of flow
            
    return steps
