# tests/test_riot_client.py

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
from requests import Response

from scripts.riot_client import RiotAPIClient, RiotAPIConfig, RiotAPIError


def make_mock_response(
    status_code: int,
    json_data: Any = None,
    headers: Dict[str, str] | None = None,
) -> Response:
    resp = Mock(spec=Response)
    resp.status_code = status_code
    resp.ok = 200 <= status_code < 300
    resp.headers = headers or {}
    resp.text = str(json_data) if json_data is not None else ""
    resp.json.return_value = json_data
    return resp  # type: ignore[return-value]


def make_client_with_mock_session(mock_session: Mock) -> RiotAPIClient:
    config = RiotAPIConfig(
        api_key="dummy-key",
        region="asia",
        lol_platform="kr",
        tft_platform="ap",
    )
    client = RiotAPIClient(
        config=config,
        session=mock_session,
        max_retries=2,
        backoff_factor=0.1,  # 테스트에서는 짧게
        timeout=1,
    )
    return client


def test_get_success_single_request():
    # given
    mock_session = Mock()
    mock_response = make_mock_response(200, {"ok": True})
    mock_session.request.return_value = mock_response

    client = make_client_with_mock_session(mock_session)

    # when
    data = client.get("/lol/test-endpoint", game="lol")

    # then
    assert data == {"ok": True}
    mock_session.request.assert_called_once()
    _, kwargs = mock_session.request.call_args
    # method는 키워드 인자로 전달되기 때문에 kwargs로 검증
    assert kwargs["method"] == "GET"
    assert "/lol/test-endpoint" in kwargs["url"]


def test_retry_on_429_then_success():
    # given: 첫 번째 응답은 429, 두 번째는 200
    mock_session = Mock()
    resp_429 = make_mock_response(429, {"status": "rate-limited"}, headers={})
    resp_200 = make_mock_response(200, {"ok": True})
    mock_session.request.side_effect = [resp_429, resp_200]

    client = make_client_with_mock_session(mock_session)

    # when
    with patch("scripts.riot_client.time.sleep") as sleep_mock:
        data = client.get("/lol/test-endpoint", game="lol")

    # then
    assert data == {"ok": True}
    assert mock_session.request.call_count == 2
    sleep_mock.assert_called_once()  # 백오프 호출 확인


def test_retry_exceeds_max_raises_error():
    # given: 3번 모두 503 응답 (max_retries=2 → 총 3회 시도 후 실패)
    mock_session = Mock()
    resp_503 = make_mock_response(503, {"status": "server-error"}, headers={})
    mock_session.request.side_effect = [resp_503, resp_503, resp_503]

    client = make_client_with_mock_session(mock_session)

    # when / then
    with patch("scripts.riot_client.time.sleep"):
        with pytest.raises(RiotAPIError):
            client.get("/lol/test-endpoint", game="lol")


def test_invalid_game_raises_value_error():
    mock_session = Mock()
    client = make_client_with_mock_session(mock_session)

    with pytest.raises(ValueError):
        client.get("/lol/test-endpoint", game="valorant")
