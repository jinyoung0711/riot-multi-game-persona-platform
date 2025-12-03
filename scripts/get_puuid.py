from scripts.riot_client import RiotClient, RiotAPIError


def main() -> None:
    """
    Riot ID(gameName#tagLine)로 내 PUUID를 조회해서 출력하는 스크립트
    """
    # TODO: 여기 두 줄을 본인 Riot ID로 바꿔줘야 함!
    game_name = "김종휘"   # 예: "Hide on bush"
    tag_line = "휘리릭"          # 예: "KR1"

    client = RiotClient()

    try:
        account = client.get_account_by_riot_id(game_name, tag_line)
    except RiotAPIError as e:
        print("Riot API 호출 실패:", e)
        return

    # account-v1 응답에는 일반적으로 puuid, gameName, tagLine 등이 들어 있음
    print("=== Riot Account Info ===")
    print(f"gameName : {account.get('gameName')}")
    print(f"tagLine  : {account.get('tagLine')}")
    print(f"puuid    : {account.get('puuid')}")


if __name__ == "__main__":
    main()
