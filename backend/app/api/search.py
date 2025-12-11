"""Search and discovery API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import re
import uuid

from app.core.database import get_async_db
from app.api.dev_auth import get_current_user_optional
from app.models.search import SearchIndex, SearchQuery, SavedSearch, SearchSuggestion
from app.models.api_endpoint import APIEndpoint
from app.models.repository import Repository

router = APIRouter()


# ==================== Pydantic Schemas ====================

class SearchRequest(BaseModel):
    query: str
    methods: Optional[List[str]] = None  # ["GET", "POST"]
    tags: Optional[List[str]] = None
    repositories: Optional[List[str]] = None
    include_deprecated: bool = False
    page: int = 1
    page_size: int = 20


class SearchResultItem(BaseModel):
    endpoint_id: str
    path: str
    method: str
    description: Optional[str]
    repository_id: str
    repository_name: str
    tags: Optional[List[str]]
    is_deprecated: bool
    score: float
    highlights: Optional[dict]  # {"path": "...", "description": "..."}


class SearchResponse(BaseModel):
    query: str
    total: int
    page: int
    page_size: int
    results: List[SearchResultItem]
    suggestions: List[str]
    filters_applied: dict


class SuggestionResponse(BaseModel):
    suggestions: List[str]
    recent_searches: List[str]
    popular_tags: List[str]


class SavedSearchCreate(BaseModel):
    name: str
    query_text: Optional[str] = None
    filters: Optional[dict] = None


class SavedSearchResponse(BaseModel):
    id: str
    name: str
    query_text: Optional[str]
    filters: Optional[dict]
    is_pinned: bool
    use_count: int
    created_at: datetime


# ==================== Search Endpoints ====================

@router.post("/search", response_model=SearchResponse)
async def search_endpoints(
    request: SearchRequest,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Full-text search across all endpoints with filters.
    
    Supports:
    - Text search in path, description, parameters
    - Method filtering (GET, POST, etc.)
    - Tag filtering
    - Repository filtering
    - Pagination
    """
    org_id = current_user.get("organization_id")
    query_text = request.query.strip().lower()
    
    # Build base query
    base_query = (
        select(APIEndpoint, Repository)
        .join(Repository, APIEndpoint.repository_id == Repository.id)
        .where(Repository.organization_id == org_id)
    )
    
    # Apply text search
    if query_text:
        search_pattern = f"%{query_text}%"
        base_query = base_query.where(
            or_(
                APIEndpoint.path.ilike(search_pattern),
                APIEndpoint.description.ilike(search_pattern),
                APIEndpoint.summary.ilike(search_pattern)
            )
        )
    
    # Apply method filter
    if request.methods:
        base_query = base_query.where(APIEndpoint.method.in_(request.methods))
    
    # Apply repository filter
    if request.repositories:
        base_query = base_query.where(Repository.id.in_(request.repositories))
    
    # Apply tag filter (if tags stored in endpoint)
    if request.tags:
        for tag in request.tags:
            base_query = base_query.where(
                APIEndpoint.tags.contains([tag])
            )
    
    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (request.page - 1) * request.page_size
    paginated_query = base_query.offset(offset).limit(request.page_size)
    
    # Execute search
    result = await db.execute(paginated_query)
    rows = result.all()
    
    # Build results with highlighting
    results = []
    for endpoint, repo in rows:
        highlights = _highlight_matches(query_text, endpoint.path, endpoint.description)
        
        results.append(SearchResultItem(
            endpoint_id=str(endpoint.id),
            path=endpoint.path,
            method=endpoint.method,
            description=endpoint.description,
            repository_id=str(repo.id),
            repository_name=repo.name,
            tags=endpoint.tags,
            is_deprecated=endpoint.is_deprecated if hasattr(endpoint, 'is_deprecated') else False,
            score=_calculate_relevance(query_text, endpoint),
            highlights=highlights
        ))
    
    # Sort by relevance
    results.sort(key=lambda x: x.score, reverse=True)
    
    # Track search query for analytics
    if query_text:
        search_log = SearchQuery(
            organization_id=org_id,
            user_id=current_user.get("id"),
            query_text=query_text,
            query_type="text",
            filters={
                "methods": request.methods,
                "tags": request.tags,
                "repositories": request.repositories
            },
            result_count=total
        )
        db.add(search_log)
        await db.commit()
    
    # Get suggestions based on query
    suggestions = await _get_suggestions(query_text, org_id, db)
    
    return SearchResponse(
        query=request.query,
        total=total,
        page=request.page,
        page_size=request.page_size,
        results=results,
        suggestions=suggestions,
        filters_applied={
            "methods": request.methods,
            "tags": request.tags,
            "repositories": request.repositories
        }
    )


@router.get("/search/suggestions", response_model=SuggestionResponse)
async def get_search_suggestions(
    q: str = Query(default="", max_length=100),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get search suggestions based on partial query."""
    org_id_str = current_user.get("organization_id") if current_user else None
    user_id_str = current_user.get("id") if current_user else None
    
    # Return empty suggestions if no auth context
    if not org_id_str or not user_id_str:
        return SuggestionResponse(
            suggestions=[],
            recent_searches=[],
            popular_tags=[]
        )
    
    try:
        org_id = uuid.UUID(org_id_str)
        user_id = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        return SuggestionResponse(
            suggestions=[],
            recent_searches=[],
            popular_tags=[]
        )
    
    suggestions = []
    
    if q:
        # Get matching endpoint paths
        result = await db.execute(
            select(APIEndpoint.path)
            .join(Repository, APIEndpoint.repository_id == Repository.id)
            .where(
                Repository.organization_id == org_id,
                APIEndpoint.path.ilike(f"%{q}%")
            )
            .distinct()
            .limit(5)
        )
        paths = [row[0] for row in result.all()]
        suggestions.extend(paths)
        
        # Get matching descriptions
        result = await db.execute(
            select(APIEndpoint.summary)
            .join(Repository, APIEndpoint.repository_id == Repository.id)
            .where(
                Repository.organization_id == org_id,
                APIEndpoint.summary.ilike(f"%{q}%"),
                APIEndpoint.summary.isnot(None)
            )
            .distinct()
            .limit(3)
        )
        summaries = [row[0] for row in result.all() if row[0]]
        suggestions.extend(summaries[:3])
    
    # Get recent searches for user
    recent_result = await db.execute(
        select(SearchQuery.query_text)
        .where(
            SearchQuery.user_id == user_id,
            SearchQuery.organization_id == org_id
        )
        .order_by(desc(SearchQuery.searched_at))
        .distinct()
        .limit(5)
    )
    recent_searches = [row[0] for row in recent_result.all()]
    
    # Get popular tags
    result = await db.execute(
        select(APIEndpoint.tags)
        .join(Repository, APIEndpoint.repository_id == Repository.id)
        .where(
            Repository.organization_id == org_id,
            APIEndpoint.tags.isnot(None)
        )
        .limit(50)
    )
    all_tags = []
    for row in result.all():
        if row[0]:
            all_tags.extend(row[0])
    
    # Count tag frequency
    tag_counts = {}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    popular_tags = sorted(tag_counts.keys(), key=lambda x: tag_counts[x], reverse=True)[:10]
    
    return SuggestionResponse(
        suggestions=suggestions[:8],
        recent_searches=recent_searches,
        popular_tags=popular_tags
    )


# ==================== Saved Searches ====================

@router.get("/search/saved", response_model=List[SavedSearchResponse])
async def list_saved_searches(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """List user's saved searches."""
    user_id = current_user.get("id")
    
    result = await db.execute(
        select(SavedSearch)
        .where(SavedSearch.user_id == user_id)
        .order_by(desc(SavedSearch.is_pinned), desc(SavedSearch.use_count))
    )
    searches = result.scalars().all()
    
    return [
        SavedSearchResponse(
            id=str(s.id),
            name=s.name,
            query_text=s.query_text,
            filters=s.filters,
            is_pinned=s.is_pinned,
            use_count=s.use_count,
            created_at=s.created_at
        )
        for s in searches
    ]


@router.post("/search/saved", response_model=SavedSearchResponse)
async def save_search(
    data: SavedSearchCreate,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Save a search for quick access."""
    user_id = current_user.get("id")
    
    saved = SavedSearch(
        user_id=user_id,
        name=data.name,
        query_text=data.query_text,
        filters=data.filters
    )
    
    db.add(saved)
    await db.commit()
    await db.refresh(saved)
    
    return SavedSearchResponse(
        id=str(saved.id),
        name=saved.name,
        query_text=saved.query_text,
        filters=saved.filters,
        is_pinned=saved.is_pinned,
        use_count=saved.use_count,
        created_at=saved.created_at
    )


@router.delete("/search/saved/{search_id}")
async def delete_saved_search(
    search_id: str,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a saved search."""
    user_id = current_user.get("id")
    
    result = await db.execute(
        select(SavedSearch).where(
            SavedSearch.id == search_id,
            SavedSearch.user_id == user_id
        )
    )
    saved = result.scalar_one_or_none()
    
    if not saved:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    await db.delete(saved)
    await db.commit()
    
    return {"message": "Saved search deleted"}


# ==================== Search Analytics ====================

@router.get("/search/analytics")
async def get_search_analytics(
    days: int = Query(default=7, ge=1, le=30),
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_async_db)
):
    """Get search analytics for the organization."""
    org_id = current_user.get("organization_id")
    
    from datetime import timedelta
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total searches
    total_result = await db.execute(
        select(func.count(SearchQuery.id))
        .where(
            SearchQuery.organization_id == org_id,
            SearchQuery.searched_at >= start_date
        )
    )
    total_searches = total_result.scalar() or 0
    
    # Top queries
    top_queries_result = await db.execute(
        select(SearchQuery.query_text, func.count(SearchQuery.id).label('count'))
        .where(
            SearchQuery.organization_id == org_id,
            SearchQuery.searched_at >= start_date
        )
        .group_by(SearchQuery.query_text)
        .order_by(desc('count'))
        .limit(10)
    )
    top_queries = [{"query": row[0], "count": row[1]} for row in top_queries_result.all()]
    
    # Zero result queries
    zero_result = await db.execute(
        select(SearchQuery.query_text, func.count(SearchQuery.id).label('count'))
        .where(
            SearchQuery.organization_id == org_id,
            SearchQuery.searched_at >= start_date,
            SearchQuery.result_count == 0
        )
        .group_by(SearchQuery.query_text)
        .order_by(desc('count'))
        .limit(5)
    )
    zero_result_queries = [{"query": row[0], "count": row[1]} for row in zero_result.all()]
    
    return {
        "total_searches": total_searches,
        "top_queries": top_queries,
        "zero_result_queries": zero_result_queries,
        "period_days": days
    }


# ==================== Helper Functions ====================

def _highlight_matches(query: str, path: str, description: Optional[str]) -> dict:
    """Highlight matching text in search results."""
    if not query:
        return {}
    
    highlights = {}
    
    # Highlight in path
    if query.lower() in path.lower():
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        highlights["path"] = pattern.sub(f"<mark>{query}</mark>", path)
    
    # Highlight in description
    if description and query.lower() in description.lower():
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        highlights["description"] = pattern.sub(f"<mark>{query}</mark>", description)
    
    return highlights


def _calculate_relevance(query: str, endpoint) -> float:
    """Calculate relevance score for ranking."""
    if not query:
        return 1.0
    
    score = 0.0
    query_lower = query.lower()
    
    # Exact path match (highest)
    if query_lower == endpoint.path.lower():
        score += 100
    elif query_lower in endpoint.path.lower():
        score += 50
        # Bonus for path segment match
        if f"/{query_lower}" in endpoint.path.lower() or f"/{query_lower}/" in endpoint.path.lower():
            score += 20
    
    # Description match
    if endpoint.description and query_lower in endpoint.description.lower():
        score += 30
    
    # Summary match (title)
    if endpoint.summary and query_lower in endpoint.summary.lower():
        score += 40
    
    return score


async def _get_suggestions(query: str, org_id: str, db: AsyncSession) -> List[str]:
    """Get search suggestions based on query."""
    if not query or len(query) < 2:
        return []
    
    # Get similar paths
    result = await db.execute(
        select(APIEndpoint.path)
        .join(Repository, APIEndpoint.repository_id == Repository.id)
        .where(
            Repository.organization_id == org_id,
            APIEndpoint.path.ilike(f"%{query}%")
        )
        .distinct()
        .limit(5)
    )
    
    return [row[0] for row in result.all()]
