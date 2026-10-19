
from unittest.mock import MagicMock

from app.models.product import Product
from app.models.tenant import UserRole


def make_scalars_result(*items):
    result = MagicMock()
    result.scalars.return_value.all.return_value = list(items)
    result.scalars.return_value.first.return_value = (
        items[0] if items else None
    )
    return result


def test_list_products_only_returns_current_tenant_products(
    client, jwt_secret, mock_db, test_user
):
    own_product = Product(
        id=101,
        tenant_id=1,
        sku="A-101",
        name="Company A Product",
        current_stock=20,
        safety_stock=5,
        unit_cost=10.0,
    )

    # 첫 번째 execute: 인증 사용자 조회
    # 두 번째 execute: 상품 목록 조회
    mock_db.execute.side_effect = [
        _user_result(test_user),
        make_scalars_result(own_product),
    ]

    response = client.get(
        "/api/v1/inventory/products",
        headers=_auth_headers(test_user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["tenant_id"] == 1
    assert body[0]["sku"] == "A-101"


def test_get_product_from_another_tenant_returns_404(
    client, jwt_secret, mock_db, test_user
):
    mock_db.execute.side_effect = [
        _user_result(test_user),
        make_scalars_result(),
    ]

    response = client.get(
        "/api/v1/inventory/products/202",
        headers=_auth_headers(test_user.id),
    )

    assert response.status_code == 404


def test_viewer_cannot_create_product(
    client, jwt_secret, mock_db, viewer_user
):
    mock_db.execute.return_value = _user_result(viewer_user)

    response = client.post(
        "/api/v1/inventory/products",
        headers=_auth_headers(viewer_user.id),
        json={
            "sku": "A-303",
            "name": "Forbidden Product",
            "category": "test",
            "current_stock": 10,
            "safety_stock": 2,
            "unit_cost": 5.0,
            "supplier_id": None,
            "tenant_id": 1,
        },
    )

    assert response.status_code == 403
    mock_db.add.assert_not_called()


def test_create_product_uses_current_user_tenant_not_payload(
    client, jwt_secret, mock_db, test_user
):
    mock_db.execute.return_value = _user_result(test_user)

    async def refresh_product(product):
        product.id = 303

    mock_db.refresh.side_effect = refresh_product

    response = client.post(
        "/api/v1/inventory/products",
        headers=_auth_headers(test_user.id),
        json={
            "sku": "A-303",
            "name": "Tenant Scoped Product",
            "category": "test",
            "current_stock": 10,
            "safety_stock": 2,
            "unit_cost": 5.0,
            "supplier_id": None,
            "tenant_id": 2,
        },
    )

    assert response.status_code == 201

    created_product = mock_db.add.call_args.args[0]
    assert isinstance(created_product, Product)
    assert created_product.tenant_id == test_user.tenant_id
    assert created_product.tenant_id != 2
    assert response.json()["tenant_id"] == test_user.tenant_id


def _user_result(user):
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    return result


def _auth_headers(user_id):
    from app.core.security import create_access_token

    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}"}

