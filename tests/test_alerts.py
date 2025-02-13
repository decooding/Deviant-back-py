import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app  # Теперь pytest найдет main.py
from fastapi.testclient import TestClient


client = TestClient(app)


def test_create_alert():
    response = client.post(
        "/alerts/", json={"type": "fight", "description": "Test alert"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "fight"


def test_get_alerts():
    response = client.get("/alerts/")
    assert response.status_code == 200


def test_delete_alert():
    # Сначала создаем тревогу
    response = client.post(
        "/alerts/", json={"type": "test", "description": "To be deleted"}
    )
    assert response.status_code == 200
    alert_id = response.json()["id"]

    # Теперь удаляем
    delete_response = client.delete(f"/alerts/{alert_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "Alert deleted successfully"}

def test_update_alert():
    # Создаем новую тревогу
    response = client.post("/alerts/", json={"type": "fire", "description": "Пожар в здании"})
    assert response.status_code == 200
    alert_data = response.json()
    alert_id = alert_data["id"]

    # Обновляем тревогу
    updated_data = {"type": "false_alarm", "description": "Ложная тревога"}
    update_response = client.put(f"/alerts/{alert_id}", json=updated_data)
    assert update_response.status_code == 200
    updated_alert = update_response.json()

    # Проверяем, что данные обновились
    assert updated_alert["type"] == "false_alarm"
    assert updated_alert["description"] == "Ложная тревога"

def test_create_alert_invalid():
    # Отправляем запрос без обязательного параметра "type"
    response = client.post("/alerts/", json={"description": "Тест без типа"})
    assert response.status_code == 422  # Ошибка валидации
