
from unittest.mock import MagicMock

from app.core.security import create_access_token


def _user_result(user):
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    return result


def _auth_headers(user_id):
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}"}


def test_viewer_cannot_run_inventory_prediction(
    client, jwt_secret, mock_db, viewer_user
):
    mock_db.execute.return_value = _user_result(viewer_user)

    response = client.post(
        "/api/v1/orders/run-prediction/202",
        headers=_auth_headers(viewer_user.id),
    )

    assert response.status_code == 403


def test_viewer_cannot_decide_purchase_order(
    client, jwt_secret, mock_db, viewer_user
):
    mock_db.execute.return_value = _user_result(viewer_user)

    response = client.patch(
        "/api/v1/orders/202/decision",
        headers=_auth_headers(viewer_user.id),
        json={
            "action": "APPROVED",
            "final_qty": 10,
        },
    )

    assert response.status_code == 403

    # 권한 검사에서 차단되므로 발주 조회는 실행되지 않아야 한다.
    assert mock_db.execute.await_count == 1


def test_cannot_decide_purchase_order_from_another_tenant(
    client, jwt_secret, mock_db, test_user
):
    # 첫 번째 조회는 인증 사용자,
    # 두 번째 조회는 현재 테넌트에서 해당 발주를 찾는 쿼리다.
    mock_db.execute.side_effect = [
        _user_result(test_user),
        _user_result(None),
    ]

    response = client.patch(
        "/api/v1/orders/202/decision",
        headers=_auth_headers(test_user.id),
        json={
            "action": "APPROVED",
            "final_qty": 10,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Purchase order not found"


def test_decision_metrics_are_scoped_to_current_tenant(
    client, jwt_secret, mock_db, test_user
):
    metrics_result = MagicMock()
    metrics_result.all.return_value = [
        ("APPROVED", 2),
        ("MODIFIED", 1),
        ("REJECTED", 1),
    ]

    mock_db.execute.side_effect = [
        _user_result(test_user),
        metrics_result,
    ]

    response = client.get(
        "/api/v1/orders/decision-metrics",
        headers=_auth_headers(test_user.id),
    )

    assert response.status_code == 200
    assert response.json() == {
        "total_decisions": 4,
        "approved_count": 2,
        "modified_count": 1,
        "rejected_count": 1,
    }

    # 실제로 실행된 집계 SQL에 테넌트 필터가 있는지 검증한다.
    metrics_stmt = mock_db.execute.await_args_list[1].args[0]
    compiled_sql = str(metrics_stmt)

    assert "order_decision_events.tenant_id" in compiled_sql
    assert "order_decision_events.tenant_id =" in compiled_sql
