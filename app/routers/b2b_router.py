from fastapi import APIRouter, HTTPException, Query, status
from typing import Dict, List

from .. import db
from ..models.b2b_models import B2BPartnerLookup, B2BPricingItem

router = APIRouter(prefix="/b2b", tags=["B2B"])

LEGACY_PARTNER_CODES: Dict[str, Dict[str, object]] = {
    "shske345pll": {
        "partner_name": "Shiske Retail",
        "tier": "silver",
        "discount_percent": 8.5,
        "discount_floor_percent": 3.0,
        "contact_email": "ap@shiske.example",
        "billing_account_id": "b2b-1001",
    },
    "pccuf987szf": {
        "partner_name": "PCC UF Stores",
        "tier": "gold",
        "discount_percent": 12.0,
        "discount_floor_percent": 5.0,
        "contact_email": "billing@pccuf.example",
        "billing_account_id": "b2b-1002",
    },
    "auzjd123ioo": {
        "partner_name": "AUZ JD Imports",
        "tier": "bronze",
        "discount_percent": 6.0,
        "discount_floor_percent": 2.0,
        "contact_email": "finance@auzjd.example",
        "billing_account_id": "b2b-1003",
    },
    "cjdjd654dkd": {
        "partner_name": "CJD JD Distribution",
        "tier": "platinum",
        "discount_percent": 16.0,
        "discount_floor_percent": 7.5,
        "contact_email": "accounts@cjdjd.example",
        "billing_account_id": "b2b-1004",
    },
}


def build_pricing_snapshot(limit: int = 5) -> List[B2BPricingItem]:
    items: List[B2BPricingItem] = []
    for product in list(db.db["products"])[:limit]:
        items.append(
            B2BPricingItem(
                sku=product.product_id.hex[:12],
                retail_price=product.price,
                wholesale_price=round(product.price * 0.62, 2),
            )
        )
    return items


@router.get(
    "/partner-lookup",
    response_model=B2BPartnerLookup,
    status_code=status.HTTP_200_OK,
)
async def legacy_partner_lookup(
    q: str = Query(
        ...,
        description=(
            "Legacy partner reference code in the format "
            "`[a-z]{5}[0-9]{3}[a-z]{3}` (example: shske345pll)."
        ),
    )
):
    """
    Legacy B2B lookup endpoint.
    Vulnerability: No authentication or access controls. Exposes internal pricing.
    """
    partner = LEGACY_PARTNER_CODES.get(q)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner reference code not found.",
        )

    return B2BPartnerLookup(
        ref_code=q,
        partner_name=partner["partner_name"],
        tier=partner["tier"],
        discount_percent=partner["discount_percent"],
        discount_floor_percent=partner["discount_floor_percent"],
        contact_email=partner["contact_email"],
        billing_account_id=partner["billing_account_id"],
        pricing_snapshot=build_pricing_snapshot(),
        legacy_notes="Legacy B2B endpoint exposes internal pricing with no auth checks.",
    )
