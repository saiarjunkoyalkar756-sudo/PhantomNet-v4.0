# PhantomNet Makefile
# Usage: make <target>
# Requires: docker, docker compose, python3, node, npm

.PHONY: help dev test build deploy audit clean stop logs

PYTHON   := python3
PIP      := pip
NPM      := npm
DC       := docker compose
DC_PROD  := docker compose -f docker-compose.yml -f docker-compose.prod.yml

##@ General

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
	/^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 } \
	/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Development

dev: ## Start full dev stack (hot-reload)
	@echo "Starting PhantomNet dev stack..."
	$(DC) up --build

dev-backend: ## Start backend services only
	$(DC) up --build gateway_service ai_behavioral_engine correlation_engine

dev-frontend: ## Start frontend dev server only
	cd dashboard_frontend && $(NPM) run dev

stop: ## Stop all running services
	$(DC) down

logs: ## Tail logs from all services
	$(DC) logs -f

##@ Testing

test: ## Run all backend + agent tests with coverage
	$(PYTHON) -m pytest tests/ backend_api/tests/ \
		--cov=backend_api \
		--cov=phantomnet_agent \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		-v --tb=short

test-agent: ## Run agent-specific tests only
	$(PYTHON) -m pytest phantomnet_agent/tests/ -v --tb=short

test-blockchain: ## Run blockchain tests only
	$(PYTHON) -m pytest blockchain_layer/test_blockchain.py -v

test-playbooks: ## Smoke-test all red team playbooks
	$(PYTHON) - <<'EOF'
	import os, yaml, sys
	d = "phantomnet_agent/red_teaming/playbooks"
	required = {"id","description","type","target","parameters","safety","mitre"}
	ok = True
	for f in os.listdir(d):
	    if not f.endswith(".yaml"): continue
	    data = yaml.safe_load(open(os.path.join(d,f)))
	    miss = required - set(data.keys())
	    if miss: print(f"FAIL {f}: missing {miss}"); ok = False
	    else: print(f"  ✓ {f}")
	sys.exit(0 if ok else 1)
	EOF

test-frontend: ## Run frontend tests
	cd dashboard_frontend && $(NPM) test -- --watchAll=false

##@ Security

audit: ## Run pip-audit + npm audit vulnerability scan
	@echo "=== Python Dependency Audit ==="
	$(PIP) install --quiet pip-audit
	pip-audit -r requirements.txt --desc on || true
	@echo "\n=== Frontend Dependency Audit ==="
	cd dashboard_frontend && $(NPM) audit --audit-level=moderate || true

##@ Build

build: ## Build all Docker images
	$(DC) build

build-frontend: ## Build frontend production bundle
	cd dashboard_frontend && $(NPM) run build

build-agent: ## Build agent PyInstaller binary (requires Docker)
	docker build -t pyinstaller-builder -f Dockerfile.pyinstaller .
	docker run --rm -v $$(pwd):/src pyinstaller-builder \
		"pyinstaller phantomnet_agent/pyinstaller/agent-linux.spec"

##@ Deployment

deploy: ## Deploy production stack (with prod overrides)
	$(DC_PROD) up -d --build
	@echo "PhantomNet production stack is up."
	@echo "Gateway: http://localhost:8000"

deploy-stop: ## Stop production stack
	$(DC_PROD) down

##@ Database

db-migrate: ## Run Alembic database migrations
	cd backend_api && alembic upgrade head

db-rollback: ## Rollback last Alembic migration
	cd backend_api && alembic downgrade -1

db-status: ## Show current migration status
	cd backend_api && alembic current

##@ Cleanup

clean: ## Remove Python cache, build artifacts, htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml dist/ build/ || true
	@echo "Cleaned."

clean-docker: ## Remove all stopped containers + unused images
	docker system prune -f
