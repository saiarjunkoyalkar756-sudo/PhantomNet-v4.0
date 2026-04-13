from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import json

from .parser import parse_query
from .executor import execute_query

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()


class PNQLQuery(BaseModel):
    query: str


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "PNQL Engine service is healthy"}


@app.post("/query")
async def execute_pnql_query(pnql_query: PNQLQuery):
    logger.info(f"Received PNQL query: {pnql_query.query}")
    try:
        parsed_query = parse_query(pnql_query.query)
        results = await execute_query(parsed_query)
        return {"status": "success", "query": pnql_query.query, "results": results}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing PNQL query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error during query execution."
        )
