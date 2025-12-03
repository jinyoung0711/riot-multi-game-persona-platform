import os
import json
from pathlib import Path
from typing import List, Dict, Any

from scripts.riot_client import RiotClient, RiotAPIError


# LoL raw 데이터를 저장할 디렉토리
OUTPUT_DIR = Path("data/raw/lol")


def save_match_json(match_id: str, match_data: Dict[str, Any]) -> None:
    """
    단일 match 데이터를 JSON 파일로 저장한다.
    파일 경로: data/raw/lol/{match_id}.json
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{match_id}.json"

    # 나중에 idempotent하게 바꾸기 좋게, 지금은 그냥 덮어쓰기
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(match_data, f, ensure_ascii=False, indent=2)

    print(f"[SAVE] {out_path}")


def fetch_and_save_lol_matches(puuid: str, count: int = 5) -> List[str]:
    """
    주어진 PUUID에 대해 LoL match id 리스트를 조회하고,
    각 match detail을 가져와 JSON 파일로 저장한다.

    반환값: 성공적으로 저장한 match_id 리스트
    """
    client = RiotClient()

    # 1) match id 리스트 가져오기
    try:
        match_ids = client.get_lol_match_ids_by_puuid(puuid, count=count)
    except RiotAPIError as e:
        print("[ERROR] match id 조회 실패:", e)
        return []

    print(f"[INFO] match ids ({len(match_ids)}개): {match_ids}")

    saved_ids: List[str] = []

    # 2) match detail 하나씩 가져와서 저장
    for match_id in match_ids:
        try:
            match_data = client.get_lol_match_detail(match_id)
        except RiotAPIError as e:
            print(f"[ERROR] match detail 조회 실패: {match_id} - {e}")
            continue

        save_match_json(match_id, match_data)
        saved_ids.append(match_id)

    return saved_ids


def main() -> None:
    """
    실행 진입점.

    - TEST_PUUID 환경변수에서 PUUID를 읽어온다.
    - 최근 5개 매치만 테스트로 수집해서 data/raw/lol/ 아래에 저장한다.
    """
    puuid = os.getenv("TEST_PUUID")
    if not puuid:
        print(
            "TEST_PUUID 환경변수가 설정되어 있지 않습니다.\n"
            "1) .env 파일에 TEST_PUUID=... 추가하고\n"
            "2) 다시 실행하세요."
        )
        return

    saved_match_ids = fetch_and_save_lol_matches(puuid, count=5)
    print(f"[DONE] 총 {len(saved_match_ids)}개 매치 저장 완료.")


if __name__ == "__main__":
    main()
