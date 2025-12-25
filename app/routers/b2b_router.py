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
    "admin111min": {
        "partner_name": "admin Legacy Partner",
        "tier": "silver",
        "discount_percent": 5.7,
        "discount_floor_percent": 2.5,
        "contact_email": "legacy-admin@partner.example",
        "billing_account_id": "b2b-1101",
    },
    "alice112ith": {
        "partner_name": "AliceSmith Legacy Partner",
        "tier": "gold",
        "discount_percent": 6.4,
        "discount_floor_percent": 3.0,
        "contact_email": "legacy-alicesmith@partner.example",
        "billing_account_id": "b2b-1102",
    },
    "bobjo113son": {
        "partner_name": "BobJohnson Legacy Partner",
        "tier": "bronze",
        "discount_percent": 7.1,
        "discount_floor_percent": 3.5,
        "contact_email": "legacy-bobjohnson@partner.example",
        "billing_account_id": "b2b-1103",
    },
    "carol114ite": {
        "partner_name": "CarolWhite Legacy Partner",
        "tier": "platinum",
        "discount_percent": 7.8,
        "discount_floor_percent": 4.0,
        "contact_email": "legacy-carolwhite@partner.example",
        "billing_account_id": "b2b-1104",
    },
    "david115own": {
        "partner_name": "DavidBrown Legacy Partner",
        "tier": "silver",
        "discount_percent": 8.5,
        "discount_floor_percent": 2.0,
        "contact_email": "legacy-davidbrown@partner.example",
        "billing_account_id": "b2b-1105",
    },
    "eveda116vis": {
        "partner_name": "EveDavis Legacy Partner",
        "tier": "gold",
        "discount_percent": 9.2,
        "discount_floor_percent": 2.5,
        "contact_email": "legacy-evedavis@partner.example",
        "billing_account_id": "b2b-1106",
    },
    "frank117ler": {
        "partner_name": "FrankMiller Legacy Partner",
        "tier": "bronze",
        "discount_percent": 9.9,
        "discount_floor_percent": 3.0,
        "contact_email": "legacy-frankmiller@partner.example",
        "billing_account_id": "b2b-1107",
    },
    "ivyta118lor": {
        "partner_name": "IvyTaylor Legacy Partner",
        "tier": "platinum",
        "discount_percent": 10.6,
        "discount_floor_percent": 3.5,
        "contact_email": "legacy-ivytaylor@partner.example",
        "billing_account_id": "b2b-1108",
    },
    "kevin119ris": {
        "partner_name": "KevinHarris Legacy Partner",
        "tier": "silver",
        "discount_percent": 11.3,
        "discount_floor_percent": 4.0,
        "contact_email": "legacy-kevinharris@partner.example",
        "billing_account_id": "b2b-1109",
    },
    "laura121ott": {
        "partner_name": "LauraScott Legacy Partner",
        "tier": "gold",
        "discount_percent": 5.0,
        "discount_floor_percent": 2.0,
        "contact_email": "legacy-laurascott@partner.example",
        "billing_account_id": "b2b-1110",
    },
    "micha122ing": {
        "partner_name": "MichaelKing Legacy Partner",
        "tier": "bronze",
        "discount_percent": 5.7,
        "discount_floor_percent": 2.5,
        "contact_email": "legacy-michaelking@partner.example",
        "billing_account_id": "b2b-1111",
    },
    "natal123ung": {
        "partner_name": "NatalieYoung Legacy Partner",
        "tier": "platinum",
        "discount_percent": 6.4,
        "discount_floor_percent": 3.0,
        "contact_email": "legacy-natalieyoung@partner.example",
        "billing_account_id": "b2b-1112",
    },
    "owenh124all": {
        "partner_name": "OwenHall Legacy Partner",
        "tier": "silver",
        "discount_percent": 7.1,
        "discount_floor_percent": 3.5,
        "contact_email": "legacy-owenhall@partner.example",
        "billing_account_id": "b2b-1113",
    },
    "paula125een": {
        "partner_name": "PaulaGreen Legacy Partner",
        "tier": "gold",
        "discount_percent": 7.8,
        "discount_floor_percent": 4.0,
        "contact_email": "legacy-paulagreen@partner.example",
        "billing_account_id": "b2b-1114",
    },
    "thoma126ght": {
        "partner_name": "ThomasWright Legacy Partner",
        "tier": "bronze",
        "discount_percent": 8.5,
        "discount_floor_percent": 2.0,
        "contact_email": "legacy-thomaswright@partner.example",
        "billing_account_id": "b2b-1115",
    },
    "umatu127ner": {
        "partner_name": "UmaTurner Legacy Partner",
        "tier": "platinum",
        "discount_percent": 9.2,
        "discount_floor_percent": 2.5,
        "contact_email": "legacy-umaturner@partner.example",
        "billing_account_id": "b2b-1116",
    },
    "victo128ang": {
        "partner_name": "VictorZhang Legacy Partner",
        "tier": "silver",
        "discount_percent": 9.9,
        "discount_floor_percent": 3.0,
        "contact_email": "legacy-victorzhang@partner.example",
        "billing_account_id": "b2b-1117",
    },
    "wendy129ark": {
        "partner_name": "WendyClark Legacy Partner",
        "tier": "gold",
        "discount_percent": 10.6,
        "discount_floor_percent": 3.5,
        "contact_email": "legacy-wendyclark@partner.example",
        "billing_account_id": "b2b-1118",
    },
    "xavie131pez": {
        "partner_name": "XavierLopez Legacy Partner",
        "tier": "bronze",
        "discount_percent": 11.3,
        "discount_floor_percent": 4.0,
        "contact_email": "legacy-xavierlopez@partner.example",
        "billing_account_id": "b2b-1119",
    },
    "yvonn132nez": {
        "partner_name": "YvonneMartinez Legacy Partner",
        "tier": "platinum",
        "discount_percent": 5.0,
        "discount_floor_percent": 2.0,
        "contact_email": "legacy-yvonnemartinez@partner.example",
        "billing_account_id": "b2b-1120",
    },
    "zacha133lan": {
        "partner_name": "ZacharyNolan Legacy Partner",
        "tier": "silver",
        "discount_percent": 5.7,
        "discount_floor_percent": 2.5,
        "contact_email": "legacy-zacharynolan@partner.example",
        "billing_account_id": "b2b-1121",
    },
    "alyss134ark": {
        "partner_name": "AlyssaPark Legacy Partner",
        "tier": "gold",
        "discount_percent": 6.4,
        "discount_floor_percent": 3.0,
        "contact_email": "legacy-alyssapark@partner.example",
        "billing_account_id": "b2b-1122",
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
            "`[a-z]{5}[1-9]{3}[a-z]{3}` (example: shske345pll)."
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
