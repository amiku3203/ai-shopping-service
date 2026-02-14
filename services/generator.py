from openai import OpenAI
from config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_search_response(query: str, products: list, filters: dict):
    # Summarize top products for the context
    product_context = ""
    if products:
        for i, p in enumerate(products[:5]): # Only top 5 to save context window
            product_context += f"{i+1}. {p.get('productName')} - Price: {p.get('totalAmountAfterDiscount')} (Slug: {p.get('productSlug')})\n"
    else:
        product_context = "No products found matching the criteria."

    prompt = f"""
    You are a friendly and helpful AI Shopping Assistant for "Infinite Mart".
    
    User Query: "{query}"
    
    Filters extracted: {filters}
    
    Products found in database (Top 5):
    {product_context}
    
    Task:
    - Provide a helpful response to the user.
    - If products were found, recommend them based on the user's query. Highlight why they might be good choices.
    - If no products were found, apologize politely and suggest what else they could look for (e.g., general categories like shoes, mobiles).
    - Keep the tone professional but conversational.
    - Do NOT list all technical specs, just a brief summary.
    - Mention 1-2 specific products by name if they are really good matches.
    - Reference the "Slug" if you want to be specific, but mainly use the product Name.
    - Keep the response short (under 50 words if possible, max 80 words).
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful shopping assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating AI response: {e}")
        return "Here are the products I found for you!"
