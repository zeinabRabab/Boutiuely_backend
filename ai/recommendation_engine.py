"""
AI Recommendation Engine
========================
Uses TF-IDF + cosine similarity on product features:
  - category, tags, color, description, price_range

Returns the top-N most similar products for a given product_id.
This is a content-based filtering approach — no user history required.
"""
import re
from typing import List, Optional

from sqlalchemy.orm import Session
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from models.product import Product
from schemas import ProductResponse


def _build_feature_string(product: Product) -> str:
    """
    Combine all product attributes into a single text feature string.
    Each field is weighted by repetition to increase its influence.
    """
    parts = []

    if product.category:
        parts.extend([product.category] * 3)   # category is highly important

    if product.tags:
        tags = [t.strip() for t in product.tags.split(",") if t.strip()]
        parts.extend(tags * 2)                  # tags are second most important

    if product.color:
        parts.extend([product.color] * 2)

    if product.description:
        # Clean description: lowercase, remove punctuation
        clean_desc = re.sub(r"[^a-zA-Z0-9\s]", "", product.description.lower())
        parts.append(clean_desc)

    # Discretize price into buckets so similar-priced items cluster together
    if product.price:
        if product.price < 30:
            parts.append("budget affordable cheap")
        elif product.price < 80:
            parts.append("mid-range moderate")
        elif product.price < 150:
            parts.append("premium quality")
        else:
            parts.append("luxury high-end designer")

    return " ".join(parts) if parts else product.name


def get_recommendations(
    product_id: int,
    db: Session,
    top_n: int = 6,
) -> List[ProductResponse]:
    """
    Return top_n products most similar to the given product_id.
    Uses cosine similarity over TF-IDF feature vectors.
    """
    products = db.query(Product).all()

    if len(products) < 2:
        return []

    # Build feature strings for all products
    df = pd.DataFrame([
        {"id": p.id, "features": _build_feature_string(p)}
        for p in products
    ])

    # TF-IDF vectorization
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    try:
        tfidf_matrix = vectorizer.fit_transform(df["features"])
    except ValueError:
        return []

    # Find index of the target product
    try:
        target_idx = df[df["id"] == product_id].index[0]
    except IndexError:
        return []

    # Compute cosine similarity between target and all products
    sim_scores = cosine_similarity(tfidf_matrix[target_idx], tfidf_matrix).flatten()

    # Sort by similarity descending, skip the product itself (score = 1.0)
    scored = sorted(
        enumerate(sim_scores),
        key=lambda x: x[1],
        reverse=True,
    )
    # Exclude the product itself
    similar_indices = [i for i, score in scored if df.iloc[i]["id"] != product_id][:top_n]

    similar_ids = [df.iloc[i]["id"] for i in similar_indices]
    similar_products = [p for p in products if p.id in similar_ids]

    return [ProductResponse.model_validate(p) for p in similar_products]
