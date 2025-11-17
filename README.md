# Riot Multi-Game Persona Platform
> Cross-Title Player DNA 분석 플랫폼  
> Riot Games API(LoL / TFT / LoR 등)를 활용해 유저의 플레이스타일을 정량화하고, 멀티 게임 기반 Persona를 도출하는 데이터 플랫폼

---

## 🎯 프로젝트 한 줄 소개

Riot 계정 단위(PUUID)로 **여러 게임(LoL, TFT, LoR 등)** 의 매치 데이터를 수집하고,  
각 유저의 플레이 스타일을 수치화하여 **Player Persona(게임 성향 프로필)** 를 생성하는 플랫폼입니다.

- “이 유저는 공격적인 난투형인가, 안정적인 성장형인가?”
- “LoL에선 서포터인데, TFT에선 하이리스크 하이리턴 덱을 선호할까?”
- “여러 Riot 게임을 동시에 보는 관점에서 ‘게이머 DNA’를 정의할 수 있을까?”

이 질문에 답하기 위한 **데이터 엔지니어링 + 게임 데이터 분석** 프로젝트입니다.

---

## 🧩 메인 기능 (Planned Features)

- **멀티 게임 데이터 통합**
  - Riot PUUID 기준으로 LoL / TFT / LoR(선택) 매치 히스토리 수집
  - 게임별 → 공통 스키마로 정리 (플레이타입, 리스크 선호 등)

- **Player Persona 프로파일링**
  - 유저별 Feature Vector 생성 (공격성, 안정성, 다양성, 포지션/덱 성향 등)
  - 클러스터링 기반 Persona 군집화 (예: `Strategic Planner`, `Aggressive Fighter` 등)

- **Persona 리포트 & 대시보드**
  - “내 Riot Multi-Game Persona” 웹/대시보드
  - Persona 별 대표 지표/챔피언/덱/플레이 패턴 시각화

- **스케줄링 & 파이프라인**
  - Airflow 기반 배치 파이프라인
  - 정기적으로 신규 매치 데이터 수집 및 Persona 재계산

---

## 🏗️ 아키텍처 개요

```text
[Riot Games APIs]
  - LoL: Match / Champion Mastery / Ranked
  - TFT: Match / Ranked
  - (옵션) LoR, Valorant

          |
          v

[Airflow DAGs]
  - ingest_lol_matches
  - ingest_tft_matches
  - build_player_features
  - cluster_persona_profiles
  - quality_checks

          |
          v

[Data Lake / Warehouse]
  - raw_riot_lol_matches
  - raw_riot_tft_matches
  - dim_player, dim_game
  - fact_match_lol, fact_match_tft
  - fact_player_features
  - fact_player_persona

          |
          v

[Analytics & Apps]
  - Superset / Streamlit 대시보드
  - "My Persona" 웹 뷰
  - Persona별 통계 리포트
```

🧱 기술 스택 (Tech Stack)

Orchestration

Apache Airflow 3.x (airflow.sdk 기반 DAG)

Data & Storage

PostgreSQL or (Redshift/Snowflake 선택)

MinIO / AWS S3 (Raw 데이터 Lake)

Backend / API (옵션)

FastAPI / Django REST Framework

Frontend / Dashboard

Streamlit or React + Chart.js

Apache Superset (내부 분석용)

Others

Docker / Docker Compose

Poetry / pip-tools (Python dependency 관리)

GitHub Actions (테스트 & 린트 CI)

TODO: 실제로 확정된 스택으로 위 항목을 업데이트하세요.

📂 프로젝트 구조 (예시)
```bash
riot-multi-game-persona/
├── dags/
│   ├── persona_ingestion_lol.py
│   ├── persona_ingestion_tft.py
│   ├── persona_feature_build.py
│   └── persona_cluster_pipeline.py
├── scripts/
│   ├── riot_client.py          # Riot API 호출 공통 모듈
│   ├── extract_lol.py
│   ├── extract_tft.py
│   ├── build_features.py
│   └── cluster_persona.py
├── persona_app/
│   ├── backend/                # FastAPI (옵션)
│   └── frontend/               # Streamlit or React (옵션)
├── db/
│   ├── schema.sql              # DWH 스키마 정의
│   └── seed.sql
├── tests/
│   ├── test_riot_client.py
│   ├── test_feature_build.py
│   └── test_cluster_persona.py
├── docker-compose.yml
├── airflow/                    # Airflow 설정 (docker 이미지, env 등)
├── README.md
└── docs/
    ├── PRD.md
    ├── architecture.md
    └── data_model.md


TODO: 실제 디렉토리 구조에 맞게 수정하세요. ```



🚀 시작하기 (Getting Started)
1. 선행 조건 (Prerequisites)

Python 3.10+

Docker & Docker Compose

Riot Games Developer API Key

https://developer.riotgames.com/
 에서 발급

2. 환경 변수 설정

.env 파일 혹은 Airflow Variables로 Riot API Key를 관리합니다.

RIOT_API_KEY=your_riot_api_key_here
REGION=asia
LOL_PLATFORM=kr
TFT_PLATFORM=ap


TODO: 실제 사용하는 REGION/PLATFORM 코드로 업데이트하세요.

3. 로컬 환경 실행 (예시: Docker Compose)
# 1) 리포지토리 클론
git clone https://github.com/yourname/riot-multi-game-persona.git
cd riot-multi-game-persona

# 2) Docker 이미지 빌드 & 컨테이너 실행
docker compose up -d

# 3) Airflow UI 접속
# http://localhost:8080

🔁 파이프라인 동작 흐름
1) 데이터 수집 (Ingestion)

persona_ingestion_lol DAG

LoL match history → raw_lol_matches 테이블/파일

persona_ingestion_tft DAG

TFT match history → raw_tft_matches 테이블/파일

2) 데이터 변환 & 모델링 (Transform & Modeling)

build_player_features DAG

유저별 지표 계산

공격성(초반 교전 참여, 킬 시도, 데스 비율 등)

안정성(데스 최소화, CS, 포지셔닝 관련 지표 등)

다양성(챔피언/덱/포지션 다양성)

리스크 선호(고위험 선택 비율 등)

3) Persona 클러스터링

cluster_persona_pipeline DAG

feature 벡터 → 클러스터링(K-means 등) 수행

fact_player_persona에 Persona 라벨 저장

예: STRATEGIC_PLANNER, AGGRESSIVE_FIGHTER, TEAM_PLAYER 등

4) 대시보드 & 리포트

Superset / Streamlit에서

Persona별 통계, 플레이 패턴, 챔피언/덱 분포 시각화

(옵션) 개인 “My Persona” 조회 페이지 제공

🗺️ 3개월 로드맵 (Roadmap)

실제 진행 상황에 따라 체크박스를 업데이트하세요.

Phase 1 — Foundation & Ingestion (Week 1–4)

 Riot API 리서치 & 스키마 설계

 Docker + Airflow + DB 기본 환경 구성

 LoL / TFT 최소 PoC Ingestion DAG 구현

 Raw / Staging 레이어 테이블 구조 정의

Phase 2 — Feature & Persona Modeling (Week 5–8)

 Player Feature 지표 정의 (공격성, 안정성, 다양성, 리스크 선호 등)

 Feature 계산 파이프라인 구현 (Airflow)

 클러스터링 모델(K-means or 유사) 적용

 Persona Naming & 해석 가이드 작성

Phase 3 — Productization & Visualization (Week 9–12)

 Superset / Streamlit 대시보드 구현

 Persona별 리포트 템플릿 작성

 README / PRD / 아키텍처 문서 보완

 데모 시나리오 및 포트폴리오 정리

📜 라이선스 (License)

TODO: 오픈소스로 공개할 계획이라면 MIT, Apache-2.0 등 라이선스를 명시하세요.

🙋‍♀️ 기여 (Contributing)

이 프로젝트는 개인 포트폴리오 및 학습 목적의 프로젝트입니다.
PR, 이슈, 피드백 모두 환영합니다.

✨ Contact

Author: TODO: 이름 / GitHub / 이메일

Tags: data-engineering, airflow, riot-api, game-analytics, persona
