from src.core.service import run_service


def test_run_service():
    assert run_service() == "ok"
