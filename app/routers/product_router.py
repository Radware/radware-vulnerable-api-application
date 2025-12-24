from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
import logging

from .. import db
from ..models.product_models import (
    Product,
    ProductCreate,
    ProductInDBBase,
    ProductUpdate,
    ProductWithStock,
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

logger = logging.getLogger(__name__)

router = APIRouter()

# Minimum stock allowed for protected products when using the direct update
# endpoint. Regular purchasing can still reduce stock normally.
PROTECTED_STOCK_MINIMUM = 500_000



@router.get("/products", response_model=List[Product], tags=["Products"])
async def list_all_products():
    """
    List all available products.
    """
    return [Product.model_validate(p) for p in db.db["products"]]


@router.get(
    "/products/with-stock",
    response_model=List[ProductWithStock],
    tags=["Products", "Stock"],
)
async def list_products_with_stock():
    """
    List all products along with their stock quantities.
    """
    products = list(db.db["products"])
    product_ids = [product.product_id for product in products]
    stock_by_product_id = db.list_stock_for_products(product_ids)

    response: List[ProductWithStock] = []
    for product in products:
        product_data = product.model_dump()
        stock = stock_by_product_id.get(product.product_id)
        response.append(
            ProductWithStock(
                **product_data,
                stock_quantity=stock.quantity if stock is not None else 0,
            )
        )
    return response


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
    logger.info(
        "Creating new product '%s'. Intended BFLA: No admin check performed.",
        name,
    )
    new_product_data = ProductCreate(
        name=name, price=price, description=description, category=category
    )
    product_in_db = ProductInDBBase(**new_product_data.model_dump())
    db.db["products"].append(product_in_db)
    db.db_products_by_id[product_in_db.product_id] = product_in_db

    # Initialize stock for the new product
    initial_stock = StockInDBBase(
        product_id=product_in_db.product_id, quantity=0
    )  # Default to 0 stock
    db.db["stock"].append(initial_stock)
    db.db_stock_by_product_id[product_in_db.product_id] = initial_stock

    return Product.model_validate(product_in_db)


# SQL/NoSQL Injection Target. Naive implementation.
# IMPORTANT: This route is placed BEFORE /{product_id} to resolve routing ambiguity.
@router.get("/products/search", response_model=List[Product], tags=["Products"])
async def search_products_by_name(name: str = Query(...)):
    """
    Search for products by name (case-insensitive substring match).
    Intended Injection Target: Simulates vulnerability where 'name' could be unsafely used in a backend query.
    """
    logger.info(
        "Searching for product with name containing: '%s'. Intended Injection Target.",
        name,
    )
    if hasattr(db, "unsafe_search_products"):
        try:
            results = db.unsafe_search_products(name)
            return [Product.model_validate(p) for p in results]
        except Exception as exc:
            logger.info("Search failed on SQL backend: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Search query failed due to invalid input",
            )

    # VULNERABILITY: Naive string matching, simulating how a direct query concatenation might behave.
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
        logger.info("Potential injection characters detected in search term: %s", name)
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
    product = db.db_products_by_id.get(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    return Product.model_validate(product)


@router.get(
    "/products/{product_id}/with-stock",
    response_model=ProductWithStock,
    tags=["Products", "Stock"],
)
async def get_product_by_id_with_stock(product_id: UUID):
    """
    Get a product by its unique ID along with stock quantity.
    """
    product = db.db_products_by_id.get(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    stock = db.get_stock(product_id)
    return ProductWithStock(
        **product.model_dump(),
        stock_quantity=stock.quantity if stock is not None else 0,
    )


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
    product_to_update = db.db_products_by_id.get(product_id)
    if not product_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    if product_to_update.is_protected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Product '{product_to_update.name}' is protected for demo purposes "
                "and cannot be modified/deleted. Try a non-protected product."
            ),
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
                logger.info(
                    "Product %s internal_status being set to '%s' via query param. Parameter Pollution Target.",
                    product_id,
                    value,
                )

    product_to_update.updated_at = datetime.now(timezone.utc)
    return Product.model_validate(product_to_update)


# BFLA Target: No admin check initially.
@router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_200_OK,
    tags=["Products"],
    response_model=dict,
)
async def delete_existing_product(
    product_id: UUID,
    # current_user: TokenData = Depends(get_current_user) # BFLA: No check for admin status
):
    """
    Delete an existing product.
    Intended BFLA: No admin check performed, allowing any authenticated user to delete products.
    """
    product_to_delete = db.db_products_by_id.get(product_id)
    if not product_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )
    if product_to_delete.is_protected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Product '{product_to_delete.name}' is protected for demo purposes "
                "and cannot be modified/deleted. Try a non-protected product."
            ),
        )

    logger.info(
        "Deleting product %s. Intended BFLA: No admin check performed.",
        product_id,
    )
    if product_to_delete in db.db["products"]:
        db.db["products"].remove(product_to_delete)
    db.db_products_by_id.pop(product_id, None)
    # Also remove associated stock
    db.db["stock"] = [s for s in db.db["stock"] if s.product_id != product_id]
    db.db_stock_by_product_id.pop(product_id, None)
    # Consider implications for orders with this product (e.g., mark as unavailable, don't delete from historical orders)
    return {"message": "Product deleted successfully"}


@router.get("/products/{product_id}/stock", response_model=Stock, tags=["Stock"])
async def get_product_stock_info(product_id: UUID):
    """
    Get stock information for a specific product.
    """
    stock_info = db.db_stock_by_product_id.get(product_id)
    product_exists = db.db_products_by_id.get(product_id)

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
    stock_to_update = db.db_stock_by_product_id.get(product_id)
    product_exists = db.db_products_by_id.get(product_id)

    if not product_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found, cannot update stock.",
        )

    if product_exists.is_protected:
        logger.info(
            "Stock update attempted on protected product %s (%s).",
            product_exists.name,
            product_id,
        )

        if quantity < PROTECTED_STOCK_MINIMUM:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Product '{product_exists.name}' is protected for demo purposes "
                    f"and cannot have stock reduced below {PROTECTED_STOCK_MINIMUM}. "
                    "Try a non-protected product or use the normal purchase flow."
                ),
            )

    if not stock_to_update:
        # If product exists but stock record doesn't, create it (could happen if product was added without stock init)
        logger.info("Stock record for product %s not found. Creating one.", product_id)
        stock_to_update = StockInDBBase(product_id=product_id, quantity=quantity)
        db.db["stock"].append(stock_to_update)
        db.db_stock_by_product_id[product_id] = stock_to_update
    else:
        stock_to_update.quantity = quantity

    stock_to_update.last_updated = datetime.now(timezone.utc)
    logger.info(
        "Updating stock for product %s to quantity %s. Intended BFLA: No admin/owner check performed.",
        product_id,
        quantity,
    )
    return Stock.model_validate(stock_to_update)
