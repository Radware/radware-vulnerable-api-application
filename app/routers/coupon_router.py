from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional
from uuid import UUID
from datetime import datetime

from .. import db
from ..models.coupon_models import Coupon, CouponCreate, CouponInDBBase
from ..models.order_models import TokenData
from .user_router import get_current_user

router = APIRouter()


@router.get("/coupons/{coupon_code}", response_model=Coupon, tags=["Coupons"])
async def get_coupon_by_code(
    coupon_code: str, current_user: TokenData = Depends(get_current_user)
):
    coupon = db.db_coupons_by_code.get(coupon_code)
    if not coupon or not coupon.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found or inactive")
    return Coupon.model_validate(coupon)


@router.post(
    "/admin/coupons",
    response_model=Coupon,
    status_code=status.HTTP_201_CREATED,
    tags=["Admin"],
)
async def create_coupon(
    code: str = Query(...),
    discount_type: str = Query(...),
    discount_value: float = Query(...),
    is_active: bool = Query(True),
    usage_limit: Optional[int] = Query(None),
    expiration_date: Optional[str] = Query(None),
    current_user: TokenData = Depends(get_current_user),
):
    if code in db.db_coupons_by_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon code already exists")

    exp_dt = None
    if expiration_date:
        try:
            exp_dt = datetime.fromisoformat(expiration_date)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid expiration_date format")

    coupon_data = CouponCreate(
        code=code,
        discount_type=discount_type,
        discount_value=discount_value,
        is_active=is_active,
        usage_limit=usage_limit,
        expiration_date=exp_dt,
    )
    new_coupon = CouponInDBBase(**coupon_data.model_dump())
    db.db_coupons_by_id[new_coupon.coupon_id] = new_coupon
    db.db_coupons_by_code[new_coupon.code] = new_coupon
    return Coupon.model_validate(new_coupon)


@router.delete(
    "/admin/coupons/{coupon_code_or_id}",
    response_model=dict,
    tags=["Admin"],
)
async def delete_coupon(
    coupon_code_or_id: str, current_user: TokenData = Depends(get_current_user)
):
    coupon = None
    try:
        coupon_id = UUID(coupon_code_or_id)
        coupon = db.db_coupons_by_id.get(coupon_id)
    except ValueError:
        coupon = db.db_coupons_by_code.get(coupon_code_or_id)

    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found")
    if getattr(coupon, "is_protected", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Coupon is protected and cannot be deleted")

    db.db_coupons_by_id.pop(coupon.coupon_id, None)
    db.db_coupons_by_code.pop(coupon.code, None)
    return {"message": "Coupon deleted successfully"}

