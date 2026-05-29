# PhantomNet v4.0 — Phase 1: Architectural Audit Results

This audit provides a comprehensive evaluation of every folder and file at the root level of the PhantomNet v4.0 repository. It establishes clear **KEEP**, **DELETE**, or **MERGE** decisions based on three core criteria:
1. **Actively Used:** Is this item actively executed or used by any running service?
2. **Imported/Referenced:** Is this item imported or referenced anywhere in the codebase?
3. **Project Integrity:** Would the project break if this item was removed?

---

## 📁 1. Folders Audit

| Folder Name | Decision | Question Answers & Rationale |
| :--- | :---: | :--- |
| `.antigravitycli/` | **MERGE** | **Used?** No (IDE config). **Referenced?** Yes (IDE metadata). **Break?** No.<br>*Action:* Consolidate into `.ai-agents/` to declutter the root. |
| `.claude/` | **MERGE** | **Used?** No (IDE config). **Referenced?** Yes (IDE settings). **Break?** No.<br>*Action:* Consolidate into `.ai-agents/` to declutter the root. |
| `.git/` | **KEEP** | **Used?** Yes (Git VC). **Referenced?** No. **Break?** Yes (loses version control history).<br>*Action:* Retain as the essential Git repository metadata directory. |
| `.github/` | **KEEP** | **Used?** Yes (CI/CD workflows). **Referenced?** No. **Break?** Yes (breaks automated CI/CD runs).<br>*Action:* Essential for GitHub Action workflows. |
| `.kiro/` | **MERGE** | **Used?** No (IDE config). **Referenced?** Yes (IDE steering). **Break?** No.<br>*Action:* Consolidate into `.ai-agents/` to declutter the root. |
| `.pytest_cache/` | **DELETE** | **Used?** No (local test temp folder). **Referenced?** No. **Break?** No.<br>*Action:* Safe to delete. Add to `.gitignore` so it's never committed. |
| `.venv_phantomnet/` | **KEEP** | **Used?** Yes (local development interpreter). **Referenced?** Yes (test execution). **Break?** Yes (local test execution fails).<br>*Action:* Keep locally, but ensure it is added to `.gitignore` so it's not committed. |
| `PhantomNet-v3.0/` | **DELETE** | **Used?** No (legacy major version). **Referenced?** No. **Break?** No.<br>*Action:* Obsolete code from the previous version. Safe to delete. |
| `backend_api/` | **KEEP** | **Used?** Yes (core microservice grid). **Referenced?** Yes (heavily imported). **Break?** Yes (core backend is destroyed).<br>*Action:* Core repository component. Maintain and refactor. |
| `blockchain_layer/` | **KEEP** | **Used?** Yes (audit ledger logic). **Referenced?** Yes (imported by blockchain service). **Break?** Yes.<br>*Action:* Keep and verify integration with threat alert pipelines. |
| `dashboard_frontend/` | **KEEP** | **Used?** Yes (React SOC Dashboard). **Referenced?** No. **Break?** Yes (no visualization portal).<br>*Action:* Keep the directory, but perform a premium rewrite of all visual components. |
| `DOCS/` | **MERGE** | **Used?** No. **Referenced?** Yes (some references in Markdown). **Break?** No.<br>*Action:* Copy the unique file `platform_support.md` to `docs/` and delete `DOCS/`. |
| `docs/` | **KEEP** | **Used?** No. **Referenced?** Yes (API/networking docs). **Break?** No.<br>*Action:* Essential unified repository for architecture schemas and guides. |
| `features/` | **MERGE** | **Used?** Partially (planning/research specs). **Referenced?** No. **Break?** No.<br>*Action:* Consolidate unimplemented capability blueprints into `docs/roadmap.md` and clean up the root. |
| `files/` | **MERGE** | **Used?** Yes (Linux systemd templates). **Referenced?** No. **Break?** Yes (breaks systemd installations).<br>*Action:* Move systemd templates to `infra/systemd/` and delete root `files/` folder. |
| `infra/` | **KEEP** | **Used?** Yes (Docker files, PostgreSQL, and Redis setups). **Referenced?** Yes. **Break?** Yes (production containers cannot spin up).<br>*Action:* Keep as the main infrastructure configuration home. |
| `logs/` | **DELETE** | **Used?** No (temp text logs). **Referenced?** No. **Break?** No.<br>*Action:* Delete committed logs from git and enforce ignore rules in `.gitignore`. |
| `microservices/` | **MERGE** | **Used?** Yes (contains `enrichment_service` connected to event stream). **Referenced?** Yes. **Break?** Yes.<br>*Action:* Consolidate `enrichment_service` inside `backend_api/` under a clean namespace to standardize import layouts, then delete `microservices/` root folder. |
| `mitre_data/` | **KEEP** | **Used?** Yes (read dynamically by MITRE TTP mapper). **Referenced?** Yes. **Break?** Yes (threat mapping service fails).<br>*Action:* Keep as it holds required intelligence databases. |
| `phantomnet_agent/` | **KEEP** | **Used?** Yes (endpoint sensor agent). **Referenced?** Yes. **Break?** Yes (breaks host telemetry).<br>*Action:* Keep, maintain, and verify local testing suites. |
| `phantomnet_core/` | **MERGE** | **Used?** Yes (OS detection adapters). **Referenced?** Yes (imported by agent collectors). **Break?** Yes.<br>*Action:* Merge `os_adapter.py` functionality into `shared.platform_utils` or consolidate the wrapper to `backend_api/shared/` to remove the redundant top-level python namespace. |
| `phantomnet-website/` | **KEEP** | **Used?** Yes (Next.js SaaS Portal). **Referenced?** No. **Break?** Yes (breaks Admin/User portals).<br>*Action:* Keep and verify live endpoint bindings to FastAPI. |
| `plugins/` | **MERGE** | **Used?** No (only mock plugins exist). **Referenced?** No. **Break?** No.<br>*Action:* Consolidate mock plugin packages under `backend_api/plugins/` or dynamic testing folders to keep root clean. |
| `website/` | **DELETE** | **Used?** No. **Referenced?** No. **Break?** No.<br>*Action:* Redundant static mockup of the landing page. The live Next.js application already implements these pages. Delete completely. |

---

## 📝 2. Markdown (.md) Files Audit

| File Name | Decision | Question Answers & Rationale |
| :--- | :---: | :--- |
| `README.md` | **KEEP** | **Used?** Yes. **Referenced?** No. **Break?** No.<br>*Action:* Keep as the main entry point and guide. Update with the consolidated structure. |
| `CHANGELOG.md` | **KEEP** | **Used?** Yes. **Referenced?** No. **Break?** No.<br>*Action:* Essential development tracking document. Keep. |
| `CLAUDE.md` | **KEEP** | **Used?** Yes (critical instructions for Claude agent). **Referenced?** No. **Break?** No.<br>*Action:* Crucial project-specific instructions guide. Keep. |
| `AGENTS.md` | **DELETE** | **Used?** No. **Referenced?** No. **Break?** No.<br>*Action:* Redundant instructions for AI agents. Merge into `CLAUDE.md` and delete. |
| `CONTRIBUTING.md` | **KEEP** | **Used?** Yes. **Referenced?** No. **Break?** No.<br>*Action:* Retain standard open source contributor guidelines. |
| `CODE_OF_CONDUCT.md`| **KEEP** | **Used?** Yes. **Referenced?** No. **Break?** No.<br>*Action:* Retain standard community behavior guidelines. |
| `SECURITY.md` | **KEEP** | **Used?** Yes. **Referenced?** No. **Break?** No.<br>*Action:* Retain standard vulnerability disclosure policy. |
| `SUPPORT.md` | **KEEP** | **Used?** Yes. **Referenced?** No. **Break?** No.<br>*Action:* Retain support contacts and tiers. |
| `RELEASE_NOTES_v2.0.md`| **DELETE** | **Used?** No. **Referenced?** No. **Break?** No.<br>*Action:* Outdated minor release notes. Safe to delete. |
| `deployment_notes.md`| **MERGE** | **Used?** No. **Referenced?** No. **Break?** No.<br>*Action:* Merge details into `docs/DEPLOYMENT_GUIDE.md` and delete. |
| `implement.md` | **DELETE** | **Used?** No. **Referenced?** No. **Break?** No.<br>*Action:* Historic draft work log, no longer aligns with v4 codebase. Delete. |
| `testing.md` | **MERGE** | **Used?** No. **Referenced?** No. **Break?** No.<br>*Action:* Merge instructions into `docs/DEVELOPER_GUIDE.md` and delete. |
| `usage.md` | **MERGE** | **Used?** No. **Referenced?** No. **Break?** No.<br>*Action:* Merge CLI and tool usage guides into `README.md` and delete. |
| `task.md` | **DELETE** | **Used?** No. **Referenced?** No. **Break?** No.<br>*Action:* Legacy task list. Safe to delete. |
| `PHANTOMNET_CONTEXT.md`| **KEEP** | **Used?** Yes. **Referenced?** No. **Break?** No.<br>*Action:* Invaluable architectural and contextual guide for developers and AI agents. Keep. |
| `Final.md` | **KEEP** | **Used?** Yes. **Referenced?** No. **Break?** No.<br>*Action:* Active instructions. Keep during implementation. |
| `Update.md` | **DELETE** | **Used?** No. **Referenced?** No. **Break?** No.<br>*Action:* Completed task guidelines. Can be safely deleted after review. |

---

## ⚡ 3. Scripts Audit

| Script Name | Decision | Question Answers & Rationale |
| :--- | :---: | :--- |
| `run_all.py` | **DELETE** | **Used?** No. **Referenced?** No. **Break?** No.<br>*Action:* Outdated script that tries to run obsolete SQLite configs and uses incorrect service paths. Delete. |
| `run_backend.sh` | **DELETE** | **Used?** No. **Referenced?** No. **Break?** No.<br>*Action:* Replaced by unified `run_phantomnet.sh` launcher and Docker. Delete. |
| `run_phantomnet.sh`| **FIX** | **Used?** Yes. **Referenced?** No. **Break?** No.<br>*Action:* Refactor to serve as the unified, simple containerized shell launcher. |
| `run_manual.ps1` | **DELETE** | **Used?** No. **Referenced?** No. **Break?** No.<br>*Action:* Legacy Windows manual process manager. Replaced by Powershell Docker scripts. Delete. |
| `setup-nix.sh` | **DELETE** | **Used?** No. **Referenced?** No. **Break?** No.<br>*Action:* Legacy configuration script. Replaced by `install_linux.sh`. Delete. |
| `install_agent.sh` | **DELETE** | **Used?** No. **Referenced?** No. **Break?** No.<br>*Action:* Redundant script. Handled fully by `install_linux.sh`. Delete. |
| `install_agent.ps1` | **DELETE** | **Used?** No. **Referenced?** No. **Break?** No.<br>*Action:* Redundant script. Handled fully by `install_windows.ps1`. Delete. |
| `install_backend.sh`| **DELETE** | **Used?** No. **Referenced?** No. **Break?** No.<br>*Action:* Redundant shell installer. Handled by Docker infrastructure. Delete. |
| `install_linux.sh` | **FIX** | **Used?** Yes. **Referenced?** No. **Break?** No.<br>*Action:* Harden and clean up as the single Linux system installer. |
| `install_windows.ps1`| **FIX** | **Used?** Yes. **Referenced?** No. **Break?** No.<br>*Action:* Harden and clean up as the single Windows system installer. |
| `Start-PhantomNet.ps1`| **KEEP** | **Used?** Yes. **Referenced?** No. **Break?** No.<br>*Action:* Convenient Windows developer utility to spin up containers. Keep. |
| `Stop-PhantomNet.ps1`| **KEEP** | **Used?** Yes. **Referenced?** No. **Break?** No.<br>*Action:* Convenient Windows developer utility to stop containers. Keep. |
| `stop_grid.ps1` | **DELETE** | **Used?** No. **Referenced?** No. **Break?** No.<br>*Action:* Replaced by standard `Stop-PhantomNet.ps1`. Delete. |
| `phantomnet-cli` | **FIX** | **Used?** Yes. **Referenced?** No. **Break?** No.<br>*Action:* Retain and fix to interact properly with standard v4 services. |

---

## 🐳 4. Dockerfiles Audit

| Dockerfile | Decision | Question Answers & Rationale |
| :--- | :---: | :--- |
| `Dockerfile.backend` | **MERGE** | **Used?** Yes. **Referenced?** Yes (in docker-compose.yml). **Break?** Yes.<br>*Action:* Move to `infra/docker/Dockerfile.backend` and update compose pathways. |
| `Dockerfile.event_stream_processor` | **MERGE** | **Used?** Yes. **Referenced?** Yes. **Break?** Yes.<br>*Action:* Move to `infra/docker/Dockerfile.event_stream_processor` and update compose pathways. |
| `Dockerfile.orchestrator` | **MERGE** | **Used?** Yes. **Referenced?** Yes. **Break?** Yes.<br>*Action:* Move to `infra/docker/Dockerfile.orchestrator` and update compose pathways. |
| `Dockerfile.policy_engine` | **DELETE** | **Used?** No. **Referenced?** Yes. **Break?** No.<br>*Action:* Legacy policy service no longer defined in active compose files. Safe to delete. |
| `Dockerfile.pyinstaller` | **MERGE** | **Used?** Yes (used for packaging agents). **Referenced?** No. **Break?** No.<br>*Action:* Move to `infra/docker/Dockerfile.pyinstaller`. |
