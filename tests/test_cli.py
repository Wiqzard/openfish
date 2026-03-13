from __future__ import annotations

from typing import Any

from app import cli


def test_cli_without_args_shows_welcome(capsys: Any) -> None:
    exit_code = cli.main(["--plain"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "OpenFish Command Deck" in captured.out
    assert "openfish ui" in captured.out


def test_cli_dispatches_ui_command(monkeypatch: Any) -> None:
    recorded: dict[str, Any] = {}

    def fake_run_web_app(host: str, port: int, reload: bool) -> None:
        recorded.update({"host": host, "port": port, "reload": reload})

    monkeypatch.setattr(cli, "run_web_app", fake_run_web_app)

    exit_code = cli.main(["--plain", "ui", "--host", "0.0.0.0", "--port", "8100", "--no-reload"])

    assert exit_code == 0
    assert recorded == {"host": "0.0.0.0", "port": 8100, "reload": False}


def test_cli_dispatches_mcp_command(monkeypatch: Any) -> None:
    recorded: dict[str, Any] = {}

    def fake_run_mcp_server(transport: str) -> None:
        recorded["transport"] = transport

    monkeypatch.setattr(cli, "run_mcp_server", fake_run_mcp_server)

    exit_code = cli.main(["--plain", "mcp", "--transport", "sse"])

    assert exit_code == 0
    assert recorded == {"transport": "sse"}


def test_cli_dispatches_dummy_vlm_command(monkeypatch: Any) -> None:
    recorded: dict[str, Any] = {}

    def fake_run_dummy_vlm_server(host: str, port: int) -> None:
        recorded.update({"host": host, "port": port})

    monkeypatch.setattr(cli, "run_dummy_vlm_server", fake_run_dummy_vlm_server)

    exit_code = cli.main(["--plain", "dummy-vlm", "--host", "127.0.0.2", "--port", "8999"])

    assert exit_code == 0
    assert recorded == {"host": "127.0.0.2", "port": 8999}
