import math
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from schemas import MovieDetailResponseSchema
from src.database import get_db, MovieModel
from src.schemas import MovieListResponseSchema
router = APIRouter()


@router.get("/movies/")
async def get_movie_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=20)
) -> MovieListResponseSchema:
    result = await db.execute(select(func.count(MovieModel.id)))
    total_items = result.scalar()
    if not total_items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")
    total_pages = math.ceil(total_items / per_page)
    offset = (page - 1) * per_page
    result = await db.scalars(select(MovieModel).offset(offset).limit(per_page))
    movies = result.all()
    if not movies:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")
    base_url = request.url.path
    prev_page = (
        f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None
    )
    return MovieListResponseSchema(
        movies=movies,
        prev_page=prev_page,
        next_page=next_page,
        total_pages=total_pages,
        total_items=total_items
    )


@router.get("/movies/{movie_id}/")
async def get_movie_details(movie_id: int, db: AsyncSession = Depends(get_db)) -> MovieDetailResponseSchema:
    if movie_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid movie_id: {movie_id}. Must be positive."
        )

    try:
        result = await db.get(MovieModel, movie_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not Found"
            )
        return MovieDetailResponseSchema.model_validate(result)

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred."
        ) from e
