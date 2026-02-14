from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.extractor import extract_query_data
from services.mongo_search import search_products, search_products_by_brand
from services.ranker import rank_products
from utils import serialize_mongo_obj
import json

router = APIRouter(prefix="/ai", tags=["AI Search"])

class SearchQuery(BaseModel):
    query: str

@router.post("/search")
async def search(search_query: SearchQuery):
    try:
        # 1. Extract filters from query
        filters = extract_query_data(search_query.query)
        
        # 2. Search products (with filters)
        products = search_products(filters)
        
        message = "Success"
        filters_applied = filters
        
        # 3. Fallback Logic: If no results, try searching by brand only
        if not products and filters.get("brand"):
            print(f"No results found for detailed query. Switch to fallback for brand: {filters['brand']}")
            fallback_products = search_products_by_brand(filters["brand"])
            
            if fallback_products:
                products = fallback_products
                message = f"No exact matches found. Showing other {filters['brand']} products."
                # We clear other filters to show what we are actually showing
                filters_applied = {"brand": filters["brand"], "fallback": True}

        # 4. Rank products (Optional, but good for ordering)
        # We only rank if we have products and it's not a fallback (or maybe we do want to rank always?)
        if products and not filters_applied.get("fallback"):
             products = rank_products(products, filters)

        # 5. Generate AI Conversational Response
        from services.generator import generate_search_response
        ai_message = generate_search_response(search_query.query, products, filters_applied)

        return {
            "message": ai_message,
            "filters_applied": filters_applied,
            "total_results": len(products),
            "products": serialize_mongo_obj(products)
        }

    except Exception as e:
        print(f"Error processing search: {e}")
        raise HTTPException(status_code=500, detail=str(e))
