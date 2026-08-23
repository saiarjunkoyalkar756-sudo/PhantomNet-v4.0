from __future__ import annotations

from fastapi import Depends, FastAPI
from loguru import logger
from pydantic import BaseModel

from backend_api.case_management_service.workflow import CaseWorkflow, init_case_workflow_store
from backend_api.core.response import error_response, success_response
from backend_api.iam_service.policy import require_capability
from backend_api.shared.database import User
from backend_api.shared.service_factory import create_phantom_service


async def case_startup(app: FastAPI) -> None:
    """Initialize only the tenant-scoped governed case workflow store."""
    await init_case_workflow_store()
    logger.info("Case Management Service: governed workflow store initialized.")


case_workflow = CaseWorkflow()

app = create_phantom_service(
    name="Case Management Service",
    description="Service for tenant-scoped security investigation cases and governed playbook lifecycles.",
    version="1.0.0",
    custom_startup=case_startup,
    required_dependencies=("database",),
)


class GovernedCaseTransition(BaseModel):
    status: str


class PlaybookRequest(BaseModel):
    playbook_id: str
    playbook_version: str


class PlaybookCompletion(BaseModel):
    status: str


@app.api_route(
    "/cases",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
@app.api_route(
    "/cases/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def retired_legacy_case_api(legacy_path: str = ""):
    """Block the legacy, non-tenant-scoped case API rather than silently serving it."""
    return error_response(
        code="LEGACY_CASE_API_RETIRED",
        message="The legacy case API is retired. Use tenant-scoped /governed-cases routes with the required capability.",
        status_code=410,
    )


@app.post("/governed-cases/from-alert/{alert_id}", status_code=201)
async def create_governed_case_from_alert(
    alert_id: str,
    current_user: User = Depends(require_capability("cases:write")),
):
    try:
        case, created = await case_workflow.create_from_alert(
            str(current_user.tenant_id), alert_id, current_user.username
        )
    except LookupError:
        return error_response(code="NOT_FOUND", message="Alert not found.", status_code=404)
    return success_response(data={"case": case.model_dump(mode="json"), "created": created})


@app.get("/governed-cases/{case_id}")
async def get_governed_case(
    case_id: str,
    current_user: User = Depends(require_capability("alerts:read")),
):
    try:
        case = await case_workflow.get_case(str(current_user.tenant_id), case_id)
    except LookupError:
        return error_response(code="NOT_FOUND", message="Case not found.", status_code=404)
    return success_response(data=case.model_dump(mode="json"))


@app.patch("/governed-cases/{case_id}/status")
async def transition_governed_case(
    case_id: str,
    transition: GovernedCaseTransition,
    current_user: User = Depends(require_capability("cases:write")),
):
    try:
        case = await case_workflow.transition_case(
            str(current_user.tenant_id), case_id, transition.status, current_user.username
        )
    except LookupError:
        return error_response(code="NOT_FOUND", message="Case not found.", status_code=404)
    except ValueError as exc:
        return error_response(code="INVALID_CASE_TRANSITION", message=str(exc), status_code=409)
    return success_response(data=case.model_dump(mode="json"))


@app.post("/governed-cases/{case_id}/playbooks", status_code=201)
async def request_case_playbook(
    case_id: str,
    request: PlaybookRequest,
    current_user: User = Depends(require_capability("cases:write")),
):
    try:
        run = await case_workflow.request_playbook(
            tenant_id=str(current_user.tenant_id),
            case_id=case_id,
            playbook_id=request.playbook_id,
            playbook_version=request.playbook_version,
            actor=current_user.username,
            requires_approval=True,
        )
    except LookupError:
        return error_response(code="NOT_FOUND", message="Case not found.", status_code=404)
    return success_response(data=run.model_dump(mode="json"))


@app.post("/governed-cases/playbook-runs/{run_id}/approve")
async def approve_case_playbook(
    run_id: str,
    current_user: User = Depends(require_capability("response:approve")),
):
    try:
        run = await case_workflow.transition_playbook(
            str(current_user.tenant_id), run_id, "approved", current_user.username
        )
    except LookupError:
        return error_response(code="NOT_FOUND", message="Playbook run not found.", status_code=404)
    except ValueError as exc:
        return error_response(code="INVALID_PLAYBOOK_TRANSITION", message=str(exc), status_code=409)
    return success_response(data=run.model_dump(mode="json"))


@app.post("/governed-cases/playbook-runs/{run_id}/start")
async def start_case_playbook(
    run_id: str,
    current_user: User = Depends(require_capability("cases:write")),
):
    try:
        run = await case_workflow.transition_playbook(
            str(current_user.tenant_id), run_id, "running", current_user.username
        )
    except LookupError:
        return error_response(code="NOT_FOUND", message="Playbook run not found.", status_code=404)
    except ValueError as exc:
        return error_response(code="INVALID_PLAYBOOK_TRANSITION", message=str(exc), status_code=409)
    return success_response(data=run.model_dump(mode="json"))


@app.post("/governed-cases/playbook-runs/{run_id}/complete")
async def complete_case_playbook(
    run_id: str,
    completion: PlaybookCompletion,
    current_user: User = Depends(require_capability("cases:write")),
):
    if completion.status not in {"completed", "failed", "cancelled"}:
        return error_response(
            code="INVALID_PLAYBOOK_OUTCOME",
            message="Outcome must be completed, failed, or cancelled.",
            status_code=400,
        )
    try:
        run = await case_workflow.transition_playbook(
            str(current_user.tenant_id), run_id, completion.status, current_user.username
        )
    except LookupError:
        return error_response(code="NOT_FOUND", message="Playbook run not found.", status_code=404)
    except ValueError as exc:
        return error_response(code="INVALID_PLAYBOOK_TRANSITION", message=str(exc), status_code=409)
    return success_response(data=run.model_dump(mode="json"))


@app.get("/governed-cases/{case_id}/playbook-runs")
async def list_case_playbooks(
    case_id: str,
    current_user: User = Depends(require_capability("alerts:read")),
):
    runs = await case_workflow.list_playbook_runs(str(current_user.tenant_id), case_id)
    return success_response(data=[run.model_dump(mode="json") for run in runs])
