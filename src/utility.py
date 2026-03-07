import os

from .get_listed_kingdoms_member_info_api import get_listed_kingdoms_member_info_api
from .get_match_data_api import get_match_data_api


def fn(n):
    if abs(n) >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    elif abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    else:
        return str(n)

def total_kingdom(data_list):
    dkp_t4_dead = os.environ["DKP_T4_DEAD"]
    dkp_t5_dead = os.environ["DKP_T5_DEAD"]
    print(f"统计起始日:{data_list[0].get("from_date")}，统计结束日:{data_list[0].get("to_date")}")
    group_total_kill = 0
    group_total_dead_t4 = 0
    group_total_dead_t5 = 0
    for d in data_list:
        total_kill = 0
        total_dead_t4 = 0
        total_dead_t5 = 0

        # 遍历所有玩家
        for p in d.get("data"):
            total_kill += p.get("kill", 0)
            total_dead_t4 += p.get("dead_t4", 0)
            total_dead_t5 += p.get("dead_t5", 0)
        # 输出结果
        print(f"王国:{d.get("kingdom")}",end=" ")
        print(f"总Kill: {total_kill/100000000:.1f} 亿",end=" ")
        print(f"总dead_t4: {total_dead_t4/10000:.1f} 万",end=" ")
        print(f"总dead_t5: {total_dead_t5/10000:.1f} 万")
        group_total_kill += total_kill
        group_total_dead_t4 += total_dead_t4
        group_total_dead_t5 += total_dead_t5
    # 输出结果
    print(f"阵营总Kill: {group_total_kill/100000000:.1f} 亿",end=" ")
    print(f"dead_t4: {group_total_dead_t4/10000:.1f} 万",end=" ")
    print(f"dead_t5: {group_total_dead_t5/10000:.1f} 万")
    print(f"阵营总DKP: {(group_total_kill+group_total_dead_t4*dkp_t4_dead+group_total_dead_t5*dkp_t5_dead)/1000000000:.1f} B")

def show_kvk_match_data(
        kvk_info,show_kingdom:bool=True, 
        show_sum:bool=True
    ):
    
    camps:dict = kvk_info.get("camps")
    print("-------KVK MATCH DATAS-------")
    print(f"MAP:{kvk_info.get("kvk_map_id", "Unknown")}")
    for key in camps.keys():
        kingdoms = camps.get(key)
        print(f"CAMP:{key} {kingdoms}")
        total_dead = 0
        total_kill = 0
        total_power = 0
        total_score = 0
        for k in kingdoms:
            response = get_match_data_api(str(k))
            dead = response["data"]["dead"]
            kill = response["data"]["kill"]
            power = response["data"]["power"]
            kvk_score = response["data"]["kvkKillScore"]
            if show_kingdom:
                print(f"KD:{k},KVK-SCORE:{fn(kvk_score)},POWER:{fn(power)},DEAD:{fn(dead)},KILL:{fn(kill)}")
            total_dead += dead
            total_kill += kill
            total_power += power
            total_score += kvk_score
        if show_sum:
            print(f"TOTAL-KVK-SCORE:{fn(total_score)},TOTAL-POWER:{fn(total_power)},TOTAL-DEAD:{fn(total_dead)},TOTAL-KILL:{fn(total_kill)}")

def show_kvk_dkp(kvk_info):
    print("-------KVK DKP-------")
    start = kvk_info.get("start")
    end = kvk_info.get("end")
    camps:dict = kvk_info.get("camps")
    
    print(f"MAP:{kvk_info.get("kvk_map_id", "Unknown")}")
    for key in camps.keys():
        kingdoms = camps.get(key)
        print(f"CAMP:{key}")
        data_list = []
        for k in kingdoms:
            response = get_listed_kingdoms_member_info_api(
                from_date=start,
                kingdom_id=str(k))
            data = response.get("data")
            detail_data = {
                "kingdom":k,
                "from_date":start,
                "to_date":end,
                "data":data
            }
            data_list.append(detail_data)
        total_kingdom(data_list=data_list)