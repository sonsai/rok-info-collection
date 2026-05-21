from pathlib import Path


def get_kvk_match_json_path(folder_name, kingdom_id):
    return f"data/kvk/{folder_name}/match/{kingdom_id}.json"


def get_kvk_dkp_json_path(folder_name, kingdom_id):
    return f"data/kvk/{folder_name}/dkp/{kingdom_id}.json"


def get_match_json_path(index, kingdom_id):
    return f"data/match/{index}/{kingdom_id}.json"


def get_kingdoms_json_path(days, index, kingdom_id):
    return f"data/kingdoms/{days}d/{index}/{kingdom_id}.json"


def get_evaluated_kingdoms_json_path(index, kingdom_id):
    return f"data/kingdoms/evaluated/{index}/{kingdom_id}.json"


def get_ex_evaluated_kingdoms_json_path(index, kingdom_id):
    return f"data/ex/evaluated/{index}/{kingdom_id}.json"


def get_kingdoms_kvk_history_json_path(kingdom_id):
    index = kingdom_id // 100
    return f"data/kingdoms/history/{index}/{kingdom_id}.json"


def get_players_json_path(pidx):
    return f"data/player/player_list_{pidx}.json"
