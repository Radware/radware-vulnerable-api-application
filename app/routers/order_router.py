from fastapi import APIRouter, HTTPException, status, Query, Depends, Request
from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime, timezone

from .. import db
from ..models.order_models import (
    Order,
    OrderCreate,
    OrderInDBBase,
    OrderItem,
    OrderItemCreate,
    OrderItemInDBBase,
    TokenData,
)
from ..models.product_models import Product, Stock
from ..models.user_models import User, Address, CreditCard
from ..models.coupon_models import Coupon
from ..routers.user_router import get_current_user  # Reuse the dependency

# --- VULNERABILITY INJECTION: Insecure cache for pending coupons ---
# This dictionary will map a user_id to a coupon_code they've tried to apply.
pending_coupons_cache: Dict[UUID, str] = {}
# --- END VULNERABILITY INJECTION ---

router = APIRouter(prefix="/users/{user_id}/orders", tags=["Orders"])  # Common prefix


# Helper to find product and stock
def get_product_and_stock(product_id: UUID):
    product = db.db_products_by_id.get(product_id)
    if not product:
        return None, None
    stock = db.db_stock_by_product_id.get(product_id)
    return product, stock


@router.get("", response_model=List[Order])
async def list_user_orders(
    user_id: UUID, current_user: TokenData = Depends(get_current_user)
):
    # BOLA Vulnerability: Authenticated, but no check if current_user.user_id matches path user_id.
    print(
        f"Listing orders for user {user_id}. Authenticated user: {current_user.user_id}. BOLA: No ownership check."
    )

    # Check if the user_id from path even exists
    path_user_exists = db.db_users_by_id.get(user_id)
    if not path_user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    user_order_objects = db.db_orders_by_user_id.get(user_id, [])
    response_orders = []
    for order_db in user_order_objects:
        items_for_this_order = db.db_order_items_by_order_id.get(order_db.order_id, [])
        order_response = Order.model_validate(order_db)
        order_response.items = [
            OrderItem.model_validate(item) for item in items_for_this_order
        ]
        card = db.db_credit_cards_by_id.get(order_db.credit_card_id)
        if card:
            order_response.credit_card_last_four = card.card_last_four
        response_orders.append(order_response)
    return response_orders


@router.post("", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_user_order(
    user_id: UUID,  # User ID from path - BOLA target
    request: Request,  # To access all query parameters
    current_user: TokenData = Depends(get_current_user),
):
    # BOLA Vulnerability for user_id in path:
    # No check if current_user.user_id matches path user_id.
    print(
        f"Attempting to create order for user {user_id} by authenticated user {current_user.user_id}. BOLA on user_id in path."
    )

    query_params = request.query_params
    address_id_str = query_params.get("address_id")
    credit_card_id_str = query_params.get("credit_card_id")

    if not address_id_str or not credit_card_id_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="address_id and credit_card_id are required query parameters.",
        )

    try:
        address_id = UUID(address_id_str)
        credit_card_id = UUID(credit_card_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format for address_id or credit_card_id.",
        )

    # BOLA Vulnerability for address_id and credit_card_id from query:
    # The system does not validate if the provided address_id and credit_card_id belong to the user_id in the path OR the authenticated user.
    # An attacker could use another user's address_id or credit_card_id if known/guessable.
    print(
        f"Order creation using address_id: {address_id} and credit_card_id: {credit_card_id}. BOLA on these IDs if not owned by user {user_id} or {current_user.user_id}."
    )

    # Validate existence of user, address, and credit card (without checking ownership for BOLA demo)
    target_user_exists = db.db_users_by_id.get(user_id)
    if not target_user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target user with ID {user_id} not found.",
        )

    address_exists = db.db_addresses_by_id.get(address_id)
    if not address_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Address with ID {address_id} not found.",
        )
    # BOLA: We don't check if address_exists.user_id == user_id or current_user.user_id

    credit_card_exists = db.db_credit_cards_by_id.get(credit_card_id)
    if not credit_card_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credit Card with ID {credit_card_id} not found.",
        )
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
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Quantity for product_id_{i} must be positive.",
                )
            parsed_products[product_id] = parsed_products.get(product_id, 0) + quantity
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid format for product_id_{i} or quantity_{i}.",
            )
        i += 1

    if not parsed_products:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No products specified for the order.",
        )

    # The order should always be owned by the authenticated user (attacker).
    # user_id from the path may be a victim when BOLA is exploited.
    new_order_db = OrderInDBBase(
        user_id=current_user.user_id,
        address_id=address_id,
        credit_card_id=credit_card_id,
    )
    db.db["orders"].append(new_order_db)
    db.db_orders_by_id[new_order_db.order_id] = new_order_db
    db.db_orders_by_user_id.setdefault(current_user.user_id, []).append(new_order_db)

    created_order_items_db: List[OrderItemInDBBase] = []
    current_total_amount = 0.0

    for product_id_key, quantity_val in parsed_products.items():
        product, stock = get_product_and_stock(product_id_key)
        if not product:
            # Rollback order creation (simplified: remove order from db)
            db.db["orders"].remove(new_order_db)
            db.db_orders_by_id.pop(new_order_db.order_id, None)
            if new_order_db in db.db_orders_by_user_id.get(current_user.user_id, []):
                db.db_orders_by_user_id[current_user.user_id].remove(new_order_db)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id_key} not found.",
            )
        if not stock or stock.quantity < quantity_val:
            db.db["orders"].remove(new_order_db)
            db.db_orders_by_id.pop(new_order_db.order_id, None)
            if new_order_db in db.db_orders_by_user_id.get(current_user.user_id, []):
                db.db_orders_by_user_id[current_user.user_id].remove(new_order_db)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {product.name} (ID: {product_id_key}). Available: {stock.quantity if stock else 0}, Requested: {quantity_val}",
            )

        # Deduct stock
        stock.quantity -= quantity_val
        stock.last_updated = datetime.now(timezone.utc)

        price_at_purchase = product.price
        order_item_db = OrderItemInDBBase(
            order_id=new_order_db.order_id,
            product_id=product_id_key,
            quantity=quantity_val,
            price_at_purchase=price_at_purchase,
        )
        db.db["order_items"].append(order_item_db)
        db.db_order_items_by_id[order_item_db.order_item_id] = order_item_db
        db.db_order_items_by_order_id.setdefault(new_order_db.order_id, []).append(
            order_item_db
        )
        created_order_items_db.append(order_item_db)
        current_total_amount += price_at_purchase * quantity_val

    new_order_db.total_amount = round(current_total_amount, 2)
    new_order_db.updated_at = datetime.now(timezone.utc)

    # --- START OF VULNERABILITY INJECTION ---
    # Check the insecure cache for a pending coupon for this user
    if user_id in pending_coupons_cache:
        coupon_code_to_apply = pending_coupons_cache.pop(
            user_id
        )  # Get and remove from cache
        coupon = db.db_coupons_by_code.get(coupon_code_to_apply)
        if coupon:
            print(
                f"VULNERABILITY: Found and applying cached coupon '{coupon.code}' to new order {new_order_db.order_id}."
            )

            # Re-apply the coupon logic here
            if coupon.discount_type == "percentage":
                discount = round(
                    new_order_db.total_amount * (coupon.discount_value / 100), 2
                )
            else:
                discount = coupon.discount_value

            if discount > new_order_db.total_amount:
                discount = new_order_db.total_amount

            new_order_db.total_amount = round(new_order_db.total_amount - discount, 2)
            new_order_db.applied_coupon_id = coupon.coupon_id
            new_order_db.applied_coupon_code = coupon.code
            new_order_db.discount_amount = round(discount, 2)

            # Also increment usage count on the actual coupon
            coupon.usage_count += 1
            if (
                coupon.is_protected
                and coupon.usage_limit is not None
                and coupon.usage_count >= coupon.usage_limit
            ):
                coupon.usage_count = 0
            coupon.updated_at = datetime.now(timezone.utc)
    # --- END OF VULNERABILITY INJECTION ---

    # Prepare response model
    order_response = Order.model_validate(new_order_db)
    order_response.items = [
        OrderItem.model_validate(item) for item in created_order_items_db
    ]
    card = db.db_credit_cards_by_id.get(new_order_db.credit_card_id)
    if card:
        order_response.credit_card_last_four = card.card_last_four

    print(
        f"Order {new_order_db.order_id} created successfully for user {user_id} with total {new_order_db.total_amount}."
    )
    return order_response


@router.get("/{order_id}", response_model=Order)
async def get_user_order_by_id(
    user_id: UUID, order_id: UUID, current_user: TokenData = Depends(get_current_user)
):
    # BOLA Vulnerability: No check if current_user.user_id matches path user_id.
    print(
        f"Fetching order {order_id} for user {user_id}. Authenticated user: {current_user.user_id}. BOLA: No ownership check."
    )

    order_db = db.db_orders_by_id.get(order_id)
    if not order_db or order_db.user_id != user_id:
        path_user_exists = db.db_users_by_id.get(user_id)
        if not path_user_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found.",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found for user {user_id}.",
        )

    items_for_this_order = db.db_order_items_by_order_id.get(order_db.order_id, [])

    order_response = Order.model_validate(order_db)
    order_response.items = [
        OrderItem.model_validate(item) for item in items_for_this_order
    ]
    card = db.db_credit_cards_by_id.get(order_db.credit_card_id)
    if card:
        order_response.credit_card_last_four = card.card_last_four
    return order_response


@router.post("/{order_id}/apply-coupon", response_model=Order)
async def apply_coupon_to_order(
    user_id: UUID,
    order_id: UUID,
    coupon_code: str = Query(...),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Apply a coupon to an existing order.
    INTENTIONALLY VULNERABLE VERSION: If the order doesn't exist, this function
    will insecurely cache the coupon intent for the user, which can be
    exploited by the next order creation.
    """
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action for the specified user",
        )

    order_db = db.db_orders_by_id.get(order_id)

    # --- START OF VULNERABLE LOGIC ---
    if not order_db:
        # VULNERABILITY: Order does not exist. Instead of failing, we cache the coupon.
        coupon = db.db_coupons_by_code.get(coupon_code)
        if coupon and coupon.is_active:
            print(
                f"VULNERABILITY: Order {order_id} not found. Caching coupon '{coupon_code}' for user {user_id}."
            )
            pending_coupons_cache[user_id] = coupon_code
            # Lie to the attacker and pretend it worked by returning a fake, minimal order object.
            fake_order_response = {
                "order_id": order_id,
                "user_id": user_id,
                "status": "pending_confirmation",
                "applied_coupon_code": coupon_code,
                "total_amount": -1.0,
                "address_id": "00000000-0000-0000-0000-000000000000",
                "credit_card_id": "00000000-0000-0000-0000-000000000000",
                "items": [],
            }
            return Order.model_validate(fake_order_response)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Coupon not found or inactive",
            )
    # --- END OF VULNERABLE LOGIC ---

    if order_db.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this order",
        )

    if order_db.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot apply coupon to a non-pending order",
        )

    if order_db.applied_coupon_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon already applied to this order",
        )

    coupon = db.db_coupons_by_code.get(coupon_code)
    if not coupon or not coupon.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found or inactive"
        )

    if coupon.usage_limit is not None and coupon.usage_count >= coupon.usage_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon usage limit reached"
        )

    if coupon.discount_type == "percentage":
        discount = round(order_db.total_amount * (coupon.discount_value / 100), 2)
    else:
        discount = coupon.discount_value

    if discount > order_db.total_amount:
        discount = order_db.total_amount

    order_db.total_amount = round(order_db.total_amount - discount, 2)
    order_db.applied_coupon_id = coupon.coupon_id
    order_db.applied_coupon_code = coupon.code
    order_db.discount_amount = round(discount, 2)
    order_db.updated_at = datetime.now(timezone.utc)

    coupon.usage_count += 1
    coupon.updated_at = datetime.now(timezone.utc)

    items_for_this_order = db.db_order_items_by_order_id.get(order_db.order_id, [])
    order_response = Order.model_validate(order_db)
    order_response.items = [
        OrderItem.model_validate(item) for item in items_for_this_order
    ]
    card = db.db_credit_cards_by_id.get(order_db.credit_card_id)
    if card:
        order_response.credit_card_last_four = card.card_last_four
    return order_response
