import sys
import os
from unittest.mock import MagicMock

# --- Global Mocking BEFORE Imports ---
# We must mock db.mongo to prevent real connection attempt at import time
sys.modules["db"] = MagicMock()
sys.modules["db.mongo"] = MagicMock()
sys.modules["pymongo"] = MagicMock()

# Now we can safely import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch

# Fix the mocked products_collection for later use in tests
# Since we mocked the whole module, we need to ensure search_products can access a collection
# But wait, search_products imports `products_collection` from `db.mongo`.
# So `from services.mongo_search import search_products` will get `Unittest.mock.MagicMock` as `products_collection`.
# That is fine, we can configure it in the test function.

client = TestClient(app)

def test_search_flow():
    """Test basic search functionality"""
    print("\n--- Testing Search Flow ---")
    response = client.post("/agent/chat", json={"query": "iphone"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) > 0

@patch("services.workflow.requests.get")
def test_order_flow_no_login(mock_get):
    """Test order attempt without login"""
    print("\n--- Testing Order Flow (No Login) ---")
    response = client.post("/agent/chat", json={"query": "buy iphone"})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200 # It returns 200 but context should indicate failure/end
    # With current logic, if intent is order and no user, it goes to END immediately 
    # Logic: route_intent returns END if order & no user
    # So messages might be empty or default. 
    # Let's check if it failed gracefully.

@patch("services.workflow.requests.get") # Mock user info
@patch("services.workflow.requests.post") # Mock order creation
@patch("services.mongo_search.products_collection.find") # Mock Mongo
def test_order_flow_success(mock_mongo_find, mock_post, mock_get):
    """Test full order flow with mocks"""
    print("\n--- Testing Order Flow (Success) ---")
    
    # Mock User
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"user": {"_id": "u1", "name": "Test User"}}
    
    # Mock Product (Stock > 0)
    mock_product = {
        "_id": "p1", 
        "productName": "iPhone 15", 
        "price": 1000, 
        "totalAmountAfterDiscount": 1000,
        "stock": 10,
        "productImage": ["img.jpg"]
    }
    # Mock Mongo Cursor
    mock_cursor = MagicMock()
    mock_cursor.limit.return_value = [mock_product]
    mock_mongo_find.return_value = mock_cursor

    # Mock Order Creation
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"order": {"_id": "order_123"}}

    # Call with Token
    response = client.post(
        "/agent/chat", 
        json={"query": "buy iphone", "history": []}, 
        headers={"Authorization": "Bearer valid_token"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert "Order created successfully!" in data["messages"][0]
    assert data["next_step"] == "end"

if __name__ == "__main__":
    try:
        test_search_flow()
        test_order_flow_no_login()
        test_order_flow_success()
        print("\n✅ All Tests Passed!")
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
