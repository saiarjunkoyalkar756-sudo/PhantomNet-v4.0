# backend_api/soar_engine/state.py

# In-memory stores for playbooks and playbook runs.
# Used by soar_engine/consumer.py and tests to manage playbook lifecycle.
playbooks_store = {}
playbook_runs = {}