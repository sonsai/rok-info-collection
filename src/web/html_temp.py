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
        gap: 12px;
        max-height: 90vh;
        overflow-y: auto;
        padding-right: 10px;
    }

    .card {
        background: rgba(255, 255, 255, 0.08);
        padding: 12px 16px;
        border-radius: 8px;
        display: flex;
        flex-direction: column;
        width: fit-content;
        min-width: 320px;
        border-left: 4px solid #4CAF50;
    }

    .name {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 6px;
    }

    .row {
        display: flex;
        gap: 20px;
        font-size: 14px;
        opacity: 0.9;
    }

    .row span {
        display: inline-block;
        min-width: 120px;
    }
</style>
</head>
<body>

<div class="title">王国 {{ kingdom }} - 玩家数据</div>
<h2>{{ start }} - {{ end }}</h2>

<div class="player-list">
    {% for p in players %}
    <div class="card">
        <div class="row">
            <span>ID：{{ p.id }}</span>
        </div>
        <div class="name">
            <span>{{ p.name }}</span>
        </div>
        <div class="row">
            <span>战力：{{ p.power }}</span>
            <span>阵亡：{{ p.dead }}</span>
            <span>击杀：{{ p.kill }}</span>
        </div>
        <div class="row">
          <span>T1击杀：{{ p.t1 }}</span>
          <span>T2击杀：{{ p.t2 }}</span>
          <span>T3击杀：{{ p.t3 }}</span>
          <span>T4击杀：{{ p.t4 }}</span>
          <span>T5击杀：{{ p.t5 }}</span>
        </div>
        <div class="row">
          <span>T1阵亡：{{ p.dead_t1 }}</span>
          <span>T2阵亡：{{ p.dead_t2 }}</span>
          <span>T3阵亡：{{ p.dead_t3 }}</span>
          <span>T4阵亡：{{ p.dead_t4 }}</span>
          <span>T5阵亡：{{ p.dead_t5 }}</span>
        </div>
        <div class="row">
            <span>采集：{{ p.collect }}</span>
            <span>援助：{{ p.help }}</span>
        </div>
    </div>
    {% endfor %}
</div>

</body>
</html>
"""