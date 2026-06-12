from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_docker_build_context_excludes_local_configuration() -> None:
    ignored = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()

    assert ".env" in ignored
    assert ".coverage" in ignored
    assert ".venv" in ignored


def test_container_runs_non_root_with_graceful_stop() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "\nUSER app\n" in dockerfile
    assert "\nSTOPSIGNAL SIGTERM\n" in dockerfile
    assert "--no-cache-dir --no-compile" in dockerfile


def test_platform_interface_lists_only_application_inputs() -> None:
    interface = (ROOT / "deployment" / "cas-platform.interface.yaml").read_text(encoding="utf-8")

    assert "outputsConsumed" not in interface
    assert "APPLICATIONINSIGHTS_CONNECTION_STRING" in interface
    assert "targetPort: 8080" in interface
