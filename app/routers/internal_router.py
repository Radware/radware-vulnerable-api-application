"""Legacy internal "customer data sync / export" backend service.

Backstory (demo narrative): ops/billing once ran a nightly job that batch-pulled
full customer records into an external reconciliation system. That downstream
system was retired and the job was marked decommissioned, but the HTTP handler
that fronted it was never unmounted. It never appeared in the published OpenAPI
("internal plumbing") and was left unauthenticated on the assumption it was only
reachable from the internal network. A later migration moved the host to a public
subnet and the route quietly came back to life.

Vulnerabilities demonstrated (intentional, for the Radware Cloud WAAP demo):
  * No authentication and no ownership check (BOLA) -> any caller can read any
    customer record and enumerate the whole customer base by `account_ref`.
  * Excessive data exposure -> `scope=full` widens the response to PII, payment
    metadata, a credential hash, and internal-only fields.
  * Absent from the published OpenAPI schema -> surfaces in API Discovery as a
    shadow / zombie API (Last Origin = Discovery, not OAS).

All returned "sensitive" data is seeded/synthetic demo data for fake users.
"""

import hashlib
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from .. import db
from ..models.internal_models import (
    CustomerSyncRequest,
    InternalCustomerRecord,
    SyncAddress,
    SyncPaymentMethod,
)

# Mounted bare in main.py; the router carries the full /api/v1 prefix -> final
# path is /api/v1/customer-sync. It blends into the normal /api tree (so it is
# served by the existing nginx /api proxy and surfaces in API Discovery among the
# real endpoints) while the stray "v1" reads as a leftover from a retired API
# version -- a far less conspicuous zombie than a literal /internal path.
router = APIRouter(prefix="/api/v1", tags=["Sync"])


# Synthetic internal-only enrichment for a few well-known demo customers. Any
# customer not listed here falls through to synth_profile() so enumeration always
# returns a rich, deterministic record.
INTERNAL_CUSTOMER_PROFILES = {
    "admin": {
        "account_tier": "platinum",
        "account_status": "active",
        "tax_id": "US-TAX-0000-0001",
        "lifetime_value": 99999.00,
        "internal_risk_notes": "Internal superuser; do not expose externally.",
    },
    "AliceSmith": {
        "account_tier": "platinum",
        "account_status": "active",
        "tax_id": "US-TAX-4821-0097",
        "lifetime_value": 48213.55,
        "internal_risk_notes": "VIP; manual fraud override on file 2026-03.",
    },
    "BobJohnson": {
        "account_tier": "gold",
        "account_status": "active",
        "tax_id": "US-TAX-7731-2218",
        "lifetime_value": 15320.40,
        "internal_risk_notes": "Chargeback history; watchlist tier 2.",
    },
    "CarolWhite": {
        "account_tier": "silver",
        "account_status": "dormant",
        "tax_id": "US-TAX-3390-5567",
        "lifetime_value": 4220.10,
        "internal_risk_notes": "Dormant since 2025-11; retention campaign pending.",
    },
    "QuinnBaker": {
        "account_tier": "gold",
        "account_status": "active",
        "tax_id": "US-TAX-6612-8841",
        "lifetime_value": 20110.75,
        "internal_risk_notes": "Flagged by BLA engine; multi-account access pattern.",
    },
}

DEFAULT_TIERS = ["bronze", "silver", "gold", "platinum"]


def synth_profile(username: str) -> dict:
    """Deterministic synthetic enrichment for any customer not listed above."""
    h = int(hashlib.sha256(username.encode()).hexdigest(), 16)
    tier = DEFAULT_TIERS[h % 4]
    return {
        "account_tier": tier,
        "account_status": "active" if h % 7 else "dormant",
        "tax_id": f"US-TAX-{h % 10000:04d}-{(h // 10000) % 10000:04d}",
        "lifetime_value": round((h % 90000) + 1000 + (h % 100) / 100, 2),
        "internal_risk_notes": f"Auto-synced from legacy CRM; segment={tier}; no review on file.",
    }


def _resolve_user(ref: str):
    """Resolve a customer by username, email, or user_id (UUID) - no auth."""
    user = db.get_user_by_username(ref) or db.get_user_by_email(ref)
    if user:
        return user
    try:
        return db.get_user(UUID(ref))
    except (ValueError, AttributeError, TypeError):
        return None


@router.post(
    "/customer-sync",
    response_model=InternalCustomerRecord,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,  # hygiene; served schema comes from openapi.yaml anyway
)
async def customer_sync(req: CustomerSyncRequest):
    """
    Legacy internal customer data-sync/export service.

    Vulnerability: no authentication, no ownership check (BOLA), excessive data
    exposure on `scope=full`, and absent from the published OpenAPI schema.
    """
    user = _resolve_user(req.account_ref)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer reference not found.",
        )

    profile = INTERNAL_CUSTOMER_PROFILES.get(user.username) or synth_profile(user.username)

    record = InternalCustomerRecord(
        account_ref=req.account_ref,
        customer_id=str(user.user_id),
        username=user.username,
        email=str(user.email),
        is_admin=user.is_admin,
        account_tier=profile["account_tier"],
        account_status=profile["account_status"],
    )

    if req.scope.lower() == "full":
        record.tax_id = profile["tax_id"]
        record.lifetime_value = profile["lifetime_value"]
        record.internal_risk_notes = profile["internal_risk_notes"]
        record.password_hash = user.password_hash
        record.addresses = [
            SyncAddress(
                street=a.street,
                city=a.city,
                country=a.country,
                zip_code=a.zip_code,
            )
            for a in db.list_addresses_for_user(user.user_id)
        ]
        record.payment_methods = [
            SyncPaymentMethod(
                cardholder_name=c.cardholder_name,
                card_last_four=c.card_last_four,
                expiry_month=c.expiry_month,
                expiry_year=c.expiry_year,
                card_number_hash=c.card_number_hash,
            )
            for c in db.list_credit_cards_for_user(user.user_id)
        ]

    return record
