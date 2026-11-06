"""Models for the legacy internal customer-sync/export service.

This backend service predates the public product API. It was used by the
ops/billing nightly "customer data sync" job and is intentionally NOT part of
the published OpenAPI schema. It is kept here, unauthenticated, to demonstrate a
"zombie" API: a decommissioned-but-still-reachable internal service that leaks
sensitive (synthetic) customer data when discovered and abused.
"""

from typing import List, Optional

from pydantic import BaseModel


class CustomerSyncRequest(BaseModel):
    """Flat JSON body accepted by the legacy customer-sync export service."""

    account_ref: str  # REQUIRED: username, email, or user_id (UUID string)
    scope: str = "summary"  # "summary" | "full"  <- disclosure-escalation flag
    format: str = "json"  # "json" | "compact" (legacy export flag; cosmetic)


class SyncAddress(BaseModel):
    street: str
    city: str
    country: str
    zip_code: str


class SyncPaymentMethod(BaseModel):
    cardholder_name: str
    card_last_four: str  # last four only; full PAN is never stored
    expiry_month: str
    expiry_year: str
    card_number_hash: Optional[str] = None  # stored hash, not the PAN


class InternalCustomerRecord(BaseModel):
    # --- always returned (scope=summary) ---
    account_ref: str
    customer_id: str
    username: str
    email: str
    is_admin: bool
    account_tier: str
    account_status: str
    sync_source: str = "customer-sync-svc (legacy, internal-only)"
    # --- escalated disclosure (scope=full); Optional so summary still validates ---
    tax_id: Optional[str] = None
    lifetime_value: Optional[float] = None
    internal_risk_notes: Optional[str] = None
    password_hash: Optional[str] = None
    addresses: Optional[List[SyncAddress]] = None
    payment_methods: Optional[List[SyncPaymentMethod]] = None
