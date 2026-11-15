from app.application.system_health import check_database_health


def test_database_health_use_case_checks_the_database_port() -> None:
    calls = []

    class Reader:
        def check_database(self) -> None:
            calls.append("checked")

    assert check_database_health(Reader()) is None
    assert calls == ["checked"]
