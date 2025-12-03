# scripts/lol_models.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class LolPlayerMatch:
    # 메타
    match_id: str
    game_mode: str
    game_duration: int  # seconds
    game_creation: int  # timestamp (ms)

    # 플레이어 기본
    puuid: str
    champion_name: str
    team_id: int
    team_position: str
    role: str
    win: bool

    # 전투/운영 스탯
    kills: int
    deaths: int
    assists: int
    kda: float

    damage_to_champions: int
    damage_per_min: float
    gold_earned: int
    gold_per_min: float

    cs: int
    cs_per_min: float
    vision_score: float

    @classmethod
    def from_riot_match(cls, match: Dict[str, Any], puuid: str) -> "LolPlayerMatch":
        """한 개의 Riot match JSON + 대상 puuid -> LolPlayerMatch 로 변환"""

        info = match["info"]
        meta = match["metadata"]

        game_duration: int = info["gameDuration"]  # 초 단위
        game_creation: int = info["gameCreation"]  # timestamp(ms)

        # 이 경기에서 해당 puuid인 플레이어 찾기
        try:
            participant = next(p for p in info["participants"] if p["puuid"] == puuid)
        except StopIteration:
            raise ValueError(f"puuid={puuid} 가 이 매치에 존재하지 않습니다. match_id={meta.get('matchId')}")

        kills = participant["kills"]
        deaths = participant["deaths"]
        assists = participant["assists"]

        # 0데스일 때 0으로 나누지 않도록 방어
        kda = (kills + assists) / max(1, deaths)

        total_cs = participant.get("totalMinionsKilled", 0) + participant.get("neutralMinionsKilled", 0)
        minutes = game_duration / 60.0 if game_duration > 0 else 1.0
        cs_per_min = total_cs / minutes

        challenges = participant.get("challenges", {}) or {}
        damage_per_min = float(challenges.get("damagePerMinute", 0.0))
        gold_per_min = float(challenges.get("goldPerMinute", 0.0))

        return cls(
            # 메타
            match_id=meta["matchId"],
            game_mode=info["gameMode"],
            game_duration=game_duration,
            game_creation=game_creation,

            # 플레이어 기본
            puuid=puuid,
            champion_name=participant["championName"],
            team_id=participant["teamId"],
            team_position=participant.get("teamPosition") or participant.get("individualPosition", "UNKNOWN"),
            role=participant.get("role", "UNKNOWN"),
            win=participant["win"],

            # 전투/운영
            kills=kills,
            deaths=deaths,
            assists=assists,
            kda=kda,
            damage_to_champions=participant.get("totalDamageDealtToChampions", 0),
            damage_per_min=damage_per_min,
            gold_earned=participant.get("goldEarned", 0),
            gold_per_min=gold_per_min,
            cs=total_cs,
            cs_per_min=cs_per_min,
            vision_score=float(participant.get("visionScore", 0.0)),
        )
