import os
import json
from pathlib import Path

from dotenv import load_dotenv  
from scripts.lol_models import LolPlayerMatch  

load_dotenv()  

TEST_PUUID = os.getenv("TEST_PUUID")

match_path = Path("data/raw/lol/KR_7932515732.json")
with match_path.open(encoding="utf-8") as f:
    match_json = json.load(f)

player_match = LolPlayerMatch.from_riot_match(match_json, TEST_PUUID)
print(player_match)
