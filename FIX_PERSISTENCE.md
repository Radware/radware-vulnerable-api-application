# Fix for Stock Not Updating and Empty Order History

## Root Causes Identified

### 1. Stock Not Decreasing When Orders Created
**Problem**: When creating an order, the code modified `stock.quantity` in memory but never persisted the change to the database.

**Location**: `app/routers/order_router.py:209`
```python
stock.quantity -= quantity_val  # Modified in memory only!
stock.last_updated = datetime.now(timezone.utc)
```

**Fix**: Added explicit `db.update_stock()` call after modification.

### 2. Orders Not Being Saved to Database
**Problem**: The `CollectionProxy.append()` method was a no-op (just `pass`). When code did:
- `db.db["orders"].append(new_order_db)` - Nothing happened!
- `db.db["order_items"].append(order_item_db)` - Nothing happened!

**Location**: `app/db_sqlite.py` - CollectionProxy class

**Fix**: Implemented proper `append()` logic that actually calls database creation methods:
```python
def append(self, item):
    if self.collection == "orders":
        self.backend.create_order(item)
    elif self.collection == "order_items":
        self.backend.create_order_item(item)
    # ... other collections
```

### 3. Coupon Updates Not Persisted
**Problem**: When applying coupons, `coupon.usage_count` was incremented in memory but not saved to database.

**Locations**: 
- `app/routers/order_router.py:263` (during order creation with cached coupon)
- `app/routers/order_router.py:425` (when applying coupon to existing order)

**Fix**: Added `db.update_coupon()` calls after modifications.

### 4. Address/Credit Card `is_default` Updates Not Persisted
**Problem**: Throughout the codebase, when addresses or credit cards had their `is_default` field changed, the changes were only in memory.

**Locations**: Multiple places in `user_profile_router.py` and `user_router.py`

**Fix**: Added `db.update_address()` and `db.update_credit_card()` calls after all `is_default` modifications.

## Changes Made

### File: `app/db_sqlite.py`

**Added to `CollectionProxy.append()`:**
```python
def append(self, item):
    """Add item to collection. Actual persistence handled by specific methods."""
    if self.collection == "orders" and hasattr(item, 'order_id'):
        self.backend.create_order(item)
    elif self.collection == "order_items" and hasattr(item, 'order_item_id'):
        self.backend.create_order_item(item)
    elif self.collection == "users" and hasattr(item, 'user_id'):
        self.backend.create_user(item)
    elif self.collection == "products" and hasattr(item, 'product_id'):
        self.backend.create_product(item)
    elif self.collection == "addresses" and hasattr(item, 'address_id'):
        self.backend.create_address(item)
    elif self.collection == "credit_cards" and hasattr(item, 'card_id'):
        self.backend.create_credit_card(item)
    elif self.collection == "stock" and hasattr(item, 'product_id'):
        self.backend.update_stock(item.product_id, item.quantity)
```

### File: `app/routers/order_router.py`

**Stock Update (line ~211):**
```python
# Deduct stock
stock.quantity -= quantity_val
stock.last_updated = datetime.now(timezone.utc)
# Persist stock update to database
db.update_stock(product_id_key, stock.quantity)
```

**Coupon Update During Order Creation (line ~271):**
```python
coupon.usage_count += 1
coupon.updated_at = datetime.now(timezone.utc)
# Persist coupon update to database
db.update_coupon(coupon.coupon_id, coupon.model_dump())
```

**Order and Coupon Update When Applying Coupon (line ~422):**
```python
order_db.total_amount = round(order_db.total_amount - discount, 2)
order_db.applied_coupon_id = coupon.coupon_id
order_db.applied_coupon_code = coupon.code
order_db.discount_amount = round(discount, 2)
order_db.updated_at = datetime.now(timezone.utc)
# Persist order update to database
db.update_order(order_db.order_id, order_db.model_dump())

coupon.usage_count += 1
coupon.updated_at = datetime.now(timezone.utc)
# Persist coupon update to database
db.update_coupon(coupon.coupon_id, coupon.model_dump())
```

### File: `app/routers/user_profile_router.py`

**Address Creation with is_default (lines ~128-138):**
- Added `db.update_address()` calls when setting first address as default
- Added `db.update_address()` calls when changing is_default for other addresses
- Added `db.update_address()` call for the new address itself

**Address Update (line ~203):**
- Added `db.update_address()` calls when un-defaulting other addresses
- Added final `db.update_address(address_id, address_to_update.model_dump())`

**Address Deletion (line ~263):**
- Added `db.update_address()` when reassigning default after deleting default address

**Credit Card Creation with is_default (line ~348):**
- Added `db.update_credit_card()` calls when un-defaulting other cards

**Credit Card Update (line ~430):**
- Added `db.update_credit_card()` calls when changing is_default
- Added final `db.update_credit_card(card_id, card_to_update.model_dump())`

**Credit Card Deletion (line ~492):**
- Added `db.update_credit_card()` when reassigning default after deletion

### File: `app/routers/user_router.py`

**Add Credit Card to User (lines ~410-418):**
- Added `db.update_credit_card()` when setting first card as default
- Added `db.update_credit_card()` calls when changing is_default for cards

**Update Credit Card (line ~493):**
- Added `db.update_credit_card()` calls when changing is_default
- Added final `db.update_credit_card(card_id, credit_card_to_update.model_dump())`

**Delete Credit Card (line ~551):**
- Added `db.update_credit_card()` when reassigning default after deletion

## Pattern Explanation

### Memory Backend vs SQLite Backend

**Memory Backend (Old):**
- Objects stored directly in Python lists/dicts
- Modifying an object automatically "persists" (it's just in memory)
- `list.append()` adds the object to the in-memory list

**SQLite Backend (New):**
- Objects must be explicitly saved to database
- Modifying a Pydantic model object doesn't change the database
- `db.update_*()` or `db.create_*()` must be called to persist changes

### Common Pattern Now Required

```python
# 1. Retrieve object from database
item = db.db_something_by_id.get(item_id)

# 2. Modify the object
item.field = new_value
item.updated_at = datetime.now(timezone.utc)

# 3. MUST persist the change!
db.update_something(item_id, item.model_dump())
```

## Testing

After deploying these changes:

1. **Stock should decrease** when orders are created
2. **Order history should show orders** (orders are now persisted)
3. **Coupon usage counts** should increment properly
4. **Default addresses/cards** should persist correctly across sessions

## Deployment

```bash
cd ~/radware-vulnerable-api-application
git pull
sudo docker-compose -f docker-compose.rva-db.yml down
sudo docker volume rm rva-pgdata
sudo docker-compose -f docker-compose.rva-db.yml up -d --build
sleep 30
curl http://localhost:8000/api/products  # Check stock values
```

## Files Modified

- `app/db_sqlite.py` - Fixed CollectionProxy.append() to actually persist items
- `app/routers/order_router.py` - Added stock, order, and coupon persistence calls
- `app/routers/user_profile_router.py` - Added address and credit card persistence calls  
- `app/routers/user_router.py` - Added credit card persistence calls
