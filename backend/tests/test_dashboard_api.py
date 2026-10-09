from uuid import uuid4

from fastapi.testclient import TestClient


def commit(client: TestClient, pdf: bytes) -> None:
    client.post("/api/imports", files={"file": ("cas.pdf", pdf, "application/pdf")})


def test_dashboard_totals_and_series_come_from_the_ledger(
    client: TestClient, mock_cas_pdf: bytes
) -> None:
    commit(client, mock_cas_pdf)

    dashboard = client.get("/api/dashboard").json()

    assert dashboard["current_value"] == "365170.11"
    assert dashboard["invested"] == "331272.71"
    assert dashboard["absolute_return"] == "33897.40"
    assert dashboard["series"][-1] == {"date": "2025-03-31", "value": "365170.11"}


def test_dashboard_positions_carry_their_asset_class_and_share(
    client: TestClient, mock_cas_pdf: bytes
) -> None:
    commit(client, mock_cas_pdf)

    positions = client.get("/api/dashboard").json()["positions"]

    assert [(p["asset_class"], p["percent"]) for p in positions] == [
        ("equity", "35.46"),
        ("other", "51.51"),
        ("other", "13.03"),
    ]


def test_dashboard_is_empty_before_any_import(client: TestClient) -> None:
    assert client.get("/api/dashboard").json() == {
        "current_value": "0",
        "invested": "0",
        "absolute_return": "0",
        "series": [],
        "positions": [],
    }


def test_asset_class_filter_rescopes_the_dashboard(client: TestClient, mock_cas_pdf: bytes) -> None:
    commit(client, mock_cas_pdf)

    dashboard = client.get("/api/dashboard", params={"asset_class": "equity"}).json()

    assert dashboard["current_value"] == "129476.23"
    assert [p["scheme"] for p in dashboard["positions"]] == [
        "HDFC Top 200 Fund - Direct Plan - Growth"
    ]


def test_an_unknown_asset_class_is_rejected(client: TestClient) -> None:
    assert client.get("/api/dashboard", params={"asset_class": "art"}).status_code == 422


def test_member_filter_keeps_only_that_members_positions(
    client: TestClient, mock_cas_pdf: bytes
) -> None:
    commit(client, mock_cas_pdf)

    member = client.get("/api/filters").json()["members"][0]["id"]
    scoped = client.get("/api/dashboard", params={"member": member}).json()

    assert scoped["current_value"] == "365170.11"


def test_an_unknown_member_scopes_the_dashboard_to_nothing(
    client: TestClient, mock_cas_pdf: bytes
) -> None:
    commit(client, mock_cas_pdf)

    scoped = client.get("/api/dashboard", params={"member": str(uuid4())}).json()

    assert (scoped["current_value"], scoped["positions"]) == ("0", [])


def test_filters_list_the_seeded_member_and_every_asset_class(
    client: TestClient, mock_cas_pdf: bytes
) -> None:
    commit(client, mock_cas_pdf)

    options = client.get("/api/filters").json()

    assert [member["name"] for member in options["members"]] == ["Me"]
    assert [entry["value"] for entry in options["asset_classes"]] == [
        "equity",
        "debt",
        "gold",
        "real_estate",
        "cash",
        "crypto",
        "other",
    ]
