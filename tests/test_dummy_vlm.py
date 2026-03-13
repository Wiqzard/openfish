from __future__ import annotations

from fastapi.testclient import TestClient

from app.testing.dummy_vlm_server import app

client = TestClient(app)


def test_dummy_vlm_server_returns_valid_completion() -> None:
    response = client.post(
        "/chat/completions",
        json={
            "model": "dummy-plan",
            "messages": [
                {"role": "system", "content": "You are a dummy model."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this screenshot."},
                        {"type": "image_url", "image_url": {"url": "data:image/png;base64,ZmFrZQ=="}},
                    ],
                },
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    content = payload["choices"][0]["message"]["content"]
    assert "summary" in content
    assert "confidence" in content


def test_dummy_vlm_server_supports_schema_error_scenario() -> None:
    response = client.post(
        "/chat/completions",
        headers={"X-Dummy-VLM-Scenario": "dummy-schema-error"},
        json={
            "model": "dummy-plan",
            "messages": [
                {"role": "system", "content": "You are a dummy model."},
                {"role": "user", "content": "trigger schema error"},
            ],
        },
    )

    assert response.status_code == 200
    content = response.json()["choices"][0]["message"]["content"]
    assert '"confidence": 4' in content


def test_dummy_vlm_server_can_emit_http_error() -> None:
    response = client.post(
        "/chat/completions",
        headers={"X-Dummy-VLM-Scenario": "dummy-http-error"},
        json={
            "model": "dummy-plan",
            "messages": [
                {"role": "system", "content": "You are a dummy model."},
                {"role": "user", "content": "trigger http error"},
            ],
        },
    )

    assert response.status_code == 500


def test_dummy_vlm_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
