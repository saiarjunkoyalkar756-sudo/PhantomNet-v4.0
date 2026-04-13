#!/bin/bash

echo "Starting PhantomNet API Gateway..."
export JWT_SECRET_KEY="super_secret_jwt_key_random_string_12345"
export DB_PASSWORD="super_secret_db_password_random_string_67890"
export NEO4J_PASSWORD="super_secret_neo4j_password_random_string_abcde"
export PYTHONPATH=~/test
uvicorn backend_api.gateway_service.main:app --host 0.0.0.0 --port 8000 &> ~/test/logs/api_gateway.log &
sleep 2

echo "Starting PhantomNet Agent..."
cd ~/test/phantomnet_agent || exit
python3 main.py --mode full &> ~/test/logs/agent.log &
sleep 2

echo "Starting Dashboard..."
cd ~/test/dashboard_frontend || exit
npm start &> ~/test/logs/dashboard.log &
sleep 2

echo "PhantomNet running on Termux ✔"
