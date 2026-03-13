"""
Baserow API Client — Table 865847 sync
"""
import os
import logging
import httpx

logger = logging.getLogger("frek.baserow")

BASEROW_TOKEN = os.environ.get("BASEROW_TOKEN", "")
BASEROW_API = "https://api.baserow.io/api"
TABLE_ID = 865847


def _headers():
    return {"Authorization": f"Token {BASEROW_TOKEN}"}


async def list_rows(table_id: int = TABLE_ID, size: int = 200, page: int = 1, filters: dict = None):
    params = {"size": size, "page": page}
    if filters:
        params.update(filters)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{BASEROW_API}/database/rows/table/{table_id}/",
                headers=_headers(), params=params,
            )
            if resp.status_code == 200:
                return resp.json()
            logger.warning(f"Baserow list_rows {table_id}: HTTP {resp.status_code}")
            return {"count": 0, "results": []}
    except Exception as e:
        logger.warning(f"Baserow unreachable: {e}")
        return {"count": 0, "results": []}


async def create_row(data: dict, table_id: int = TABLE_ID):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{BASEROW_API}/database/rows/table/{table_id}/",
                headers={**_headers(), "Content-Type": "application/json"},
                json=data,
            )
            if resp.status_code in (200, 201):
                return resp.json()
            logger.warning(f"Baserow create_row: HTTP {resp.status_code} - {resp.text[:200]}")
            return None
    except Exception as e:
        logger.warning(f"Baserow create error: {e}")
        return None


async def update_row(row_id: int, data: dict, table_id: int = TABLE_ID):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.patch(
                f"{BASEROW_API}/database/rows/table/{table_id}/{row_id}/",
                headers={**_headers(), "Content-Type": "application/json"},
                json=data,
            )
            if resp.status_code == 200:
                return resp.json()
            logger.warning(f"Baserow update_row: HTTP {resp.status_code}")
            return None
    except Exception as e:
        logger.warning(f"Baserow update error: {e}")
        return None


async def get_fields(table_id: int = TABLE_ID):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{BASEROW_API}/database/fields/table/{table_id}/",
                headers=_headers(),
            )
            if resp.status_code == 200:
                return resp.json()
            return []
    except Exception as e:
        logger.warning(f"Baserow fields error: {e}")
        return []
