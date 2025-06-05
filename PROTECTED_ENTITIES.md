# Protected Demo Entities in RVA eCommerce

To ensure the stability of core demonstration flows and the continuous learning of security systems (like Radware WAAP), certain entities within this vulnerable e-commerce application are marked as "protected." This document outlines which entities are protected and what that means for demonstrating vulnerabilities.

## Purpose of Protected Entities

1.  **Flow Stability:** Core users and products used in automated legitimate traffic generation are protected from destructive changes that would break these flows. Addresses and credit cards are protected by virtue of their owner being protected, particularly against deletion of the last item.
2.  **Predictable Demos:** Key entities used in common manual demonstration scenarios remain consistent.
3.  **WAAP Learning:** Provides a stable baseline of "normal" API interactions for security systems to learn from.
4.  **User Guidance:** Prevents accidental or malicious disruption of the shared demo environment by guiding users to exploit non-protected or self-created entities for destructive tests.

## What "Protected" Means

*   **Top-Level Protected Entities (Users, Products):**
    *   Cannot be deleted if their `is_protected` flag is `true` in `prepopulated_data.json`. Attempts will result in an HTTP 403 Forbidden error.
*   **Limited Modification for Protected Users (`user.is_protected: true`):**
    *   `username` cannot be changed.
    *   `email` **can** be updated.
    *   Other attributes (like `is_admin` for parameter pollution demos) may still be modifiable.
*   **Limited Modification for Protected Products (`product.is_protected: true`):**
    *   `name`, `price`, and `category` cannot be changed.
    *   Other attributes (like `internal_status` for parameter pollution demos or `description`) may still be modifiable.
    *   Stock quantity for protected products can be updated directly (though there's a `PROTECTED_STOCK_MINIMUM` if updating via the dedicated stock endpoint, not via purchase).
*   **Addresses & Credit Cards of a Protected User (`user.is_protected: true`):**
    *   **Modification:** Addresses and credit cards belonging to a protected user can generally be edited (e.g., street name, cardholder name, expiry dates).
    *   **Deletion:** Can be deleted, **unless** it is the user's last address or last credit card respectively. Attempting to delete the last one results in an HTTP 403 error with a message like "Protected user '{username}' must have at least one address/card. Cannot delete the last one."
    *   **Default Status:** Protected users can change which of their addresses or credit cards is the default at any time. If a new item is set as default, the previous default item will have its `is_default` flag set to `false`. If a default address/card is deleted (and it wasn't their last one), another remaining item for that user is automatically set as the new default.
*   **Non-Destructive Exploits Still Work:** You can still perform BOLA to *view* data of protected users/objects, and other non-altering exploits like certain parameter pollutions.
*   **Newly Created Entities are NOT Protected:** Any user, product, address, or credit card you create (either legitimately or via a BFLA exploit) will **not** be protected by default (their `is_protected` flag will be `false`). These are fair game for all types of vulnerability testing, including deletion.
*   **Daily Reset:** The entire application environment is reset daily, so any changes to non-protected entities or any newly created entities will be wiped.

## List of Protected Entities (from `prepopulated_data.json`)

### Protected Users:

The following users have `is_protected: true` in `prepopulated_data.json`:
*   `admin` (ID: `00000001-0000-0000-0000-000000000001`)
*   `AliceSmith` (ID: `00000002-0000-0000-0000-000000000002`)
*   `BobJohnson` (ID: `00000003-0000-0000-0000-000000000003`)
*   `CarolWhite` (ID: `00000004-0000-0000-0000-000000000004`)
*   `DavidBrown` (ID: `00000005-0000-0000-0000-000000000005`)
*   `EveDavis` (ID: `00000006-0000-0000-0000-000000000006`)
*   `FrankMiller` (ID: `00000007-0000-0000-0000-000000000007`)
*   `IvyTaylor` (ID: `00000010-0000-0000-0000-000000000010`)

*(GraceWilson and HenryMoore are NOT protected, i.e., their `is_protected` flag is `false`)*

### User Addresses & Credit Cards:

The protection of addresses and credit cards (specifically, the rule against deleting the last item) is derived from their owning user's `is_protected` status. All addresses and credit cards belonging to the **Protected Users** listed above are subject to the "cannot delete last item" rule. Individual address and credit card objects in `prepopulated_data.json` do not have their own `is_protected` flags.

### Protected Products:

The following products have `is_protected: true` in `prepopulated_data.json`:
*   `Laptop Pro 15` (ID: `f47ac10b-58cc-4372-a567-0e02b2c3d479`)
*   `Wireless Mouse` (ID: `a1b2c3d4-e5f6-7890-1234-567890abcdef`)
*   `Mechanical Keyboard` (ID: `b2c3d4e5-f6a7-8901-2345-678901bcdef0`)
*   `4K Monitor 27 inch` (ID: `c3d4e5f6-a7b8-9012-3456-789012cdef01`)
*   `Gaming Headset` (ID: `d4e5f6a7-b8c9-0123-4567-890123def012`)
*   `Smartwatch Series X` (ID: `e5f6a7b8-c9d0-1234-5678-901234ef0123`)
*   `Bluetooth Speaker` (ID: `f6a7b8c9-d0e1-2345-6789-012345f01234`)
*   `Webcam HD 1080p` (ID: `07b8c9d0-e1f2-3456-7890-123456012345`)
*   `External SSD 1TB` (ID: `18c9d0e1-f2a3-4567-8901-234567123456`)
*   `Graphics Tablet` (ID: `29d0e1f2-a3b4-5678-9012-345678234567`)
*   `Office Chair Ergonomic` (ID: `30e1f2a3-b4c5-6789-0123-456789345678`)
*   `Noise Cancelling Headphones` (ID: `41f2a3b4-c5d6-7890-1234-567890456789`)
*   `Smartphone Model Z` (ID: `52a3b4c5-d6e7-8901-2345-678901567890`)
*   `E-Reader Pro` (ID: `63b4c5d6-e7f8-9012-3456-789012678901`)
*   `Fitness Tracker Band` (ID: `74c5d6e7-f8a9-0123-4567-890123789012`)

The following products are **NOT protected** (i.e., `is_protected: false` in `prepopulated_data.json`) and can be fully manipulated/deleted for demo purposes:
*   `Portable Charger 20000mAh`
*   `VR Headset Advanced`
*   `Digital Camera DSLR`
*   `Projector Mini HD`
*   `Desk Lamp LED`

### Protected Coupons:

Coupons can also be flagged with `is_protected: true` in `prepopulated_data.json`.
These coupons cannot be deleted via the `/api/admin/coupons/{coupon_code_or_id}`
endpoint; attempting to do so returns **HTTP 403 Forbidden**.  No protected
coupons ship by default, but the flag is respected if added for demos.

## Testing Vulnerabilities

When testing vulnerabilities that involve deleting or making critical modifications:
1.  **Attempt on a Protected User or Product:** Observe the 403 error for disallowed actions (e.g., deleting user, changing username, deleting product).
2.  **Attempt on Addresses/Cards of a Protected User:**
    *   Modification should generally succeed.
    *   Setting a new default should succeed.
    *   Deletion should succeed unless it's the user's last address/card, in which case a specific 403 ("...must have at least one...") will be returned.
3.  **Attempt on a Non-Protected Entity (User or Product) or their sub-entities:**
    *   Use one of the non-protected users (GraceWilson, HenryMoore) or non-protected products listed above.
    *   **OR** create a new user/product (e.g., via BFLA if you're a regular user trying to `POST /api/products`) and then target your newly created entity and its sub-entities.
    These actions should succeed and demonstrate the vulnerability fully (e.g., deletion, modification without restriction).
