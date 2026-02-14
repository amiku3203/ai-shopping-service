def rank_products(products, filters):
    for product in products:
        score = 0

        # Brand boost
        if filters.get("brand") and product.get("brand") and filters["brand"].lower() == product["brand"].lower():
            score += 2

        # Feature keyword match
        if filters.get("features"):
            searchable_text = (
                product.get("description", "") + " " +
                " ".join(product.get("features", []))
            ).lower()

            for feature in filters["features"]:
                if feature and feature.lower() in searchable_text:
                    score += 1

        product["ai_score"] = score

    return sorted(products, key=lambda x: x["ai_score"], reverse=True)
