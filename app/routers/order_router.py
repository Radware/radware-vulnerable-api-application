from fastapi import APIRouter, HTTPException, status, Query, Depends, Request
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime, timezone

from .. import db
from ..models.order_models import Order, OrderCreate, OrderInDBBase, OrderItem, OrderItemCreate, OrderItemInDBBase, TokenData
from ..models.product_models import Product, Stock
from ..models.user_models import User, Address, CreditCard
from ..routers.user_router import get_current_user # Reuse the dependency

router = APIRouter(
    prefix="/users/{user_id}/orders", # Common prefix
    tags=["Orders"]
)

# Helper to find product and stock
def get_product_and_stock(product_id: UUID):
    product = next((p for p in db.db["products"] if p.product_id == product_id), None)
    if not product:
        return None, None
    stock = next((s for s in db.db["stock"] if s.product_id == product_id), None)
    return product, stock

@router.get("", response_model=List[Order])
async def list_user_orders(
    user_id: UUID, 
    current_user: TokenData = Depends(get_current_user)
):
    # BOLA Vulnerability: Authenticated, but no check if current_user.user_id matches path user_id.
    print(f"Listing orders for user {user_id}. Authenticated user: {current_user.user_id}. BOLA: No ownership check.")

    # Check if the user_id from path even exists
    path_user_exists = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if not path_user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found.")

    user_orders_db = [o for o in db.db["orders"] if o.user_id == user_id]
    response_orders = []
    for order_db in user_orders_db:
        items_db = [item for item in db.db["order_items"] if item.order_id == order_db.order_id]
        order_response = Order.model_validate(order_db)
        order_response.items = [OrderItem.model_validate(item) for item in items_db]
        card = next(
            (cc for cc in db.db["credit_cards"] if cc.card_id == order_db.credit_card_id),
            None,
        )
        if card:
            order_response.credit_card_last_four = card.card_last_four
        response_orders.append(order_response)
    return response_orders

@router.post("", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_user_order(
    user_id: UUID, # User ID from path - BOLA target
    request: Request, # To access all query parameters
    current_user: TokenData = Depends(get_current_user)
):
    # BOLA Vulnerability for user_id in path:
    # No check if current_user.user_id matches path user_id.
    print(f"Attempting to create order for user {user_id} by authenticated user {current_user.user_id}. BOLA on user_id in path.")

    query_params = request.query_params
    address_id_str = query_params.get("address_id")
    credit_card_id_str = query_params.get("credit_card_id")

    if not address_id_str or not credit_card_id_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="address_id and credit_card_id are required query parameters.")

    try:
        address_id = UUID(address_id_str)
        credit_card_id = UUID(credit_card_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID format for address_id or credit_card_id.")

    # BOLA Vulnerability for address_id and credit_card_id from query:
    # The system does not validate if the provided address_id and credit_card_id belong to the user_id in the path OR the authenticated user.
    # An attacker could use another user's address_id or credit_card_id if known/guessable.
    print(f"Order creation using address_id: {address_id} and credit_card_id: {credit_card_id}. BOLA on these IDs if not owned by user {user_id} or {current_user.user_id}.")

    # Validate existence of user, address, and credit card (without checking ownership for BOLA demo)
    target_user_exists = next((u for u in db.db["users"] if u.user_id == user_id), None)
    if not target_user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target user with ID {user_id} not found.")

    address_exists = next((a for a in db.db["addresses"] if a.address_id == address_id), None)
    if not address_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Address with ID {address_id} not found.")
    # BOLA: We don't check if address_exists.user_id == user_id or current_user.user_id

    credit_card_exists = next((cc for cc in db.db["credit_cards"] if cc.card_id == credit_card_id), None)
    if not credit_card_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Credit Card with ID {credit_card_id} not found.")
    # BOLA: We don't check if credit_card_exists.user_id == user_id or current_user.user_id

    parsed_products: Dict[UUID, int] = {}
    i = 1
    while True:
        product_id_str = query_params.get(f"product_id_{i}")
        quantity_str = query_params.get(f"quantity_{i}")
        if not product_id_str or not quantity_str:
            break
        try:
            product_id = UUID(product_id_str)
            quantity = int(quantity_str)
            if quantity <= 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Quantity for product_id_{i} must be positive.")
            parsed_products[product_id] = parsed_products.get(product_id, 0) + quantity
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid format for product_id_{i} or quantity_{i}.")
        i += 1

    if not parsed_products:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No products specified for the order.")

    new_order_db = OrderInDBBase(user_id=user_id, address_id=address_id, credit_card_id=credit_card_id)
    db.db["orders"].append(new_order_db)

    created_order_items_db: List[OrderItemInDBBase] = []
    current_total_amount = 0.0

    for product_id_key, quantity_val in parsed_products.items():
        product, stock = get_product_and_stock(product_id_key)
        if not product:
            # Rollback order creation (simplified: remove order from db)
            db.db["orders"].remove(new_order_db)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ID {product_id_key} not found.")
        if not stock or stock.quantity < quantity_val:
            db.db["orders"].remove(new_order_db)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Insufficient stock for product {product.name} (ID: {product_id_key}). Available: {stock.quantity if stock else 0}, Requested: {quantity_val}")
        
        # Deduct stock
        stock.quantity -= quantity_val
        stock.last_updated = datetime.now(timezone.utc)
        
        price_at_purchase = product.price
        order_item_db = OrderItemInDBBase(
            order_id=new_order_db.order_id,
            product_id=product_id_key,
            quantity=quantity_val,
            price_at_purchase=price_at_purchase
        )
        db.db["order_items"].append(order_item_db)
        created_order_items_db.append(order_item_db)
        current_total_amount += price_at_purchase * quantity_val
    
    new_order_db.total_amount = round(current_total_amount, 2)
    new_order_db.updated_at = datetime.now(timezone.utc)

    # Prepare response model
    order_response = Order.model_validate(new_order_db)
    order_response.items = [OrderItem.model_validate(item) for item in created_order_items_db]
    card = next(
        (cc for cc in db.db["credit_cards"] if cc.card_id == new_order_db.credit_card_id),
        None,
    )
    if card:
        order_response.credit_card_last_four = card.card_last_four
    
    print(f"Order {new_order_db.order_id} created successfully for user {user_id} with total {new_order_db.total_amount}.")
    return order_response


@router.get("/{order_id}", response_model=Order)
async def get_user_order_by_id(
    user_id: UUID, 
    order_id: UUID, 
    current_user: TokenData = Depends(get_current_user)
):
    # BOLA Vulnerability: No check if current_user.user_id matches path user_id.
    print(f"Fetching order {order_id} for user {user_id}. Authenticated user: {current_user.user_id}. BOLA: No ownership check.")

    order_db = next((o for o in db.db["orders"] if o.order_id == order_id and o.user_id == user_id), None)
    if not order_db:
        # Check if user exists first to give a more specific error, or if order just doesn't belong to them / doesn't exist
        path_user_exists = next((u for u in db.db["users"] if u.user_id == user_id), None)
        if not path_user_exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with ID {order_id} not found for user {user_id}.")

    items_db = [item for item in db.db["order_items"] if item.order_id == order_db.order_id]

    order_response = Order.model_validate(order_db)
    order_response.items = [OrderItem.model_validate(item) for item in items_db]
    card = next(
        (cc for cc in db.db["credit_cards"] if cc.card_id == order_db.credit_card_id),
        None,
    )
    if card:
        order_response.credit_card_last_four = card.card_last_four
    return order_response
