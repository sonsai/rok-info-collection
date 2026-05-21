from src.path_utils import get_players_json_path


def set_history_info(data, player_data_list):
    player_id = int(data.get("id"))
    player_list_data_path = get_players_json_path(player_id // 1_000_000)
    player_list_data = player_data_list.get(player_list_data_path, {})
    past_player_data = player_list_data.get(str(player_id))
    if not past_player_data:
        return data

    past_kingdom_list = past_player_data.get("kingdom", [])
    if len(past_kingdom_list) > 1:
        data["past_kingdoms"] = past_kingdom_list[-2:-5:-1]

    past_name_list = past_player_data.get("name", [])
    if len(past_name_list) > 1:
        data["past_names"] = past_name_list[-2:-5:-1]

    return data


def get_player_from_kingdom(player_id, kingdom_data) -> dict:
    for player in kingdom_data.get("data", []):
        if player["id"] == player_id:
            return player
    return {}
