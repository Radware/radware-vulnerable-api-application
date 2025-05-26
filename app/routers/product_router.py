from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from .. import db
from ..models.product_models import (
    Product,
    ProductCreate,
    ProductInDBBase,
    ProductUpdate,
    Stock,
    StockUpdate,
    StockInDBBase,
)
from ..models.user_models import (
    User,
)  # For potential future owner checks, though not used for BFLA demo
from ..routers.user_router import (
    get_current_user,
)  # Re-use existing dependency for consistency
from ..models.order_models import TokenData  # Ensure TokenData is imported

router = APIRouter()


@router.get("/products", response_model=List[Product], tags=["Products"])
async def list_all_products():
    """
    List all available products.
    """
    return [Product.model_validate(p) for p in db.db["products"]]


# BFLA Target: No admin check initially. Data via query parameters.
@router.post(
    "/products",
    response_model=Product,
    status_code=status.HTTP_201_CREATED,
    tags=["Products"],
)
async def create_new_product(
    name: str = Query(...),
    price: float = Query(...),
    description: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    # current_user: TokenData = Depends(get_current_user) # BFLA: No check for admin status
):
    """
    Create a new product.
    Intended BFLA: No admin check performed, allowing any authenticated user to create products.
    """
    print(
        f"Creating new product '{name}'. Intended BFLA: No admin check performed."
    )  # Logging for demo
    new_product_data = ProductCreate(
        name=name, price=price, description=description, category=category
    )
    product_in_db = ProductInDBBase(**new_product_data.model_dump())
    db.db["products"].append(product_in_db)

    # Initialize stock for the new product
    initial_stock = StockInDBBase(
        product_id=product_in_db.product_id, quantity=0
    )  # Default to 0 stock
    db.db["stock"].append(initial_stock)

    return Product.model_validate(product_in_db)


# SQL/NoSQL Injection Target. Naive implementation.
# IMPORTANT: This route is placed BEFORE /{product_id} to resolve routing ambiguity.
@router.get("/products/search", response_model=List[Product], tags=["Products"])
async def search_products_by_name(name: str = Query(...)):
    """
    Search for products by name (case-insensitive substring match).
    Intended Injection Target: Simulates vulnerability where 'name' could be unsafely used in a backend query.
    """
    print(
        f"Searching for product with name containing: '{name}'. Intended Injection Target."
    )
    # VULNERABILITY: Naive string matching, simulating how a direct query concatenation might behave.
    # In a real SQL/NoSQL scenario, `name` would be unsafely injected into a query.
    # For our in-memory store, we just do a simple substring match, but the intent is to show the input point.
    results = [
        Product.model_validate(p)
        for p in db.db["products"]
        if name.lower() in p.name.lower()
    ]

    # Simulate a scenario where an injection might cause an error or unexpected behavior
    if (
        "'" in name or ";" in name or "--" in name
    ):  # Very basic check for typical SQL injection characters
        # This is a placeholder. In a real app, this might cause a DB error or return unintended data.
        print(f"Potential injection characters detected in search term: {name}")
        # To make it more demonstrative for testing, if it looks like an attack, return empty or error.
        # raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Simulated query error due to suspicious input.")

    if not results:
        # To make it clear if a search yields nothing vs. an error for the demo
        # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No products found matching your query.")
        pass  # Allow empty results
    return results


@router.get("/products/{product_id}", response_model=Product, tags=["Products"])
async def get_product_by_id(product_id: UUID):
    """
    Get a product by its unique ID.
    """
    product = next((p for p in db.db["products"] if p.product_id == product_id), None)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return Product.model_validate(product)


# Parameter Pollution Target for internal_status. Data via query parameters.
@router.put("/products/{product_id}", response_model=Product, tags=["Products"])
async def update_existing_product(
    product_id: UUID,
    name: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    price: Optional[float] = Query(None),
    category: Optional[str] = Query(None),
    internal_status_param: Optional[str] = Query(
        None, alias="internal_status"
    ),  # Parameter pollution target
    # current_user: TokenData = Depends(get_current_user) # BFLA: No check for admin/owner
):
    """
    Update an existing product's details.
    Intended Parameter Pollution Target: 'internal_status' can be set by unprivileged users.
    Intended BFLA: No admin/owner check performed.
    """
    product_to_update = next(
        (p for p in db.db["products"] if p.product_id == product_id), None
    )
    if not product_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    # Use ProductUpdate model to get clean update data
    update_data = ProductUpdate(
        name=name,
        description=description,
        price=price,
        category=category,
        internal_status=internal_status_param,
    ).model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided"
        )

    for key, value in update_data.items():
        if (
            value is not None
        ):  # Ensure we only update fields that were actually passed (excluding unset)
            setattr(product_to_update, key, value)
            if key == "internal_status":
                print(
                    f"Product {product_id} internal_status being set to '{value}' via query param. Parameter Pollution Target."
                )

    product_to_update.updated_at = datetime.now(timezone.utc)
    return Product.model_validate(product_to_update)


# BFLA Target: No admin check initially.
@router.delete(
    "/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Products"]
)
async def delete_existing_product(
    product_id: UUID,
    # current_user: TokenData = Depends(get_current_user) # BFLA: No check for admin status
):
    """
    Delete an existing product.
    Intended BFLA: No admin check performed, allowing any authenticated user to delete products.
    """
    product_index = -1
    for i, p in enumerate(db.db["products"]):
        if p.product_id == product_id:
            product_index = i
            break

    if product_index == -1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    print(
        f"Deleting product {product_id}. Intended BFLA: No admin check performed."
    )  # Logging for demo
    db.db["products"].pop(product_index)
    # Also remove associated stock
    db.db["stock"] = [s for s in db.db["stock"] if s.product_id != product_id]
    # Consider implications for orders with this product (e.g., mark as unavailable, don't delete from historical orders)
    return


@router.get("/products/{product_id}/stock", response_model=Stock, tags=["Stock"])
async def get_product_stock_info(product_id: UUID):
    """
    Get stock information for a specific product.
    """
    stock_info = next((s for s in db.db["stock"] if s.product_id == product_id), None)
    product_exists = next(
        (p for p in db.db["products"] if p.product_id == product_id), None
    )

    if not product_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found, so no stock information available.",
        )

    if not stock_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock information not found for this product (possibly not initialized).",
        )
    return Stock.model_validate(stock_info)


# BFLA Target: No admin/owner check initially. Quantity via query parameter.
@router.put("/products/{product_id}/stock", response_model=Stock, tags=["Stock"])
async def update_product_stock_quantity(
    product_id: UUID,
    quantity: int = Query(..., ge=0),
    # current_user: TokenData = Depends(get_current_user) # BFLA: No check for admin/owner
):
    """
    Update the stock quantity for a product.
    Intended BFLA: No admin/owner check performed, allowing any authenticated user to modify stock.
    """
    stock_to_update = next(
        (s for s in db.db["stock"] if s.product_id == product_id), None
    )
    product_exists = next(
        (p for p in db.db["products"] if p.product_id == product_id), None
    )

    if not product_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found, cannot update stock.",
        )

    if hasattr(product_exists, "is_protected") and product_exists.is_protected:
        print(f"Updating stock for protected product {product_id}")

    if not stock_to_update:
        # If product exists but stock record doesn't, create it (could happen if product was added without stock init)
        print(f"Stock record for product {product_id} not found. Creating one.")
        stock_to_update = StockInDBBase(product_id=product_id, quantity=quantity)
        db.db["stock"].append(stock_to_update)
    else:
        stock_to_update.quantity = quantity

    stock_to_update.last_updated = datetime.now(timezone.utc)
    print(
        f"Updating stock for product {product_id} to quantity {quantity}. Intended BFLA: No admin/owner check performed."
    )  # Logging for demo
    return Stock.model_validate(stock_to_update)
