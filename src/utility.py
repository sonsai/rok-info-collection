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
    if data_list:
        print(f'统计起始日:{data_list[0].get("from_date")}，统计结束日:{data_list[0].get("to_date")}', file=file)
    group_total_kill = 0
    group_total_dead_t4 = 0
    group_total_dead_t5 = 0
    result = {
        "name": camp,
        "kingdoms_names":kingdoms,
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
            "PERIOD":d["from_date"] + " ~ " + d["to_date"],
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
            print(f'CAMP:{key} {str(kingdoms)}', file=f)
            camp = {
                "name": key ,
                "kingdoms_names": kingdoms,
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
        folder_name = kvk_info["kvk_map_id"] + "_" + kvk_info["start"].replace("-","")
        for key in camps.keys():
            kingdoms = camps.get(key)
            print(f'CAMP:{key}', file=f)
            data_list = []
            for k in kingdoms:
                file_name = f"data/kvk/{folder_name}/{k}.json"
                if Path(file_name).exists():
                    with open(file_name, "r", encoding="utf-8") as ff:
                        detail_data = json.load(ff)
                else:
                    url = f"https://raw.githubusercontent.com/sonsai/rok-info-collection/refs/heads/main/data/kvk/{folder_name}/{k}.json"
                    response = get_request(url=url)
                    detail_data = response.json()
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

    html += f"<h3>TOTAL RESULT</h3>"
    html += """
    <table class="sum-table">
        <tr>
            <th>CAMP</th>
            <th>Total DKP</th>
            <th>Total KILL</th>
            <th>Total T4-DEAD</th>
            <th>Total T5-DEAD</th>
        </tr>
    """
    for camp in data["camps"]:
        s = camp["sum"]
        html += f"""
            <tr>
                <td>{camp['name']}</td>
                <td>{s['TOTAL-DKP']}</td>
                <td>{s['TOTAL-KILL']}</td>
                <td>{s['TOTAL-T4_DEAD']}</td>
                <td>{s['TOTAL-T5_DEAD']}</td>
            </tr>
        """
    html += """
    </table>
    """
    for camp in data["camps"]:
        html += f"<h3>{camp['name'] + ' ' + str(camp['kingdoms_names'])}</h3>"
        html += """
        <table>
            <tr>
                <th>KD</th>
                <th>DKP</th>
                <th>KILL</th>
                <th>T4-DEAD</th>
                <th>T5-DEAD</th>
                <th>PERIOD</th>
            </tr>
        """

        for kd in camp["kingdoms"]:
            html += f"""
            <tr>
                <td>{kd['KD']}</td>
                <td>{kd['DKP']}</td>
                <td>{kd['KILL']}</td>
                <td>{kd['T4-DEAD']}</td>
                <td>{kd['T5-DEAD']}</td>
                <td>{kd['PERIOD']}</td>
            </tr>
            """
        html += """
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


    html += f"<h3>TOTAL MATCH DATA</h3>"
    html += """
    <table class="sum-table">
        <tr>
            <th>CAMP</th>
            <th>TOTAL KVK SCORE</th>
            <th>TOTAL POWER</th>
            <th>TOTAL DEAD</th>
            <th>TOTAL KILL</th>
        </tr>
    """
    for camp in data["camps"]:
        # Sum table
        s = camp["sum"]
        html += f"""
            <tr>
                <td>{camp['name']}</td>
                <td>{s['TOTAL-KVK-SCORE']}</td>
                <td>{s['TOTAL-POWER']}</td>
                <td>{s['TOTAL-DEAD']}</td>
                <td>{s['TOTAL-KILL']}</td>
            </tr>
        """
        
    html += """
        </table>
        """
    for camp in data["camps"]:
        html += f"<h3>{camp['name'] + ' ' + str(camp['kingdoms_names'])}</h3>"

        # Kingdoms table
        html += """
        <table>
            <tr>
                <th>KD</th>
                <th>KVK SCORE</th>
                <th>POWER</th>
                <th>DEAD</th>
                <th>KILL</th>
                <th>LATEST UPDATE</th>
            </tr>
        """

        for kd in camp["kingdoms"]:
            html += f"""
            <tr>
                <td>{kd['KD']}</td>
                <td>{kd['KVK-SCORE']}</td>
                <td>{kd['POWER']}</td>
                <td>{kd['DEAD']}</td>
                <td>{kd['KILL']}</td>
                <td>{kd['UPDATED-AT']}</td>
            </tr>
            """

        html += "</table>"

    html += "</body></html>"
    return html

def json_to_root_data(data):
    match_base_url = "https://rok-info-collection.onrender.com/rok-match-data?kvk_map_id="
    dkp_base_url = "https://rok-info-collection.onrender.com/rok-kvk-dkp-data?kvk_map_id="

    html = """
    <!DOCTYPE html>
    <html lang="zh">
    <head>
      <meta charset="UTF-8">
      <title>KVK 列表</title>
      <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
        .item {
          background-size: cover;
          background-position: center;
          background-repeat: no-repeat;
          padding: 30px;
          border-radius: 10px;
          color: white;
        }
        .tides_of_war  { background-image: url('/static/media/s14tides_of_war_cover.png'); }
        .king_of_all_britain { background-image: url('/static/media/s19king_of_all_britain_cover.png'); }
        .vcr { background-image: url('/static/media/vcr.png'); }
        .king_of_the_nile { background-image: url('/static/media/s9king_of_the_nile_cover.png'); }
        .siege_of_orleans { background-image: url('/static/media/s10siege_of_orleans_cover.png'); }
        .warriors_unbound { background-image: url('/static/media/s11warriors_unbound_cover.png'); }
        .storm_of_stratagems { background-image: url('/static/media/s12storm_of_stratagems_cover.png'); }
        .item-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }
        .item-title {
          font-size: 25px;
          font-weight: bold;
        }
        .item-meta {
          font-size: 20px;
          color: #fff;
        }
        .camps { margin-top: 8px; font-size: 14px; }
        .camp-line { 
          font-size: 23px;
          margin: 2px 0; 
        }
        a.button-link {
          padding: 6px 12px;
          background: #007bff;
          color: #fff;
          text-decoration: none;
          border-radius: 4px;
          font-size: 14px;
        }
        a.button-link:hover { background: #0056b3; }
        .kd-item {
          display: inline-block;
          padding: 4px 8px;
          margin: 3px;
          background: gray;
          border-radius: 4px;
          font-size: 20px;
        }
        .kd1545 {
            background: #fc8c8c
        }
      </style>
    </head>
    <body>
      <h1>KINGDOM 1545 内部数据分析</h1>
      <h2>KVK 列表</h2>
    """

    for key, item in data.items():
        html += f"""
        <div class="item {item['kvk_type'] or 'N/A'}">
          <div class="item-header">
            <div class="item-title">{key}</div>
          </div>
          
          <div class="item-meta">
            KVK ID: {item['kvk_map_id']} |
            类型: {item.get("kvk_type_cn") or item['kvk_type'] or 'N/A'} |
            时间: {item['start']} ~ {item['end']}
          </div>
          <div class="camps">
        """

        for camp_name, kds in item["camps"].items():
            html += f'<div class="camp-line">{camp_name}:</div>'
            for kd in kds:
                html += f'<div class="kd-item kd{kd}">{kd}</div>'

        html += f"""
          </div>
          <br>
          <div>
            <a class="button-link" href="{match_base_url}{key}" target="_blank">匹配数据</a>
            <a class="button-link" href="{dkp_base_url}{key}" target="_blank">DKP数据</a>
          </div>
        </div>
        <br>
        <br>
        """

    html += """
    </body>
    </html>
    """

    return html