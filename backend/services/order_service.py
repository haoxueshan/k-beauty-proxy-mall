from datetime import datetime
from uuid import uuid4

from db.supabase_client import delete_rows, insert_rows, select_rows
from schemas import CartItem, Order, OrderCreate, Product


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def list_orders(user_id: str | None = None) -> list[Order]:
    filters = {"user_id": f"eq.{user_id}"} if user_id else None
    rows = select_rows(
        "orders",
        columns="id,user_id,order_no,status,total_amount_cny,receiver_name,created_at",
        filters=filters,
        order="created_at.desc",
    )
    return [
        Order(
            id=row["id"],
            user_id=row["user_id"],
            order_no=row["order_no"],
            status=row["status"],
            total_amount_cny=float(row["total_amount_cny"] or 0),
            receiver_name=row["receiver_name"],
            created_at=_parse_datetime(row["created_at"]),
        )
        for row in rows
    ]


def add_cart_item(user_id: str, product_id: str, quantity: int, selected_option: str | None, note: str | None) -> str:
    cart_item_id = str(uuid4())
    insert_rows(
        "cart_items",
        {
            "id": cart_item_id,
            "user_id": user_id,
            "product_id": product_id,
            "quantity": quantity,
            "selected_option": selected_option,
            "note": note,
        },
    )
    return cart_item_id


def list_cart_items(user_id: str) -> list[CartItem]:
    rows = select_rows(
        "cart_items",
        columns="id,user_id,product_id,quantity,selected_option,note,created_at",
        filters={"user_id": f"eq.{user_id}"},
        order="created_at.desc",
    )
    return [
        CartItem(
            id=row["id"],
            user_id=row["user_id"],
            product_id=row["product_id"],
            quantity=int(row.get("quantity") or 1),
            selected_option=row.get("selected_option"),
            note=row.get("note"),
            created_at=_parse_datetime(row["created_at"]),
        )
        for row in rows
    ]


def get_cart_items(user_id: str, cart_item_ids: list[str]) -> list[dict]:
    if not cart_item_ids:
        return []
    in_clause = ",".join(cart_item_ids)
    return select_rows(
        "cart_items",
        columns="id,user_id,product_id,quantity,selected_option,note",
        filters={
            "user_id": f"eq.{user_id}",
            "id": f"in.({in_clause})",
        },
    )


def delete_cart_item(user_id: str, cart_item_id: str) -> bool:
    deleted_rows = delete_rows(
        "cart_items",
        filters={
            "user_id": f"eq.{user_id}",
            "id": f"eq.{cart_item_id}",
        },
    )
    return bool(deleted_rows)


def create_order(payload: OrderCreate, cart_items: list[dict], products: list[Product], user_id: str) -> Order:
    order_id = str(uuid4())
    order_no = f"OY{datetime.now():%Y%m%d}{uuid4().hex[:6].upper()}"
    product_lookup = {product.id: product for product in products}
    order_items_payload: list[dict] = []
    total_amount = 0.0

    for cart_item in cart_items:
        product = product_lookup.get(cart_item["product_id"])
        if product is None:
            continue

        quantity = int(cart_item.get("quantity") or 1)
        unit_price = float(product.proxy_price_cny)
        subtotal = round(unit_price * quantity, 2)
        total_amount += subtotal
        order_items_payload.append(
            {
                "id": str(uuid4()),
                "order_id": order_id,
                "product_id": product.id,
                "source_url": product.source_url,
                "title_zh": product.title_zh,
                "title_ko": product.title_ko,
                "selected_option": cart_item.get("selected_option"),
                "quantity": quantity,
                "unit_price_cny": unit_price,
                "subtotal_cny": subtotal,
            }
        )

    if not order_items_payload and products:
        fallback_product = products[0]
        total_amount = round(float(fallback_product.proxy_price_cny), 2)
        order_items_payload.append(
            {
                "id": str(uuid4()),
                "order_id": order_id,
                "product_id": fallback_product.id,
                "source_url": fallback_product.source_url,
                "title_zh": fallback_product.title_zh,
                "title_ko": fallback_product.title_ko,
                "selected_option": None,
                "quantity": 1,
                "unit_price_cny": float(fallback_product.proxy_price_cny),
                "subtotal_cny": total_amount,
            }
        )

    total_amount = round(total_amount, 2)
    order = Order(
        id=order_id,
        user_id=user_id,
        order_no=order_no,
        status="pending_quote",
        total_amount_cny=total_amount,
        receiver_name=payload.receiver_name,
        created_at=datetime.now(),
    )

    insert_rows(
        "orders",
        {
            "id": order_id,
            "user_id": user_id,
            "order_no": order_no,
            "status": "pending_quote",
            "product_total_cny": total_amount,
            "service_fee_cny": 0,
            "international_shipping_fee_cny": 0,
            "package_fee_cny": 0,
            "total_amount_cny": total_amount,
            "paid_amount_cny": 0,
            "receiver_name": payload.receiver_name,
            "receiver_phone": payload.receiver_phone,
            "receiver_address": payload.receiver_address,
            "user_note": payload.note,
        },
    )

    if order_items_payload:
        insert_rows("order_items", order_items_payload)
        delete_rows(
            "cart_items",
            filters={
                "user_id": f"eq.{user_id}",
                "id": f"in.({','.join(item['id'] for item in cart_items)})",
            },
        )

    return order
