CREATE TABLE IF NOT EXISTS fact_lol_player_match (
    match_id           VARCHAR(64)   NOT NULL,
    puuid              VARCHAR(128)  NOT NULL,
    
    -- 메타
    game_mode          VARCHAR(32)   NOT NULL,
    game_duration      INT           NOT NULL,
    game_creation_ts   BIGINT        NOT NULL,

    -- 플레이어 기본
    champion_name      VARCHAR(64)   NOT NULL,
    team_id            INT           NOT NULL,
    team_position      VARCHAR(32)   NOT NULL,
    role               VARCHAR(32)   NOT NULL,
    win                BOOLEAN       NOT NULL,

    -- 전투/운영 스탯
    kills              INT           NOT NULL,
    deaths             INT           NOT NULL,
    assists            INT           NOT NULL,
    kda                NUMERIC(6,2)  NOT NULL,
    dmg_to_champions   INT           NOT NULL,
    dmg_per_min        NUMERIC(10,4) NOT NULL,
    gold_earned        INT           NOT NULL,
    gold_per_min       NUMERIC(10,4) NOT NULL,
    cs                 INT           NOT NULL,
    cs_per_min         NUMERIC(10,4) NOT NULL,
    vision_score       NUMERIC(10,2) NOT NULL,

    created_at         TIMESTAMP     NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_fact_lol_player_match PRIMARY KEY (match_id, puuid)
);
