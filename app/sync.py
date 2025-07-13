import asyncio
import json
import logging
import os
import tempfile
from typing import Any, Dict

import httpx

from . import db

DB_SYNC_PEER = os.getenv("DB_SYNC_PEER")
DB_SYNC_INTERVAL = float(os.getenv("DB_SYNC_INTERVAL", "60"))

logger = logging.getLogger(__name__)


def _export_state() -> Dict[str, Any]:
    users = db.list_users()
    products = db.list_products()
    coupons = db.list_coupons()

    addresses = []
    credit_cards = []
    orders = []
    order_items = []
    for user in users:
        addresses.extend(
            [a.model_dump() for a in db.list_addresses_for_user(user.user_id)]
        )
        credit_cards.extend(
            [c.model_dump() for c in db.list_credit_cards_for_user(user.user_id)]
        )
        user_orders = db.list_orders_for_user(user.user_id)
        orders.extend([o.model_dump() for o in user_orders])
        for order in user_orders:
            order_items.extend(
                [oi.model_dump() for oi in db.list_order_items(order.order_id)]
            )

    stock = []
    for prod in products:
        s_obj = db.get_stock(prod.product_id)
        if s_obj:
            stock.append(s_obj.model_dump())

    return {
        "users": [u.model_dump() for u in users],
        "addresses": addresses,
        "credit_cards": credit_cards,
        "products": [p.model_dump() for p in products],
        "stock": stock,
        "orders": orders,
        "order_items": order_items,
        "coupons": [c.model_dump() for c in coupons],
    }


def _load_remote_data(data: Dict[str, Any]) -> None:
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as fh:
        json.dump(data, fh)
        path = fh.name
    try:
        db.initialize(path)
    finally:
        os.unlink(path)


async def _sync_iteration(client: httpx.AsyncClient) -> None:
    if not DB_SYNC_PEER:
        return
    try:
        resp = await client.get(f"{DB_SYNC_PEER}/sync")
        if resp.status_code == 200:
            _load_remote_data(resp.json())
    except Exception as exc:  # pragma: no cover - sync best effort
        logger.warning("Failed to pull updates: %s", exc)
    try:
        await client.post(f"{DB_SYNC_PEER}/sync", json=_export_state())
    except Exception as exc:  # pragma: no cover - sync best effort
        logger.warning("Failed to push updates: %s", exc)


async def _sync_loop() -> None:
    if not DB_SYNC_PEER:
        logger.info("DB sync disabled - no peer defined")
        return
    interval = DB_SYNC_INTERVAL
    async with httpx.AsyncClient(timeout=10) as client:
        while True:
            await _sync_iteration(client)
            await asyncio.sleep(interval)


def start_background_sync() -> None:
    if not DB_SYNC_PEER:
        return
    loop = asyncio.get_event_loop()
    loop.create_task(_sync_loop())
