import json
from openai import OpenAI
from config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def extract_query_data(query: str):
    prompt = f"""
    Extract the following from this query:
    - category
    - brand
    - exclude_brand
    - price_min
    - price_max
    - features (as list)

    Query: "{query}"

    Return valid JSON only.
    If value not present, return null.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = response.choices[0].message.content.strip()

    # Clean markdown
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    
    content = content.strip()

    try:
        filters = json.loads(content)
    except json.JSONDecodeError:
        filters = {}

    # Safe price conversion
    if filters.get("price_min"):
        try:
            filters["price_min"] = int(filters["price_min"])
        except:
            filters["price_min"] = None

    if filters.get("price_max"):
        try:
            filters["price_max"] = int(filters["price_max"])
        except:
            filters["price_max"] = None

    # Normalize Category
    category_map = {
        "phone": "Mobile",
        "mobile": "Mobile",
        "cellphone": "Mobile",
        "smartphone": "Mobile",
        "laptop": "Laptops",
        "notebook": "Laptops",
        "shoe": "Shoes",
        "sneaker": "Shoes"
    }
    
    if filters.get("category"):
        cat_lower = filters["category"].lower()
        if cat_lower in category_map:
            filters["category"] = category_map[cat_lower]

    return filters
