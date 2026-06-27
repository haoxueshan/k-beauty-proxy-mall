from services import order_service
from schemas import OrderCreate, Product


def _product() -> Product:
    return Product(
        id="oy-A000000000001",
        goods_no="A000000000001",
        source_url="https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000000001",
        brand_ko="테스트브랜드",
        brand_zh="测试品牌",
        title_ko="테스트 상품",
        title_zh="测试商品",
        image_url="https://example.com/item.jpg",
        original_price_krw=20000,
        sale_price_krw=15000,
        price_cny=79.5,
        proxy_price_cny=79.5,
        category_zh="测试",
        ai_summary="测试商品",
    )


def test_create_order_uses_cart_product_id_mapping(monkeypatch) -> None:
    inserted: dict[str, object] = {}
    deleted: dict[str, object] = {}

    def fake_insert_rows(table: str, payload):
        inserted[table] = payload
        return payload if isinstance(payload, list) else [payload]

    def fake_delete_rows(table: str, filters):
        deleted[table] = filters
        return [{"id": "cart-1"}]

    monkeypatch.setattr(order_service, "insert_rows", fake_insert_rows)
    monkeypatch.setattr(order_service, "delete_rows", fake_delete_rows)

    payload = OrderCreate(
        cart_item_ids=["cart-1"],
        receiver_name="Buyer",
        receiver_phone="01012345678",
        receiver_address="Seoul",
        note="order note",
    )
    cart_items = [
        {
            "id": "cart-1",
            "product_id": "oy-001",
            "source_url": "https://example.com/cart-source",
            "quantity": 2,
            "selected_option": "default",
            "note": "item note",
        }
    ]

    order = order_service.create_order(
        payload,
        cart_items,
        {"oy-001": _product()},
        "user-1",
    )

    assert order.items
    assert order.items[0].product_id == "oy-A000000000001"
    assert order.items[0].source_url == "https://example.com/cart-source"
    assert order.items[0].quantity == 2
    assert order.items[0].note == "item note"
    assert order.product_total_cny == 159.0
    assert inserted["order_items"][0]["product_id"] == "oy-A000000000001"
    assert inserted["order_items"][0]["source_url"] == "https://example.com/cart-source"
    assert deleted["cart_items"] == {"user_id": "eq.user-1", "id": "in.(cart-1)"}
