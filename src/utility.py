import datetime
import json
import os
from pathlib import Path

from .get_listed_kingdoms_member_info_api import get_listed_kingdoms_member_info_api
from .get_match_data_api import get_match_data_api
from .get_request import get_request


def fn(n):
    if abs(n) >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    elif abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    elif abs(n) >= 1_000:
        return f"{n / 1_000:.2f}K"
    else:
        return str(n)

def get_kvk_info_json()->dict:
    url = "https://raw.githubusercontent.com/sonsai/rok-info-collection/refs/heads/main/data/kvk/kvk_info.json"
    response = get_request(url=url)
    return response.json()

def total_kingdom(data_list,camp,kingdoms,file):
    dkp_t4_dead = int(os.environ["DKP_T4_DEAD"])
    dkp_t5_dead = int(os.environ["DKP_T5_DEAD"])
    print(f'统计起始日:{data_list[0].get("from_date")}，统计结束日:{data_list[0].get("to_date")}', file=file)
    group_total_kill = 0
    group_total_dead_t4 = 0
    group_total_dead_t5 = 0
    result = {
        "name": f'CAMP:{camp} {kingdoms}',
        "kingdoms":[],
        "sum":{}
    }
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
        print(f'王国:{d.get("kingdom")}',end=" ", file=file)
        print(f'总Kill: {total_kill/100000000:.1f} 亿',end=" ", file=file)
        print(f'总dead_t4: {total_dead_t4/10000:.1f} 万',end=" ", file=file)
        print(f'总dead_t5: {total_dead_t5/10000:.1f} 万', file=file)
        kingdom_json = {
            "KD":d.get("kingdom"),
            "KILL":fn(total_kill),
            "T4-DEAD":fn(total_dead_t4),
            "T5-DEAD":fn(total_dead_t5),
            "DKP":fn(total_kill + total_dead_t4 * dkp_t4_dead + total_dead_t5 * dkp_t5_dead)
        }
        result["kingdoms"].append(kingdom_json)
        group_total_kill += total_kill
        group_total_dead_t4 += total_dead_t4
        group_total_dead_t5 += total_dead_t5
    # 输出结果
    print(f'阵营总Kill: {group_total_kill/100000000:.1f} 亿',end=" ", file=file)
    print(f'dead_t4: {group_total_dead_t4/10000:.1f} 万',end=" ", file=file)
    print(f'dead_t5: {group_total_dead_t5/10000:.1f} 万', file=file)
    print(f'阵营总DKP: {(group_total_kill+group_total_dead_t4*dkp_t4_dead+group_total_dead_t5*dkp_t5_dead)/1000000000:.1f} B', file=file)
    sum = {
        "TOTAL-KILL":fn(group_total_kill),
        "TOTAL-T4_DEAD":fn(group_total_dead_t4),
        "TOTAL-T5_DEAD":fn(group_total_dead_t5),
        "TOTAL-DKP":fn(group_total_kill+group_total_dead_t4*dkp_t4_dead+group_total_dead_t5*dkp_t5_dead)
    }
    result["sum"] = sum
    return result

def show_kvk_match_data(
        kvk_info,
        show_kingdom:bool=True, 
        show_sum:bool=True
    ):

    result = {}
    os.makedirs("data", exist_ok=True)
    file_path = "data/match_data_result.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        camps:dict = kvk_info.get("camps")
        print("-------KVK MATCH DATAS-------", file=f)
        print(f'MAP:{kvk_info.get("kvk_map_id", "Unknown")}', file=f)
        result = {
            "map":kvk_info.get("kvk_map_id", "Unknown"),
            "camps":[]
        }
        for key in camps.keys():
            kingdoms = camps.get(key)
            print(f'CAMP:{key} {kingdoms}', file=f)
            camp = {
                "name": f'CAMP:{key} {kingdoms}',
                "kingdoms":[],
            }
            total_dead = 0
            total_kill = 0
            total_power = 0
            total_score = 0
            for k in kingdoms:
                file_name = f"data/match/{k}.json"
                if Path(file_name).exists():
                    with open(file_name, "r", encoding="utf-8") as ff:
                        detail_data = json.load(ff)
                else:
                    response_dict = get_match_data_api(str(k))
                    data = response_dict.get("data")
                    detail_data = {
                        "kingdom":k,
                        "date":datetime.datetime.now().strftime("%Y-%m-%d"),
                        "data":data
                    }
                    # with open(file_name, "w", encoding="utf-8") as f:
                    #     json.dump(detail_data, f, ensure_ascii=False, indent=2)
                dead = detail_data["data"]["dead"]
                kill = detail_data["data"]["kill"]
                power = detail_data["data"]["power"]
                kvk_score = detail_data["data"]["kvkKillScore"]
                if show_kingdom:
                    kingdom_json = {
                        "KD":k,
                        "UPDATED-AT":detail_data["data"]["day"],
                        "KVK-SCORE":fn(kvk_score),
                        "POWER":fn(power),
                        "DEAD":fn(dead),
                        "KILL":fn(kill)
                    }
                    camp["kingdoms"].append(kingdom_json)
                    print(f'KD:{k},KVK-SCORE:{fn(kvk_score)},POWER:{fn(power)},DEAD:{fn(dead)},KILL:{fn(kill)}', file=f)
                total_dead += dead
                total_kill += kill
                total_power += power
                total_score += kvk_score
            if show_sum:
                sum_json = {
                    "TOTAL-KVK-SCORE":fn(total_score),
                    "TOTAL-POWER":fn(total_power),
                    "TOTAL-DEAD":fn(total_dead),
                    "TOTAL-KILL":fn(total_kill)
                }
                camp["sum"] = sum_json
                print(f'TOTAL-KVK-SCORE:{fn(total_score)},TOTAL-POWER:{fn(total_power)},TOTAL-DEAD:{fn(total_dead)},TOTAL-KILL:{fn(total_kill)}', file=f)

            result["camps"].append(camp)
    return result

def show_kvk_dkp(kvk_info):
    os.makedirs("data", exist_ok=True)
    file_path = "data/dkp_data_result.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        print("-------KVK DKP-------", file=f)
        start = kvk_info.get("start")
        end = kvk_info.get("end")
        camps:dict = kvk_info.get("camps")
        
        print(f'MAP:{kvk_info.get("kvk_map_id", "Unknown")}', file=f)
        result = {
            "map":kvk_info.get("kvk_map_id", "Unknown"),
            "start":start,
            "end":end,
            "camps":[]
        }
        for key in camps.keys():
            kingdoms = camps.get(key)
            print(f'CAMP:{key}', file=f)
            data_list = []
            for k in kingdoms:
                file_name = f"data/kingdoms/{k}.json"
                if Path(file_name).exists():
                    with open(file_name, "r", encoding="utf-8") as ff:
                        detail_data = json.load(ff)
                else:
                    response = get_listed_kingdoms_member_info_api(
                        from_date=start,
                        to_date=end,
                        kingdom_id=str(k))
                    data = response.get("data")
                    detail_data = {
                        "kingdom":k,
                        "from_date":start,
                        "to_date":end,
                        "data":data
                    }
                data_list.append(detail_data)
            camp = total_kingdom(data_list=data_list,camp=key,kingdoms=kingdoms, file=f)
            result["camps"].append(camp)
    return result
def json_to_dkp_data_html(data):
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>ROK KVK DKP Data</title>
        <style>
            body {{ font-family: Arial; background: #f5f5f5; padding: 20px; }}
            h2 {{ text-align: center; }}
            h3 {{ margin-top: 30px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: center; }}
            th {{ background: #333; color: #fff; }}
            tr:nth-child(even) {{ background: #eee; }}
            .sum-table {{ margin-top: 5px; }}
        </style>
    </head>
    <body>
        <h2>ROK KvK DKP Data — Map: {data['map']}</h2>
        <h2>Start: {data['start']} — End: {data['end']}</h2>
    """

    for camp in data["camps"]:
        html += f"<h3>{camp['name']}</h3>"
        html += """
        <table>
            <tr>
                <th>KD</th>
                <th>KILL</th>
                <th>T4-DEAD</th>
                <th>T5-DEAD</th>
                <th>DKP</th>
            </tr>
        """

        for kd in camp["kingdoms"]:
            html += f"""
            <tr>
                <td>{kd['KD']}</td>
                <td>{kd['KILL']}</td>
                <td>{kd['T4-DEAD']}</td>
                <td>{kd['T5-DEAD']}</td>
                <td>{kd['DKP']}</td>
            </tr>
            """

        s = camp["sum"]
        html += f"""
        </table>
        <table class="sum-table">
            <tr><th colspan="4">SUM</th></tr>
            <tr>
                <td>Total Kill: {s['TOTAL-KILL']}</td>
                <td>Total T4 Dead: {s['TOTAL-T4_DEAD']}</td>
                <td>Total T5 Dead: {s['TOTAL-T5_DEAD']}</td>
                <td>Total DKP: {s['TOTAL-DKP']}</td>
            </tr>
        </table>
        """

    html += "</body></html>"
    return html

def json_to_match_data_html(data):
    html = """
    <html>
    <head>
        <meta charset="UTF-8">
        <title>ROK Match Data</title>
        <style>
            body { font-family: Arial; background: #f5f5f5; padding: 20px; }
            h2 { text-align: center; }
            h3 { margin-top: 30px; }
            table { border-collapse: collapse; width: 100%; margin-top: 10px; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: center; }
            th { background: #333; color: #fff; }
            tr:nth-child(even) { background: #eee; }
            .sum-table { margin-top: 5px; }
        </style>
    </head>
    <body>
        <h2>ROK Match Data — Map: """ + data["map"] + """</h2>
    """

    for camp in data["camps"]:
        html += f"<h3>{camp['name']}</h3>"

        # Kingdoms table
        html += """
        <table>
            <tr>
                <th>KD</th>
                <th>UPDATE AT</th>
                <th>KVK SCORE</th>
                <th>POWER</th>
                <th>DEAD</th>
                <th>KILL</th>
            </tr>
        """

        for kd in camp["kingdoms"]:
            html += f"""
            <tr>
                <td>{kd['KD']}</td>
                <td>{kd['UPDATED-AT']}</td>
                <td>{kd['KVK-SCORE']}</td>
                <td>{kd['POWER']}</td>
                <td>{kd['DEAD']}</td>
                <td>{kd['KILL']}</td>
            </tr>
            """

        html += "</table>"

        # Sum table
        s = camp["sum"]
        html += f"""
        <table class="sum-table">
            <tr><th colspan="4">SUM</th></tr>
            <tr>
                <td>Total KVK Score: {s['TOTAL-KVK-SCORE']}</td>
                <td>Total Power: {s['TOTAL-POWER']}</td>
                <td>Total Dead: {s['TOTAL-DEAD']}</td>
                <td>Total Kill: {s['TOTAL-KILL']}</td>
            </tr>
        </table>
        """

    html += "</body></html>"
    return html