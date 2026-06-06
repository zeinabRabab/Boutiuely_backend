from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import ProductResponse
from ai import get_recommendations

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/{product_id}", response_model=List[ProductResponse])
def recommend(
    product_id: int,
    top_n: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """
    Public — AI-powered product recommendations.
    Returns up to top_n products similar to the given product_id
    using TF-IDF cosine similarity on category, tags, color, description, and price range.
    """
    return get_recommendations(product_id, db, top_n=top_n)
