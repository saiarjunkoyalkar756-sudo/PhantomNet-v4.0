from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field # Import BaseModel and Field
from typing import List, Optional, Dict, Any
import datetime
import re

from . import crud, models
from .database import SessionLocal, engine, get_db
from ..log_normalizer.event_schema import NormalizedLogEvent as NormalizedLogEventSchema # For response models if we return full events



router = APIRouter()

# Pydantic model for a PhantomQL query request
class PhantomQLQueryRequest(BaseModel):
    query_string: str = Field(..., example="search 'failed login' | where severity == 'High' | count by source_host")
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    limit: int = 100
    skip: int = 0

# Pydantic model for a simplified response, could be more complex
class QueryResponse(BaseModel):
    results: List[Dict[str, Any]]
    count: int

class AnalyticsResponse(BaseModel):
    data: Dict[str, Any]

def _parse_phantomql_query(query_string: str) -> Dict[str, Any]:
    """
    A very basic simulated parser for PhantomQL-like queries.
    Supports 'search', 'where', 'count by'.
    Returns a dictionary of parsed components.
    """
    parsed_query = {
        "search_query": None,
        "filters": {},
        "aggregation": None,
        "group_by": None
    }

    parts = [p.strip() for p in query_string.split('|') if p.strip()]

    for part in parts:
        if part.startswith("search"):
            search_term_match = re.search(r"search\s+['\"](.*?)['\"]", part)
            if search_term_match:
                parsed_query["search_query"] = search_term_match.group(1)
        elif part.startswith("where"):
            filter_clause = part[len("where"):
].strip()
            # Very basic parsing for 'field == "value"' or 'field > value'
            filter_matches = re.findall(r"(\w+)\s*(==|!=|>|<|>=|<=)\s*['\"]?([\w\d\s\.-]+)['\"]?", filter_clause)
            for field, op, value in filter_matches:
                parsed_query["filters"][field] = {"op": op, "value": value}
        elif part.startswith("count by"):
            group_by_field = part[len("count by"):
].strip()
            parsed_query["aggregation"] = "count"
            parsed_query["group_by"] = group_by_field
    
    return parsed_query

@router.post("/query/", response_model=QueryResponse)
def execute_phantomql_query(query_request: PhantomQLQueryRequest, db: Session = Depends(get_db)):
    """
    Executes a PhantomQL-like query against the normalized event data.
    """
    parsed = _parse_phantomql_query(query_request.query_string)
    
    # Apply filters extracted from 'where' and 'search'
    # This is a simplified mapping to crud.get_normalized_events parameters
    events_filters = {
        "search_query": parsed["search_query"],
        "start_time": query_request.start_time,
        "end_time": query_request.end_time,
        "limit": query_request.limit,
        "skip": query_request.skip
    }

    # Map parsed 'where' filters to crud parameters
    for field, condition in parsed["filters"].items():
        # This is very basic and needs robust handling for different ops and types
        if condition["op"] == "==":
            if field == "event_type":
                events_filters["event_type"] = condition["value"]
            elif field == "severity":
                events_filters["severity"] = condition["value"]
            elif field == "source_host":
                events_filters["source_host"] = condition["value"]
            elif field == "source_ip":
                events_filters["source_ip"] = condition["value"]
            elif field == "destination_ip":
                events_filters["destination_ip"] = condition["value"]
            elif field == "user":
                events_filters["user"] = condition["value"]
            # Add more field mappings as necessary

    if parsed["aggregation"] == "count" and parsed["group_by"]:
        # Special handling for aggregation
        if parsed["group_by"] == "severity":
            counts = crud.count_events_by_severity(db, query_request.start_time, query_request.end_time)
            return QueryResponse(results=[{"severity": k, "count": v} for k, v in counts.items()], count=len(counts))
        elif parsed["group_by"] == "event_type":
            counts = crud.count_events_by_event_type(db, query_request.start_time, query_request.end_time)
            return QueryResponse(results=[{"event_type": k, "count": v} for k, v in counts.items()], count=len(counts))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported 'count by' field: {parsed['group_by']}")
    
    events = crud.get_normalized_events(db=db, **events_filters)
    # Convert SQLAlchemy objects to dictionaries for generic response
    results_as_dicts = [{c.name: getattr(event, c.name) for c in event.__table__.columns} for event in events]

    return QueryResponse(results=results_as_dicts, count=len(results_as_dicts))

@router.get("/analytics/severity_counts", response_model=AnalyticsResponse)
def get_severity_counts(
    start_time: Optional[datetime.datetime] = Query(None),
    end_time: Optional[datetime.datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns a count of normalized events grouped by severity level.
    """
    counts = crud.count_events_by_severity(db, start_time, end_time)
    return AnalyticsResponse(data=counts)

@router.get("/analytics/event_type_counts", response_model=AnalyticsResponse)
def get_event_type_counts(
    start_time: Optional[datetime.datetime] = Query(None),
    end_time: Optional[datetime.datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns a count of normalized events grouped by event type.
    """
    counts = crud.count_events_by_event_type(db, start_time, end_time)
    return AnalyticsResponse(data=counts)