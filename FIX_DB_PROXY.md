# Fix for db.db["collection"] AttributeError

## Issues Found

1. **Missing `db` attribute**: Routers access `db.db["products"]`, `db.db["orders"]`, `db.db["stock"]`, etc., but SQLiteBackend didn't have a `db` attribute
2. **Missing `setdefault()` methods**: `AddressesByUserIdProxy` and `CreditCardsByUserIdProxy` needed `setdefault()` for address/card creation operations

## Changes Made

### 1. Added `DatabaseProxy` and `CollectionProxy` Classes

Created two new proxy classes in `app/db_sqlite.py`:

- **`DatabaseProxy`**: Provides `db["collection"]` access pattern
- **`CollectionProxy`**: Mimics list operations for each collection (users, products, orders, etc.)

**Supported Operations:**
- `db.db["products"]` - Access a collection
- `for p in db.db["products"]` - Iterate over collection items
- `db.db["products"].append(item)` - Add item (no-op, actual creation handled by specific methods)
- `db.db["products"].remove(item)` - Remove item (no-op, actual deletion handled by specific methods)
- `item in db.db["products"]` - Check if item exists
- `db.db["stock"] = [...]` - Bulk assignment (no-op, operations handled by specific methods)

### 2. Added `setdefault()` Methods

Added `setdefault()` method to:
- `AddressesByUserIdProxy` - Used in `user_profile_router.py:123`
- `CreditCardsByUserIdProxy` - Used in `user_router.py:404`
- Already existed in `OrdersByUserIdProxy` and `OrderItemsByOrderIdProxy`

### 3. Updated SQLiteBackend.__init__

Added `self.db = DatabaseProxy(self)` as the first proxy initialization to support the `db["collection"]` access pattern.

## How It Works

### Memory Backend (Old)
```python
db.db["products"]  # Direct dictionary access to a list
```

### SQLite Backend (New)
```python
db.db["products"]  # Returns CollectionProxy("products")
                   # Which provides list-like interface
                   # But delegates to SQLAlchemy methods
```

### Example: Product Deletion

**Memory Backend:**
```python
if product in db.db["products"]:
    db.db["products"].remove(product)  # Direct list manipulation
db.db["stock"] = [s for s in db.db["stock"] if s.product_id != product_id]
```

**SQLite Backend with Proxies:**
```python
if product in db.db["products"]:  # Checks via get_product()
    db.db["products"].remove(product)  # No-op, deletion via delete_product()
db.db["stock"] = [...]  # No-op, stock deletion handled in delete_product()
```

The actual persistence operations happen through specific SQLAlchemy methods like:
- `create_user()`
- `delete_product()`
- `update_stock()`

The proxy operations are compatibility shims that make the old list-based code work with the new database-backed code.

## Collections Supported

- **users**: Full iteration support via `list_users()`
- **products**: Full iteration support via `list_products()`
- **addresses**: Partial support (no list_all_addresses yet)
- **credit_cards**: Partial support (no list_all_credit_cards yet)
- **orders**: Partial support (no list_all_orders yet)
- **stock**: Partial support (no list_all_stock yet)
- **order_items**: Partial support (no list_all_order_items yet)

## Testing

Deploy with:
```bash
cd ~/radware-vulnerable-api-application
git pull
sudo docker-compose -f docker-compose.rva-db.yml down
sudo docker volume rm rva-pgdata
sudo docker-compose -f docker-compose.rva-db.yml up -d --build
sleep 30
sudo docker logs rva-app
```

Check for:
- ✅ No AttributeError for 'db'
- ✅ No AttributeError for 'setdefault'
- ✅ Products endpoint works: `curl http://localhost:8000/api/products`
- ✅ Orders can be created
- ✅ Addresses can be added
- ✅ Credit cards can be added

## Files Modified

- `app/db_sqlite.py`:
  - Added `DatabaseProxy` class
  - Added `CollectionProxy` class  
  - Added `setdefault()` to `AddressesByUserIdProxy`
  - Added `setdefault()` to `CreditCardsByUserIdProxy`
  - Added `self.db = DatabaseProxy(self)` to `SQLiteBackend.__init__`
