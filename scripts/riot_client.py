# scripts/riot_client.py

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from dotenv import load_dotenv
import requests
from requests import Response, Session

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()
class RiotAPIError(Exception):
    """Riot API 호출 중 발생하는 예외를 래핑하는 커스텀 에러."""


@dataclass
class RiotAPIConfig:
    api_key: str
    region: str          # 예: "asia", "americas", "europe", "sea"
    lol_platform: str    # 예: "kr", "jp1"
    tft_platform: str    # 예: "ap", "kr"

    @classmethod
    def from_env(cls) -> "RiotAPIConfig":
        api_key = os.getenv("RIOT_API_KEY")
        region = os.getenv("RIOT_REGION", "asia")
        lol_platform = os.getenv("LOL_PLATFORM", "kr")
        tft_platform = os.getenv("TFT_PLATFORM", "ap")

        if not api_key:
            raise ValueError(
                "RIOT_API_KEY 환경 변수가 설정되어 있지 않습니다. "
                ".env 파일 또는 시스템 환경 변수에 Riot API 키를 설정해주세요."
            )

        return cls(
            api_key=api_key,
            region=region,
            lol_platform=lol_platform,
            tft_platform=tft_platform,
        )


class RiotAPIClient:
    """
    Riot API 공통 클라이언트.

    - 재시도 & 백오프 내장
    - region / platform 기반 base URL 관리
    - JSON 반환 헬퍼 제공
    """

    def __init__(
        self,
        config: Optional[RiotAPIConfig] = None,
        session: Optional[Session] = None,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
        timeout: int = 10,
    ) -> None:
        self.config = config or RiotAPIConfig.from_env()
        self.session: Session = session or requests.Session()
        self.session.headers.update(
            {
                "X-Riot-Token": self.config.api_key,
            }
        )

        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout

        # region 기반(예: match-v5)
        self.region_base_url = f"https://{self.config.region}.api.riotgames.com"

        # game별 platform 기반(예: summoner-v4 등)
        self.platform_base_urls: Dict[str, str] = {
            "lol": f"https://{self.config.lol_platform}.api.riotgames.com",
            "tft": f"https://{self.config.tft_platform}.api.riotgames.com",
        }

    # ----------------------------
    # 내부 공통 요청 로직
    # ----------------------------
    def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> Response:
        """
        Riot API 요청을 보내고, 429/5xx에 대해 재시도하는 내부 함수.
        """
        attempt = 0

        while True:
            try:
                logger.debug("Riot API 요청: %s %s | kwargs=%s", method, url, kwargs)
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs,
                )
            except requests.RequestException as exc:
                # 네트워크 에러 시 재시도
                if attempt >= self.max_retries:
                    logger.error("Riot API 네트워크 에러 (최대 재시도 초과): %s", exc)
                    raise RiotAPIError("Riot API 네트워크 에러") from exc

                backoff = self.backoff_factor * (2**attempt)
                logger.warning(
                    "Riot API 네트워크 에러 발생, %.1f초 후 재시도합니다. (attempt=%d/%d)",
                    backoff,
                    attempt + 1,
                    self.max_retries,
                )
                time.sleep(backoff)
                attempt += 1
                continue

            # Rate limit 및 서버 에러 상태코드
            if response.status_code in (429, 500, 502, 503, 504):
                if attempt >= self.max_retries:
                    logger.error(
                        "Riot API 에러 %s (최대 재시도 초과): %s",
                        response.status_code,
                        response.text,
                    )
                    raise RiotAPIError(
                        f"Riot API 에러 {response.status_code}: {response.text}"
                    )

                retry_after_header = response.headers.get("Retry-After")
                retry_after = float(retry_after_header) if retry_after_header else 0.0
                backoff = max(retry_after, self.backoff_factor * (2**attempt))
                logger.warning(
                    "Riot API 에러 %s, %.1f초 후 재시도합니다. (attempt=%d/%d)",
                    response.status_code,
                    backoff,
                    attempt + 1,
                    self.max_retries,
                )
                time.sleep(backoff)
                attempt += 1
                continue

            if not response.ok:
                logger.error(
                    "Riot API 요청 실패: %s %s | status=%s | body=%s",
                    method,
                    url,
                    response.status_code,
                    response.text,
                )
                raise RiotAPIError(
                    f"Riot API 요청 실패: {response.status_code} {response.text}"
                )

            return response

    # ----------------------------
    # 외부에서 사용하는 헬퍼 메서드
    # ----------------------------
    def get(
        self,
        path: str,
        *,
        game: Optional[str] = None,
        use_region: bool = False,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        GET 요청 헬퍼.

        - use_region=True 인 경우: region 기반 base URL 사용 (ex. match-v5)
        - game="lol"/"tft" 인 경우: 게임별 platform 기반 base URL 사용
        """
        if use_region:
            base = self.region_base_url
        else:
            if not game:
                raise ValueError("game을 지정하거나 use_region=True로 설정해야 합니다.")
            if game not in self.platform_base_urls:
                raise ValueError(f"지원하지 않는 game 타입입니다: {game}")
            base = self.platform_base_urls[game]

        url = f"{base}{path}"
        response = self._request_with_retry("GET", url, params=params)
        return response.json()

    # ----------------------------
    # (예시) 자주 쓰일 수 있는 편의 메서드들
    # ----------------------------
    def get_lol_match_ids_by_puuid(
        self,
        puuid: str,
        count: int = 20,
    ) -> list[str]:
        """
        LoL match-v5: PUUID 기준 매치 ID 리스트 조회.
        """
        path = f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params = {"count": count}
        data = self.get(path, use_region=True, params=params)
        # match-v5는 리스트를 반환
        return list(data)

    def get_lol_match_by_id(self, match_id: str) -> Dict[str, Any]:
        """
        LoL match-v5: matchId 기준 매치 상세 조회.
        """
        path = f"/lol/match/v5/matches/{match_id}"
        return self.get(path, use_region=True)

    def get_tft_match_ids_by_puuid(
        self,
        puuid: str,
        count: int = 20,
    ) -> list[str]:
        """
        TFT match-v1: PUUID 기준 매치 ID 리스트 조회.
        (실제 엔드포인트/버전은 Riot 문서 확인 후 필요 시 수정)
        """
        path = f"/tft/match/v1/matches/by-puuid/{puuid}/ids"
        params = {"count": count}
        data = self.get(path, use_region=True, params=params)
        return list(data)

    def get_tft_match_by_id(self, match_id: str) -> Dict[str, Any]:
        """
        TFT match-v1: matchId 기준 매치 상세 조회.
        """
        path = f"/tft/match/v1/matches/{match_id}"
        return self.get(path, use_region=True)


if __name__ == "__main__":
    """
    간단 수동 테스트용 엔트리포인트.
    - .env에 환경변수 세팅 후
    - python -m scripts.riot_client
      로 실행하면 클라이언트가 초기화되는지만 확인.
    """
    try:
        client = RiotAPIClient()
    except Exception as exc:  # noqa: BLE001
        logger.error("RiotAPIClient 초기화 실패: %s", exc)
    else:
        logger.info(
            "RiotAPIClient 초기화 성공 - region=%s, lol_platform=%s, tft_platform=%s",
            client.config.region,
            client.config.lol_platform,
            client.config.tft_platform,
        )
