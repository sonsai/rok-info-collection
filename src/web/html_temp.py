kingdom_player_html = """
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>王国 {{ kingdom }} 数据展示</title>
<style>
    body {
        background: #0d0d0d;
        color: #fff;
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 20px;
    }

    .title {
        font-size: 28px;
        margin-bottom: 20px;
        font-weight: bold;
    }

    .player-list {
        display: flex;
        flex-direction: column;
        gap: 16px;
        max-height: 85vh;
        overflow-y: auto;
        padding-right: 10px;
    }

    .card {
        background: rgba(255, 255, 255, 0.08);
        padding: 16px 20px;
        border-radius: 10px;
        width: 100%;
        max-width: 800px;
        border-left: 4px solid #4CAF50;
    }

    .name {
        font-size: 26px;
        font-weight: bold;
        margin: 6px 0 12px 0;
    }

    .section-title {
        font-size: 16px;
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 4px;
        opacity: 0.9;
    }

    .grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 6px 10px;
        font-size: 14px;
        opacity: 0.9;
    }

    .grid span {
        display: block;
        font-weight: 600;
    }
</style>
</head>
<body>
<div><span style="cursor:pointer;" onclick="location.href='/'">返回 Back</span></div>
<br>
<div class="title">王国 {{ kingdom }}</div>
<div class="section-title">60天/180天 玩家数据 </div>
<br>

<div class="player-list">
    {% for p in players %}
    <div class="card">

        <div class="grid">
            <span>ID：{{ p.id }}</span>
        </div>
        <div class="name">{{ p.name }}</div>

        <div class="grid">
            <span><div class="section-title">战力Power： </div>{{ p.power }}</span>
            <span><div class="section-title">击杀KP：</div> {{ p.kill }} / {{ p.kill_180 or "-" }}</span>
            <span><div class="section-title">阵亡Dead：</div> {{ p.dead }} / {{ p.dead_180 or "-" }}</span>
        </div>
        <div class="section-title">击杀T1-5</div>
        <div class="grid">
            <span>T1：{{ p.t1 }} / {{ p.t1_180 or "-" }}</span>
            <span>T2：{{ p.t2 }} / {{ p.t2_180 or "-" }}</span>
            <span>T3：{{ p.t3 }} / {{ p.t3_180 or "-" }}</span>
            <span>T4：{{ p.t4 }} / {{ p.t4_180 or "-" }}</span>
            <span>T5：{{ p.t5 }} / {{ p.t5_180 or "-" }}</span>
        </div>

        <div class="section-title">阵亡T1-5</div>
        <div class="grid">
            <span>T1：{{ p.dead_t1 }} / {{ p.dead_t1_180 or "-" }}</span>
            <span>T2：{{ p.dead_t2 }} / {{ p.dead_t2_180 or "-" }}</span>
            <span>T3：{{ p.dead_t3 }} / {{ p.dead_t3_180 or "-" }}</span>
            <span>T4：{{ p.dead_t4 }} / {{ p.dead_t4_180 or "-" }}</span>
            <span>T5：{{ p.dead_t5 }} / {{ p.dead_t5_180 or "-" }}</span>
        </div>

        <div class="grid">
            <span><div class="section-title">采集Collect：</div>{{ p.collect }} / {{ p.collect_180 or "-" }}</span>
            <span><div class="section-title">帮助Help：</div>{{ p.help }} / {{ p.help_180 or "-" }}</span>
        </div>

    </div>
    {% endfor %}
</div>

</body>
</html>
"""