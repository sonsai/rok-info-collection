import datetime
import json
import os
from pathlib import Path

from .get_listed_kingdoms_member_info_api import get_listed_kingdoms_member_info_api
from .get_match_data_api import get_match_data_api
from .get_request import get_request

def get_user_info(request):
    # 优先从代理头获取真实 IP
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    print(f"Your IP is: {ip}")

def fn(n):
    if abs(n) >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    elif abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    elif abs(n) >= 1_000:
        return f"{n / 1_000:.2f}K"
    else:
        return str(n)

def get_YMD_current_date():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def get_kvk_info_json()->dict:
    url = "https://raw.githubusercontent.com/sonsai/rok-info-collection/refs/heads/main/data/kvk/kvk_info.json"
    response = get_request(url=url)
    return response.json()

def total_kingdom(data_list,camp,kingdoms):
    dkp_t4_dead = int(os.environ["DKP_T4_DEAD"])
    dkp_t5_dead = int(os.environ["DKP_T5_DEAD"])
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
    result["kingdoms"].sort(key=lambda x: float(x["DKP"][:-1]) if len(x["DKP"]) > 1 else float(x["DKP"]), reverse=True)
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
    folder_name = kvk_info["kvk_map_id"] + "_" + kvk_info["start"].replace("-","")
    camps:dict = kvk_info.get("camps")
    result = {
        "map":kvk_info.get("kvk_map_id", "Unknown"),
        "camps":[]
    }
    for key in camps.keys():
        kingdoms = camps.get(key)
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
            file_name = f"data/kvk/{folder_name}/match/{k}.json"
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
            total_dead += dead
            total_kill += kill
            total_power += power
            total_score += kvk_score
        camp["kingdoms"].sort(key=lambda x: float(x["KVK-SCORE"][:-1]) if len(x["KVK-SCORE"]) > 1 else float(x["KVK-SCORE"]), reverse=True)
        if show_sum:
            sum_json = {
                "TOTAL-KVK-SCORE":fn(total_score),
                "TOTAL-POWER":fn(total_power),
                "TOTAL-DEAD":fn(total_dead),
                "TOTAL-KILL":fn(total_kill)
            }
            camp["sum"] = sum_json

        result["camps"].append(camp)
    result["camps"].sort(key=lambda x: float(x["sum"]["TOTAL-KVK-SCORE"][:-1] if len(x["sum"]["TOTAL-KVK-SCORE"]) > 1 else float(x["sum"]["TOTAL-KVK-SCORE"])), reverse=True)
    return result

def show_kvk_dkp(kvk_info):
    start = kvk_info.get("start")
    end = kvk_info.get("end")
    camps:dict = kvk_info.get("camps")
    
    result = {
        "map":kvk_info.get("kvk_map_id", "Unknown"),
        "start":start,
        "end":end,
        "camps":[]
    }
    folder_name = kvk_info["kvk_map_id"] + "_" + kvk_info["start"].replace("-","")
    for key in camps.keys():
        kingdoms = camps.get(key)
        data_list = []
        for k in kingdoms:
            file_name = f"data/kvk/{folder_name}/dkp/{k}.json"
            if Path(file_name).exists():
                with open(file_name, "r", encoding="utf-8") as ff:
                    detail_data = json.load(ff)
            else:
                url = f"https://raw.githubusercontent.com/sonsai/rok-info-collection/refs/heads/main/data/kvk/{folder_name}/dkp/{k}.json"
                response = get_request(url=url)
                detail_data = response.json()
            data_list.append(detail_data)
        camp = total_kingdom(data_list=data_list,camp=key,kingdoms=kingdoms)
        result["camps"].append(camp)

    result["camps"].sort(key=lambda x: float(x["sum"]["TOTAL-DKP"][:-1]) if len(x["sum"]["TOTAL-DKP"]) > 1 else float(x["sum"]["TOTAL-DKP"]), reverse=True)
    return result
def json_to_dkp_data_html(data):
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>ROK KVK DKP Data</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #000;
                color: #fff;
                padding: 20px;
            }}

            h2 {{
                text-align: center;
                margin-bottom: 20px;
            }}

            h3 {{
                margin-top: 30px;
                color: #f0f0f0;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
                background-color: #111;
            }}

            th, td {{
                border: 1px solid #444;
                padding: 8px;
                text-align: center;
            }}

            th {{
                background-color: #333;
                color: #fff;
            }}

            tr:nth-child(even) {{
                background-color: #1a1a1a;
                color: #fff;
            }}

            tr:nth-child(odd) {{
                background-color: #111;
                color: #fff;
            }}

            .sum-table {{
                margin-top: 5px;
            }}
        </style>

    </head>
    <body>
        <span style="cursor:pointer;" onclick="location.href='/'">返回 Back</span>
        <h2>KVK贡献分数据 ROK KvK DKP Data</h2>
        <h2>Map: {data['map']}</h2>
        <h2>Start: {data['start']} — End: {data['end']}</h2>
    """

    html += f"<h3>TOTAL RESULT</h3>"
    html += """
    <table class="sum-table">
        <tr>
            <th>阵营 CAMP</th>
            <th>总贡献分 Total DKP</th>
            <th>总击杀 Total KILL</th>
            <th>总T4阵亡 Total T4-DEAD</th>
            <th>总T5阵亡 Total T5-DEAD</th>
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
                <th>王国 KD</th>
                <th>贡献分 DKP</th>
                <th>击杀 KILL</th>
                <th>T4阵亡数 T4-DEAD</th>
                <th>T5阵亡数 T5-DEAD</th>
                <th>数据范围 PERIOD</th>
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
            body { 
                font-family: Arial; 
                background-color: #000;   /* 黑色背景 */
                color: #fff;              /* 白色文字 */
                padding: 20px; 
            }

            h2 { 
                text-align: center; 
                color: #fff;
            }

            h3 { 
                margin-top: 30px; 
                color: #f0f0f0;
            }

            table { 
                border-collapse: collapse; 
                width: 100%; 
                margin-top: 10px; 
                background-color: #111;   /* 深色表格底色 */
            }

            th, td { 
                border: 1px solid #444;   /* 深色边框 */
                padding: 8px; 
                text-align: center; 
                color: #fff;
            }

            th { 
                background: #333; 
                color: #fff; 
            }

            tr:nth-child(even) { 
                background: #1a1a1a; 
            }

            tr:nth-child(odd) { 
                background: #111; 
            }

            .sum-table { 
                margin-top: 5px; 
            }
        </style>

    </head>
    <body>
        <span style="cursor:pointer;" onclick="location.href='/'">返回 Back</span>
        <h2>匹配数据 ROK Match Data — Map: """ + data["map"] + """</h2>
    """


    html += f"<h3>TOTAL MATCH DATA</h3>"
    html += """
    <table class="sum-table">
        <tr>
            <th>阵营 CAMP</th>
            <th>总匹配积分 TOTAL KVK SCORE</th>
            <th>总战力 TOTAL POWER</th>
            <th>总阵亡 TOTAL DEAD</th>
            <th>总击杀 TOTAL KILL</th>
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
                <th>王国 KD</th>
                <th>匹配积分 KVK SCORE</th>
                <th>战力 POWER</th>
                <th>阵亡 DEAD</th>
                <th>击杀KILL</th>
                <th>更新时间 UPDATE</th>
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
      <title>KD1545 资料站</title>
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
        .heroic_anthem  { background-image: url('/static/media/s4heroic_anthem_cover.png'); }
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
        .item-card {
            background: rgba(0, 0, 0, 0.6);
            padding: 16px 20px;
            border-radius: 10px;
        }
        .item-card-white {
            background: rgba(255, 255, 255, 0.04);
            padding: 16px 20px;
            border-radius: 10px;
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
          font-size: 18px;
          font-weight: bold;
          margin: 2px 0; 
          padding: 0px 5px;
        }
        a.button-link {
            padding: 8px 16px;
            background: #2a2a2a;       /* 深灰黑 */
            border: 1px solid #444;
            border-radius: 6px;
            color: #e0e0e0;            /* 灰白文字 */
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: 0.2s;
        }
        a.button-link:hover { background: #0056b3; }
        .kd-item {
          display: inline-block;
          padding: 4px 8px;
          margin: 3px;
          background: #2a2a2a;
          border-radius: 4px;
          font-size: 16px;
          font-weight: 600;
          color: #e0e0e0;
        }
        .kd1545 {
            background: #fc8c8c;
            color: #2a2a2a;
        }
        .search-bar {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
        }

        .search-bar {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
        }

        .search-bar input {
            width: 200px;
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid #444;
            background: #1a1a1a;
            color: #ddd;
            font-size: 14px;
            outline: none;
            transition: 0.2s;
        }

        .search-bar input::placeholder {
            color: #777;
        }

        .search-bar input:focus {
            border-color: #666;
            box-shadow: 0 0 5px #666;
        }

        .search-bar button {
            padding: 8px 16px;
            background: #2a2a2a;       /* 深灰黑 */
            border: 1px solid #444;
            border-radius: 6px;
            color: #e0e0e0;            /* 灰白文字 */
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
        }

        .search-bar button:hover {
            background: #3a3a3a;       /* 稍亮一点的灰黑 */
            border-color: #555;
            transform: translateY(-1px);
        }


      </style>
      <script>
        function go() {
            const v = document.getElementById('idInput').value.trim();
            if (!v) return;
            location.href = '/kingdom-player?id=' + v;
        }
        </script>
    </head>
    <body>
        <h1>王国/个人信息查询(测试中)</h1>
        <div class="search-bar">
            <input type="text" id="idInput" placeholder="王国ID 或 玩家ID">
            <button onclick="go()">查询 Search</button>
        </div>
        <h1>KVK 列表</h1>
    """

    for key, item in data.items():

        status_label = "进行中"
        if item["start"] > get_YMD_current_date():
            status_label = "未开始"
        elif item["end"] < get_YMD_current_date():
            status_label = "已结束"

        html += f"""
        <div class="item {item['kvk_type']}">
          <div class="{'item-card-white' if item['kvk_type'] == 'vcr' else 'item-card'}">
          <div class="item-header">
            <div class="item-title">{key} {status_label}</div>
          </div>
          
          <div class="item-meta">
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
            <a class="button-link" href="{match_base_url}{key}">匹配数据</a>
            <a class="button-link" href="{dkp_base_url}{key}">DKP数据</a>
          </div>
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