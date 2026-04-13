# Networking Security Layer Architecture

This document outlines the architecture of the PhantomNet Networking Security Layer.

## System Architecture Diagram

```
+--------------------------------------------------------------------------------------------------+
|                                        Dashboard Frontend                                        |
|                                                                                                  |
| +----------------------+  +-----------------------+  +-------------------------+                 |
| | Network Overview     |  | Network Threats       |  | Network Segmentation    |                 |
| | (WebSocket)          |  | (REST API)            |  | (REST API & WebSocket)  |                 |
| +----------------------+  +-----------------------+  +-------------------------+                 |
+------------------------------------------|-------------------------------------------------------+
                                           | (HTTPS)
                                           |
+------------------------------------------v-------------------------------------------------------+
|                                     Gateway Service                                              |
|                                                                                                  |
| +-------------------------+      +-------------------------+       +-------------------------+   |
| | Zero-Trust Middleware   |----->| Micro-Segmentation API  |------>| SOAR Engine API         |   |
| +-------------------------+      +-------------------------+       +-------------------------+   |
|             |                                |                               |                   |
|             | (WebSocket)                    | (Kafka)                       | (Kafka)           |
|             |                                |                               |                   |
| +-----------v-------------+      +-----------v-----------------+   +---------v-----------------+ |
| | WebSocket Server        |      | Micro-Segmentation Service|   | SOAR Engine             | |
| | (networking events)     |      | (consumes network graph)  |   | (consumes alerts)       | |
| +-------------------------+      +---------------------------+   +---------------------------+ |
|             |                                                                                  |
|             | (Kafka)                                                                          |
|             |                                                                                  |
| +-----------v-----------------+                                                                |
| | AI Behavioral Engine    |                                                                |
| | (consumes network events) |                                                                |
| | (produces alerts)         |----------------------------------------------------------------->+
| +---------------------------+                                                                |
|             |                                                                                  |
|             | (Blockchain)                                                                     |
|             |                                                                                  |
| +-----------v-------------+                                                                    |
| | Blockchain Service      |                                                                    |
| +-------------------------+                                                                    |
+--------------------------------------------------------------------------------------------------+
                                           | (mTLS)
                                           |
+------------------------------------------v-------------------------------------------------------+
|                                        PhantomNet Agent                                          |
|                                                                                                  |
| +-------------------------+      +-------------------------+       +-------------------------+   |
| | Network Sensor          |----->| Backend Client          |------>| Network Defense         |   |
| | (captures packets)      |      | (sends events)          |       | (executes actions)      |   |
| +-------------------------+      +-------------------------+       +-------------------------+   |
+--------------------------------------------------------------------------------------------------+
```

## Folder Structure

```
/
├── backend_api/
│   ├── ai/
│   │   └── network_ids_model.py
│   ├── blockchain_service/
│   │   └── blockchain.py
│   ├── gateway_service/
│   │   ├── main.py
│   │   └── agent_command_api.py
│   ├── microsegmentation_service/
│   │   ├── service.py
│   │   └── models.py
│   ├── networking/
│   │   ├── __init__.py
│   │   └── ws_server.py
│   ├── routes/
│   │   └── agent_network.py
│   ├── security/
│   │   └── zero_trust_manager.py
│   └── soar_engine/
│       ├── __init__.py
│       ├── main.py
│       ├── playbooks.py
│       └── countermeasures.py
├── dashboard_frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── network/
│   │   │       └── NetworkGraph.jsx
│   │   └── pages/
│   │       └── network/
│   │           ├── NetworkOverviewPage.jsx
│   │           ├── NetworkThreatsPage.jsx
│   │           └── NetworkSegmentationPage.jsx
└── phantomnet_agent/
    └── networking/
        ├── __init__.py
        ├── network_sensor.py
        ├── network_defense.py
        └── backend_client.py
```
