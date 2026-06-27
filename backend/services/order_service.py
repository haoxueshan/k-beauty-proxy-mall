from datetime import datetime
from uuid import uuid4

from db.supabase_client import delete_rows, insert_rows, select_rows, update_rows
from schemas import AdminOrder, CartItem, Order, OrderCreate, OrderItemSummary, Product


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def list_orders(user_id: str | None = None, order_id: str | None = None) -> list[Order]:
    # 先查订单主表，再一次性查出所有订单项，避免每个订单单独请求 Supabase。
    filters: dict[str, str] = {}
    if user_id:
        filters["user_id"] = f"eq.{user_id}"
    if order_id:
        filters["id"] = f"eq.{order_id}"

    rows = select_rows(
        "orders",
        columns=(
            "id,user_id,order_no,status,product_total_cny,service_fee_cny,"
            "international_shipping_fee_cny,package_fee_cny,total_amount_cny,paid_amount_cny,"
            "receiver_name,receiver_phone,receiver_address,user_note,admin_note,created_at"
        ),
        filters=filters or None,
        order="created_at.desc",
    )
    order_ids = [row["id"] for row in rows]
    order_items_by_order: dict[str, list[OrderItemSummary]] = {}

    if order_ids:
        in_clause = ",".join(order_ids)
        item_rows = select_rows(
            "order_items",
            columns=(
                "id,order_id,product_id,source_url,title_zh,title_ko,"
                "selected_option,note,quantity,unit_price_cny,subtotal_cny"
            ),
            filters={"order_id": f"in.({in_clause})"},
        )
        for row in item_rows:
            order_items_by_order.setdefault(row["order_id"], []).append(
                OrderItemSummary(
                    id=row["id"],
                    product_id=row["product_id"],
                    source_url=row.get("source_url"),
                    title_zh=row.get("title_zh") or "",
                    title_ko=row.get("title_ko") or "",
                    selected_option=row.get("selected_option"),
                    note=row.get("note"),
                    quantity=int(row.get("quantity") or 1),
                    unit_price_cny=float(row.get("unit_price_cny") or 0),
                    subtotal_cny=float(row.get("subtotal_cny") or 0),
                )
            )

    return [
        Order(
            id=row["id"],
            user_id=row["user_id"],
            order_no=row["order_no"],
            status=row["status"],
            product_total_cny=float(row.get("product_total_cny") or 0),
            service_fee_cny=float(row.get("service_fee_cny") or 0),
            international_shipping_fee_cny=float(row.get("international_shipping_fee_cny") or 0),
            package_fee_cny=float(row.get("package_fee_cny") or 0),
            total_amount_cny=float(row.get("total_amount_cny") or 0),
            paid_amount_cny=float(row.get("paid_amount_cny") or 0),
            receiver_name=row["receiver_name"],
            receiver_phone=row.get("receiver_phone"),
            receiver_address=row.get("receiver_address"),
            user_note=row.get("user_note"),
            admin_note=row.get("admin_note"),
            items=order_items_by_order.get(row["id"], []),
            created_at=_parse_datetime(row["created_at"]),
        )
        for row in rows
    ]


def _enrich_admin_orders(orders: list[Order]) -> list[AdminOrder]:
    # 后台订单列表需要展示用户信息，这里批量补齐用户邮箱/姓名/手机号。
    user_ids = sorted({order.user_id for order in orders if order.user_id})
    users_by_id: dict[str, dict] = {}

    if user_ids:
        user_rows = select_rows(
            "users",
            columns="id,email,name,phone,role",
            filters={"id": f"in.({','.join(user_ids)})"},
        )
        users_by_id = {row["id"]: row for row in user_rows}

    return [
        AdminOrder(
            **order.model_dump(),
            user_email=users_by_id.get(order.user_id, {}).get("email"),
            user_name=users_by_id.get(order.user_id, {}).get("name"),
            user_phone=users_by_id.get(order.user_id, {}).get("phone"),
        )
        for order in orders
    ]


def list_admin_orders() -> list[AdminOrder]:
    return _enrich_admin_orders(list_orders())


def get_admin_order(order_id: str) -> AdminOrder | None:
    orders = list_orders(order_id=order_id)
    if not orders:
        return None
    return _enrich_admin_orders(orders)[0]


def update_admin_order(order_id: str, status: str, admin_note: str | None) -> AdminOrder | None:
    updated_rows = update_rows(
        "orders",
        filters={"id": f"eq.{order_id}"},
        payload={
            "status": status,
            "admin_note": admin_note,
            "updated_at": datetime.utcnow().isoformat(),
        },
    )
    if not updated_rows:
        return None
    return get_admin_order(order_id)


def add_cart_item(
    user_id: str,
    product_id: str,
    source_url: str | None,
    quantity: int,
    selected_option: str | None,
    note: str | None,
) -> str:
    cart_item_id = str(uuid4())
    insert_rows(
        "cart_items",
        {
            "id": cart_item_id,
            "user_id": user_id,
            "product_id": product_id,
            "source_url": source_url,
            "quantity": quantity,
            "selected_option": selected_option,
            "note": note,
        },
    )
    return cart_item_id


def list_cart_items(user_id: str) -> list[CartItem]:
    rows = select_rows(
        "cart_items",
        columns="id,user_id,product_id,source_url,quantity,selected_option,note,created_at",
        filters={"user_id": f"eq.{user_id}"},
        order="created_at.desc",
    )
    return [
        CartItem(
            id=row["id"],
            user_id=row["user_id"],
            product_id=row["product_id"],
            source_url=row.get("source_url"),
            quantity=int(row.get("quantity") or 1),
            selected_option=row.get("selected_option"),
            note=row.get("note"),
            created_at=_parse_datetime(row["created_at"]),
        )
        for row in rows
    ]


def update_cart_item(user_id: str, cart_item_id: str, quantity: int, note: str | None) -> CartItem | None:
    rows = update_rows(
        "cart_items",
        filters={
            "user_id": f"eq.{user_id}",
            "id": f"eq.{cart_item_id}",
        },
        payload={
            "quantity": quantity,
            "note": note,
        },
    )
    if not rows:
        return None

    row = rows[0]
    return CartItem(
        id=row["id"],
        user_id=row["user_id"],
        product_id=row["product_id"],
        source_url=row.get("source_url"),
        quantity=int(row.get("quantity") or 1),
        selected_option=row.get("selected_option"),
        note=row.get("note"),
        created_at=_parse_datetime(row["created_at"]),
    )


def get_cart_items(user_id: str, cart_item_ids: list[str]) -> list[dict]:
    if not cart_item_ids:
        return []
    in_clause = ",".join(cart_item_ids)
    return select_rows(
        "cart_items",
        columns="id,user_id,product_id,source_url,quantity,selected_option,note",
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


def delete_order(user_id: str, order_id: str) -> bool:
    # 删除前先校验订单归属，避免用户删除到别人的订单。
    existing_rows = select_rows(
        "orders",
        columns="id",
        filters={
            "id": f"eq.{order_id}",
            "user_id": f"eq.{user_id}",
        },
        limit=1,
    )
    if not existing_rows:
        return False

    # Keep related operational tables tidy even when the database has no FK cascade.
    delete_rows("order_items", filters={"order_id": f"eq.{order_id}"})
    delete_rows("purchase_records", filters={"order_id": f"eq.{order_id}"})
    delete_rows("logistics", filters={"order_id": f"eq.{order_id}"})

    deleted_rows = delete_rows(
        "orders",
        filters={
            "id": f"eq.{order_id}",
            "user_id": f"eq.{user_id}",
        },
    )
    return bool(deleted_rows)


def create_order(
    payload: OrderCreate,
    cart_items: list[dict],
    products_by_cart_product_id: dict[str, Product],
    user_id: str,
) -> Order:
    # 新订单金额以商品 price_cny 为准；购物车项只负责数量、选项和备注。
    order_id = str(uuid4())
    order_no = f"OY{datetime.now():%Y%m%d}{uuid4().hex[:6].upper()}"
    order_items_payload: list[dict] = []
    total_amount = 0.0

    for cart_item in cart_items:
        product = products_by_cart_product_id.get(str(cart_item["product_id"]))
        if product is None:
            continue

        quantity = int(cart_item.get("quantity") or 1)
        unit_price = float(product.price_cny)
        subtotal = round(unit_price * quantity, 2)
        total_amount += subtotal
        order_items_payload.append(
            {
                "id": str(uuid4()),
                "order_id": order_id,
                "product_id": product.id,
                "source_url": cart_item.get("source_url") or product.source_url,
                "title_zh": product.title_zh,
                "title_ko": product.title_ko,
                "selected_option": cart_item.get("selected_option"),
                "note": cart_item.get("note"),
                "quantity": quantity,
                "unit_price_cny": unit_price,
                "subtotal_cny": subtotal,
            }
        )

    total_amount = round(total_amount, 2)
    order = Order(
        id=order_id,
        user_id=user_id,
        order_no=order_no,
        status="pending",
        product_total_cny=total_amount,
        service_fee_cny=0,
        international_shipping_fee_cny=0,
        package_fee_cny=0,
        total_amount_cny=total_amount,
        paid_amount_cny=0,
        receiver_name=payload.receiver_name,
        receiver_phone=payload.receiver_phone,
        receiver_address=payload.receiver_address,
        user_note=payload.note,
        items=[
            OrderItemSummary(
                id=item["id"],
                product_id=item["product_id"],
                source_url=item.get("source_url"),
                title_zh=item["title_zh"],
                title_ko=item["title_ko"],
                selected_option=item.get("selected_option"),
                note=item.get("note"),
                quantity=int(item["quantity"]),
                unit_price_cny=float(item["unit_price_cny"]),
                subtotal_cny=float(item["subtotal_cny"]),
            )
            for item in order_items_payload
        ],
        created_at=datetime.now(),
    )

    # 当前 Supabase REST 调用不是数据库事务；若要强一致，可后续改为 PostgreSQL RPC。
    insert_rows(
        "orders",
        {
            "id": order_id,
            "user_id": user_id,
            "order_no": order_no,
            "status": "pending",
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
            "updated_at": datetime.utcnow().isoformat(),
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
