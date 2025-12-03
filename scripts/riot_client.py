"""
Riot API 클라이언트 모듈

- 환경변수에서 RIOT_API_KEY, RIOT_REGION, RIOT_LOL_PLATFORM, RIOT_TFT_PLATFORM을 읽어온다.
- LoL / TFT 매치 데이터를 가져오기 위한 공통 클라이언트를 제공한다.
"""

from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

# (옵션) .env 지원 - python-dotenv가 설치되어 있으면 자동으로 .env를 읽는다.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # 개발 초기 단계에서는 굳이 의존성 강제하지 않고, 없으면 그냥 넘어간다.
    pass


# ---------------------------------------------------------------------------
# 로깅 설정
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)
if not logger.handlers:
    # 기본 핸들러가 없을 때만 간단 설정
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(name)s - %(message)s",
    )


# ---------------------------------------------------------------------------
# 설정 & 예외 정의
# ---------------------------------------------------------------------------

@dataclass
class RiotConfig:
    """
    Riot API 설정값을 한 군데에 모아두는 데이터 클래스
    """

    api_key: str
    region: str = "asia"        # match-v5, account-v1 등 regional routing (asia, americas, europe...)
    lol_platform: str = "kr"    # LoL 플랫폼(kr, jp1, na1, ...)
    tft_platform: str = "ap"    # TFT 플랫폼(ap, kr, na1, ...)

    timeout: int = 10           # 요청 타임아웃(초)
    max_retries: int = 3        # 재시도 횟수


class RiotAPIError(Exception):
    """Riot API 호출 중 발생한 오류를 감싸는 예외"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


# ---------------------------------------------------------------------------
# RiotClient 본체
# ---------------------------------------------------------------------------

class RiotClient:
    """
    Riot Games API용 HTTP 클라이언트

    - 내부적으로 requests.Session을 사용해 커넥션 재사용
    - _request() 메서드에서 공통 인증/에러 처리/재시도 로직 처리
    """

    def __init__(self, config: Optional[RiotConfig] = None):
        # config를 직접 넘겨주지 않으면 환경변수에서 읽어온다.
        if config is None:
            api_key = os.getenv("RIOT_API_KEY")
            if not api_key:
                raise ValueError(
                    "RIOT_API_KEY 환경변수가 설정되어 있지 않습니다. "
                    ".env 또는 쉘 환경에 API 키를 설정하세요."
                )

            config = RiotConfig(
                api_key=api_key,
                region=os.getenv("RIOT_REGION", "asia"),
                lol_platform=os.getenv("RIOT_LOL_PLATFORM", "kr"),
                tft_platform=os.getenv("RIOT_TFT_PLATFORM", "ap"),
            )

        self.config = config

        # Session 하나를 공유해서 TCP 커넥션 재사용 (성능 + rate limit에 조금 더 안정적)
        self.session = requests.Session()

        # Regional / Platform base URL 정의
        self.base_urls = {
            "regional": f"https://{self.config.region}.api.riotgames.com",
            "lol_platform": f"https://{self.config.lol_platform}.api.riotgames.com",
            "tft_platform": f"https://{self.config.tft_platform}.api.riotgames.com",
        }

    # -----------------------------
    # 내부 유틸 메서드
    # -----------------------------
    def _request(self, method: str, url: str, **kwargs) -> Any:
        """
        Riot API 호출 공통 래퍼

        - 인증 헤더 추가
        - 429 / 5xx에 대해 간단한 재시도
        - JSON 응답 반환, 필요 시 RiotAPIError 예외 발생
        """
        headers = kwargs.pop("headers", {})
        headers["X-Riot-Token"] = self.config.api_key

        timeout = kwargs.pop("timeout", self.config.timeout)

        last_exc: Optional[Exception] = None

        for attempt in range(1, self.config.max_retries + 1):
            try:
                resp = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=timeout,
                    **kwargs,
                )

                # Rate limit (429) 처리
                if resp.status_code == 429:
                    retry_after = resp.headers.get("Retry-After")
                    wait_seconds = int(retry_after) if retry_after else 2 ** attempt
                    logger.warning(
                        "Rate limit(429) 발생. %s초 후 재시도합니다. (attempt=%s)",
                        wait_seconds,
                        attempt,
                    )
                    time.sleep(wait_seconds)
                    continue

                # 5xx 서버 에러는 재시도
                if 500 <= resp.status_code < 600:
                    logger.warning(
                        "서버 에러(%s) 발생. 재시도합니다. (attempt=%s)",
                        resp.status_code,
                        attempt,
                    )
                    time.sleep(2 ** attempt)
                    continue

                # 그 외 2xx가 아닌 경우는 예외
                if not resp.ok:
                    raise RiotAPIError(
                        f"Riot API 요청 실패: {resp.status_code} {resp.text[:200]}",
                        status_code=resp.status_code,
                    )

                # 정상 응답 → JSON 반환
                if "application/json" in resp.headers.get("Content-Type", ""):
                    return resp.json()
                return resp.text

            except (requests.RequestException, RiotAPIError) as exc:
                last_exc = exc
                logger.exception("Riot API 요청 중 예외 발생 (attempt=%s)", attempt)
                # 마지막 시도가 아니라면 잠시 대기 후 재시도
                if attempt < self.config.max_retries:
                    time.sleep(2 ** attempt)
                    continue

        # 여기까지 왔다는 건 재시도 끝까지 실패했다는 뜻
        if isinstance(last_exc, RiotAPIError):
            raise last_exc
        raise RiotAPIError(f"Riot API 요청 반복 실패: {last_exc}")

    # -----------------------------
    # Account / Summoner 관련 메서드
    # -----------------------------

    def get_account_by_riot_id(self, game_name: str, tag_line: str) -> Dict[str, Any]:
        """
        Riot ID (gameName#tagLine) → account-v1 API로 PUUID 조회

        예: game_name="Hide on bush", tag_line="KR1"
        """
        url = (
            f"{self.base_urls['regional']}"
            f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        )
        return self._request("GET", url)

    # -----------------------------
    # LoL match-v5 메서드
    # -----------------------------

    def get_lol_match_ids_by_puuid(
        self, puuid: str, start: int = 0, count: int = 20
    ) -> List[str]:
        """
        LoL match-v5: PUUID 기준 match id 리스트 조회
        """
        url = (
            f"{self.base_urls['regional']}"
            f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        )
        params = {"start": start, "count": count}
        return self._request("GET", url, params=params)

    def get_lol_match_detail(self, match_id: str) -> Dict[str, Any]:
        """
        LoL match-v5: 특정 match id에 대한 상세 정보 조회
        """
        url = (
            f"{self.base_urls['regional']}"
            f"/lol/match/v5/matches/{match_id}"
        )
        return self._request("GET", url)

    # -----------------------------
    # TFT match-v1 메서드 (초안)
    # -----------------------------

    def get_tft_match_ids_by_puuid(
        self, puuid: str, start: int = 0, count: int = 20
    ) -> List[str]:
        """
        TFT match-v1: PUUID 기준 match id 리스트 조회
        """
        url = (
            f"{self.base_urls['regional']}"
            f"/tft/match/v1/matches/by-puuid/{puuid}/ids"
        )
        params = {"start": start, "count": count}
        return self._request("GET", url, params=params)

    def get_tft_match_detail(self, match_id: str) -> Dict[str, Any]:
        """
        TFT match-v1: 특정 match id에 대한 상세 정보 조회
        """
        url = (
            f"{self.base_urls['regional']}"
            f"/tft/match/v1/matches/{match_id}"
        )
        return self._request("GET", url)


# ---------------------------------------------------------------------------
# 간단 사용 예시 (직접 실행 시)
# ---------------------------------------------------------------------------

def _example_usage() -> None:
    """
    python scripts/riot_client.py 를 직접 실행했을 때 동작하는 예제

    주의: 실제로 테스트하려면 PUUID 또는 Riot ID를 본인 것으로 바꿔야 한다.
    """
    client = RiotClient()

    # 1) Riot ID → PUUID
    # 실제 Riot ID로 바꿔서 테스트
    # account = client.get_account_by_riot_id("게임아이디", "KR1")
    # print("Account:", account)

    # 2) PUUID 기준 LoL match id 조회 예시 (가짜 값이므로 그냥 구조만 확인용)
    sample_puuid = "PUT-YOUR-PUUID-HERE"
    try:
        match_ids = client.get_lol_match_ids_by_puuid(sample_puuid, count=5)
        print("LoL match ids:", match_ids)
    except RiotAPIError as e:
        print("API 호출 실패:", e)


if __name__ == "__main__":
    _example_usage()
