from db.mongo import products_collection

def get_summary_projection():
    """
    Returns the MongoDB projection for standard product summaries.
    Excludes heavy fields like description.
    """
    return {
        "_id": 1,
        "productName": 1,
        "productSlug": 1,
        "productImage": 1, 
        "price": 1,
        "discount": 1, 
        "totalAmountAfterDiscount": 1,
        "brand": 1,
        "category": 1,
        "features": 1,
        "summary": 1,       # Added AI summary
        "averageRating": 1, 
        "numReviews": 1     
    }

def search_products(filters: dict):
    print(f"DEBUG: Filters: {filters}")
    query = {}

    # Brand + Exclude Brand logic
    # Now using the direct 'brand' field since we migrated data
    if filters.get("brand"):
        brand_query = {"$regex": filters["brand"], "$options": "i"} 
        
        if filters.get("exclude_brand"):
             query["$and"] = [
                 {"brand": brand_query},
                 {"brand": {"$not": {"$regex": filters["exclude_brand"], "$options": "i"}}}
             ]
        else:
            query["brand"] = brand_query

    elif filters.get("exclude_brand"):
        query["brand"] = {"$not": {"$regex": filters["exclude_brand"], "$options": "i"}}

    # Price filter
    # Using 'totalAmountAfterDiscount' per user schema
    if filters.get("price_min") or filters.get("price_max"):
        query["totalAmountAfterDiscount"] = {}

        if filters.get("price_min") is not None:
            query["totalAmountAfterDiscount"]["$gte"] = filters["price_min"]

        if filters.get("price_max") is not None:
            query["totalAmountAfterDiscount"]["$lte"] = filters["price_max"]

    # Category
    # Now using the direct 'category' field since we migrated data
    if filters.get("category"):
        query["category"] = {"$regex": filters["category"], "$options": "i"}

    # Execute query
    with open("debug_log.txt", "a") as f:
        f.write(f"DEBUG: Filters: {filters}\n")
        f.write(f"DEBUG: Final Query: {query}\n")
    
    # Use projection to limit fields
    results = list(
        products_collection.find(query, get_summary_projection()).limit(20)
    )

    return results

def search_products_by_brand(brand: str):
    """
    Fallback search: find products by brand only.
    """
    if not brand:
        return []

    query = {"brand": {"$regex": brand, "$options": "i"}}
    
    return list(
        products_collection.find(query, get_summary_projection()).limit(10)
    )
