from app.schemas.paginationSchema import PaginationMeta


def paginate(query, page: int, limit: int):
    """
    Paginate a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-indexed)
        limit: Number of items per page
    
    Returns:
        Tuple of (items, PaginationMeta)
    """
    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()
    total_pages = (total + limit - 1) // limit if limit > 0 else 0
    
    meta = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )
    
    return items, meta