from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_mock_mode() -> None:
    response = client.post(
        "/api/analyze",
        json={
            "image": {
                "dataUrl": "data:image/png;base64,ZmFrZQ==",
                "width": 1440,
                "height": 900,
                "surfaceType": "monitor",
            }
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["image"]["surfaceType"] == "monitor"
    assert "summary" in payload["plan"]
    assert payload["rawResponse"]
