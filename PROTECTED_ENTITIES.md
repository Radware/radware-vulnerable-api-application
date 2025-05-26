# Protected Demo Entities in RVA eCommerce

To ensure the stability of core demonstration flows and the continuous learning of security systems (like Radware WAAP), certain entities within this vulnerable e-commerce application are marked as "protected." This document outlines which entities are protected and what that means for demonstrating vulnerabilities.

## Purpose of Protected Entities

1.  **Flow Stability:** Core users, products, addresses, and credit cards used in automated legitimate traffic generation (e.g., by FlowRunner using `flow.json`) are protected from destructive changes that would break these flows.
2.  **Predictable Demos:** Key entities used in common manual demonstration scenarios remain consistent.
3.  **WAAP Learning:** Provides a stable baseline of "normal" API interactions for security systems to learn from.
4.  **User Guidance:** Prevents accidental or malicious disruption of the shared demo environment by guiding users to exploit non-protected or self-created entities for destructive tests.

## What "Protected" Means

*   **Deletion Prevention:** Protected entities **cannot be deleted**. Attempts will result in an HTTP 403 Forbidden error with a message guiding you to try a non-protected entity.
*   **Limited Modification:**
    *   **Protected Users:** Username and email cannot be changed. Other attributes (like `is_admin` for parameter pollution demos) may still be modifiable.
    *   **Protected Products:** Name, price, and category cannot be changed. Other attributes (like `internal_status` for parameter pollution demos or `description`) may still be modifiable.
    *   **Protected Addresses:** Generally cannot be modified.
    *   **Protected Credit Cards:** Generally cannot be modified, with a specific exception for BobJohnson's card (`cc000003-0002-...`) which allows only the specific updates defined in its demo flow (expiry year to 2031, set as default).
*   **Non-Destructive Exploits Still Work:** You can still perform BOLA to *view* data of protected users/objects, and other non-altering exploits like certain parameter pollutions.
*   **Newly Created Entities are NOT Protected:** Any user, product, address, or credit card you create (either legitimately or via a BFLA exploit) will **not** be protected by default. These are fair game for all types of vulnerability testing, including deletion.
*   **Daily Reset:** The entire application environment is reset daily, so any changes to non-protected entities or any newly created entities will be wiped.

## List of Protected Entities (from `prepopulated_data.json`)

### Protected Users:

*   `admin` (ID: `00000001-0000-0000-0000-000000000001`)
*   `AliceSmith` (ID: `00000002-0000-0000-0000-000000000002`)
*   `BobJohnson` (ID: `00000003-0000-0000-0000-000000000003`)
*   `CarolWhite` (ID: `00000004-0000-0000-0000-000000000004`)
*   `DavidBrown` (ID: `00000005-0000-0000-0000-000000000005`)
*   `EveDavis` (ID: `00000006-0000-0000-0000-000000000006`)
*   `FrankMiller` (ID: `00000007-0000-0000-0000-000000000007`)
*   `IvyTaylor` (ID: `00000010-0000-0000-0000-000000000010`)

*(GraceWilson and HenryMoore are NOT protected)*

### Protected User Addresses & Credit Cards:

*   All addresses and credit cards listed under the **protected users** above in `prepopulated_data.json` are also considered protected by default (with the modification exception for BobJohnson's specific card `cc000003-0002-...` as per its flow).

### Protected Products:

The following products are protected:
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

The following products are **NOT protected** and can be fully manipulated/deleted for demo purposes:
*   `Portable Charger 20000mAh`
*   `VR Headset Advanced`
*   `Digital Camera DSLR`
*   `Projector Mini HD`
*   `Desk Lamp LED`

## Testing Vulnerabilities

When testing vulnerabilities that involve deleting or making critical modifications:
1.  **Attempt on a Protected Entity:** Observe the 403 error and the instructive message.
2.  **Attempt on a Non-Protected Entity:**
    *   Use one of the non-protected users (GraceWilson, HenryMoore) or non-protected products listed above.
    *   **OR** create a new user/product (e.g., via BFLA if you're a regular user trying to `POST /api/products`) and then target your newly created entity.
    These actions should succeed and demonstrate the vulnerability fully.

Happy (and safe) demonstrating!