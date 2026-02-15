from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
import requests
import json
from config import settings
from services.mongo_search import search_products
from services.extractor import extract_query_data

# -----------------
# 1. State Definition
# -----------------
class AgentState(TypedDict):
    query: str
    chat_history: List[dict]
    token: Optional[str]
    user_info: Optional[dict]
    intent: Optional[str]  # "search", "order", "track"
    
    # Order Flow Data
    product: Optional[dict]
    quantity: int
    address: Optional[dict]
    payment_method: Optional[str]
    
    # Response
    messages: List[str]
    next_step: Optional[str]

# -----------------
# 2. Nodes
# -----------------

def check_login(state: AgentState):
    """Checks if user is logged in via FT_NODE API"""
    token = state.get("token")
    if not token:
        return {"user_info": None}
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        # Assuming FT_NODE API URL is accessible
        response = requests.get(f"{settings.FT_API_URL}/api/user/me", headers=headers)
        if response.status_code == 200:
            return {"user_info": response.json().get("user")}
    except Exception as e:
        print(f"Error checking login: {e}")
    
    return {"user_info": None}

def analyze_intent(state: AgentState):
    """Analyzes user query to determine intent"""
    query = state["query"].lower()
    
    # Simple keyword matching for now (can be upgraded to LLM)
    if "buy" in query or "order" in query:
        return {"intent": "order"}
    elif "track" in query or "status" in query:
        return {"intent": "track"}
    else:
        return {"intent": "search"}

def search_product_node(state: AgentState):
    """Searches for product if intent is order/search"""
    query = state["query"]
    
    filters = extract_query_data(query)
    products = search_products(filters)
    
    if products:
        # If ordering, auto-select first result for simplicity in this MVP
        return {"product": products[0], "messages": [f"Found {products[0]['productName']}"]}
    
    return {"product": None, "messages": ["Product not found."]}

def check_stock(state: AgentState):
    """Checks stock for selected product"""
    product = state.get("product")
    if not product:
        return {"messages": ["No product selected."], "next_step": "end"}
    
    if product.get("stock", 0) > 0:
        return {"messages": [f"{product['productName']} is in stock."]}
    else:
        return {"messages": ["Sorry, this product is out of stock."], "next_step": "end"}

def collect_info(state: AgentState):
    """Collects missing order info (Quantity -> Address -> Payment)"""
    updates = {}
    if not state.get("quantity"):
        updates["quantity"] = 1
        
    if not state.get("payment_method"):
        updates["payment_method"] = "COD" # Default to COD
        
    # Mocking address for MVP as it's complex to gather via single turn
    updates["address"] = {
        "address": "123 Main St",
        "city": "Tech City",
        "postalCode": "123456",
        "country": "India"
    }
    
    return updates

def create_order(state: AgentState):
    """Calls FT_NODE to create order"""
    user = state.get("user_info")
    product = state.get("product")
    token = state.get("token")
    address = state.get("address")
    
    if not user or not product or not token or not address:
        return {"messages": ["Cannot create order: Missing info."]}
    
    try:
        # Calculate totals
        price = product.get("totalAmountAfterDiscount", product["price"])
        quantity = state.get("quantity", 1)
        total = price * quantity

        payload = {
            "orderItems": [{
                "product": str(product["_id"]),
                "name": product["productName"],
                "price": price,
                "image": product["productImage"][0] if product["productImage"] else "",
                "quantity": quantity
            }],
            "shippingAddress": address,
            "paymentMethod": state.get("payment_method", "COD"),
            "itemsPrice": total,
            "shippingPrice": 0,
            "totalPrice": total,
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        # Note: In config.py we updated FT_API_URL
        response = requests.post(f"{settings.FT_API_URL}/api/order/createOrder", json=payload, headers=headers)
        
        if response.status_code == 201:
            order_data = response.json()
            # Handle different response structures if needed
            order_id = order_data.get("order", {}).get("_id") or "created"
            return {"messages": ["Order created successfully!", f"Order ID: {order_id}"], "next_step": "end"}
        else:
            return {"messages": [f"Failed to create order: {response.text}"], "next_step": "end"}
            
    except Exception as e:
        return {"messages": [f"Error creating order: {str(e)}"], "next_step": "end"}

def login_required_node(state: AgentState):
    return {"messages": ["You need to be logged in to place an order. Please log in first."], "next_step": "end"}


# -----------------
# 3. Graph Construction
# -----------------
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("check_login", check_login)
workflow.add_node("analyze_intent", analyze_intent)
workflow.add_node("search_product", search_product_node)
workflow.add_node("check_stock", check_stock)
workflow.add_node("collect_info", collect_info)
workflow.add_node("create_order", create_order)
workflow.add_node("login_required", login_required_node)

# Set Entry Point
workflow.set_entry_point("check_login")

# Add Edges
workflow.add_edge("check_login", "analyze_intent")

def route_intent(state: AgentState):
    intent = state.get("intent")
    user = state.get("user_info")
    
    if intent == "order":
        if not user:
            return "login_required"  # Must login first
        return "search_product"
    elif intent == "search":
        return "search_product"
    else:
        return "search_product"

workflow.add_conditional_edges(
    "analyze_intent",
    route_intent,
    {
        "search_product": "search_product",
        "login_required": "login_required",
        END: END
    }
)

def route_search_result(state: AgentState):
    if state.get("intent") == "order" and state.get("product"):
        return "check_stock"
    return END

workflow.add_conditional_edges(
    "search_product",
    route_search_result,
    {
        "check_stock": "check_stock",
        END: END
    }
)

def route_stock_check(state: AgentState):
    if state.get("next_step") == "end":
        return END
    return "collect_info"

workflow.add_conditional_edges(
    "check_stock",
    route_stock_check,
    {
        "collect_info": "collect_info",
        END: END
    }
)

workflow.add_edge("collect_info", "create_order")
workflow.add_edge("create_order", END)
workflow.add_edge("login_required", END)

# Compile
app = workflow.compile()
