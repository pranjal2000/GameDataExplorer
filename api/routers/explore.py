from api.schemas import DataQueryRequest
from db.clickhouse import get_clickhouse_client
from fastapi import APIRouter, HTTPException, Depends, Query

from api.utils import authenticate, logger, validate_requested_table, construct_query
from api.schemas import DataQueryResponse

router = APIRouter()

@router.post("/explore_data", response_model=DataQueryResponse, dependencies=[Depends(authenticate)])
def explore_data(
        request: DataQueryRequest,
        page: int = Query(1, gt=0),
        page_size: int = Query(25, gt=0, le=100)
    ) -> DataQueryResponse:
    """
    Endpoint to explore data from a dataset with pagination and filtering.
    """
    dataset_id = request.dataset_id
    filters = request.filters
    date_gt = request.date_gt
    date_lt = request.date_lt

    # Get ClickHouse client
    client = get_clickhouse_client()
    
    # Validate dataset_id and get table_name
    table_name = validate_requested_table(dataset_id)
    
    # Construct the query and total query for pagination
    query, total_query = construct_query(table_name, filters, date_gt, date_lt, page, page_size)
    logger.info(f"Executing query: {query}")

    try:
        # Execute the total query to get the total number of results
        total_results = client.query(total_query).result_set[0][0]
        
        # Execute the main query to get the paginated results
        data = client.query(query).result_set
    except Exception as e:
        logger.error(f"Failed to execute query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute query: {e}")

    # Return the response with status, total results, and paginated results
    return {"status": "success", "total_results": total_results, "results": data, "page": page, "page_size": page_size}