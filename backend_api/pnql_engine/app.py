from backend_api.shared.service_factory import create_phantom_service
from backend_api.core.response import success_response, error_response
from .parser import parse_query
from .executor import execute_query
from loguru import logger
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

class PNQLQuery(BaseModel):
    query: str

app = create_phantom_service(
    name="PNQL Engine Service",
    description="Parser and executor for the PhantomNet Query Language.",
    version="1.0.0"
)

@app.post("/query")
async def execute_pnql_query(pnql_query: PNQLQuery):
    logger.info(f"Received PNQL query: {pnql_query.query}")
    try:
        parsed_query = parse_query(pnql_query.query)
        results = await execute_query(parsed_query)
        return success_response(data={
            "query": pnql_query.query,
            "results": results
        })
    except ValueError as e:
        return error_response(code="PARSING_ERROR", message=str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error executing PNQL query: {e}")
        return error_response(code="EXECUTION_ERROR", message="Internal server error during query execution.", status_code=500)
