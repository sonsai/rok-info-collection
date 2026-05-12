document.querySelectorAll(".nav button").forEach(btn => {
    btn.addEventListener("click", function () {

        // 1. 移除所有按钮的 active
        document.querySelectorAll(".nav button").forEach(b => b.classList.remove("active"));
        this.classList.add("active");

        // 2. 隐藏所有页面
        document.querySelectorAll(".page").forEach(p => p.classList.remove("show"));

        // 3. 显示目标页面
        const target = this.dataset.target;
        document.getElementById(target).classList.add("show");
    });
});

function go() {
    const v = document.getElementById('idInput').value.trim();
    if (!v) return;
    location.href = '/kingdom-player?id=' + v;
}

let currentPage = 1;
let timer = null;
let totalPage = 1;

function loadPage(page, keyword="") {
    document.getElementById("match_data_table").innerHTML = "<h2>Data Loading...</h2>"
    fetch(`/api/data?page=${page}&keyword=${keyword}`)
        .then(res => res.json())
        .then(data => {
            totalPage = data.total_page;
            currentPage = data.page;
            // 渲染内容
            header = "<table><thead><tr><th>王国<br>KINGDOM</th><th>各击杀评级人数<br>NUMBER OF KP GRADE</th><th>战斗评分<br>FIGHTING POINTS</th><th>战斗综合评级(平均)<br>FIGHT RANK</th><th>匹配积分<br>KVK SCORE</th><th>战力<br>POWER</th><th>击杀<br>KILL</th><th>历届KVK评价<br>KVK EVALUATIONS</th></tr></thead><tbody>"

            body = data.match_data_list.map(kd => `
<tr>
    <td onclick="location.href='/kingdom-player?id=${kd['KD']}'">${kd['KD']}</td>
    <td>
        <img src="/static/media/rank/level_s.png" class="stat-icon">= ${kd['FIHGHTER-BUKETS']['s']}
        <img src="/static/media/rank/level_a.png" class="stat-icon">= ${kd['FIHGHTER-BUKETS']['a']}
        <img src="/static/media/rank/level_b.png" class="stat-icon">= ${kd['FIHGHTER-BUKETS']['b']}
        <img src="/static/media/rank/level_c.png" class="stat-icon">= ${kd['FIHGHTER-BUKETS']['c']}
        <img src="/static/media/rank/level_d.png" class="stat-icon">= ${kd['FIHGHTER-BUKETS']['d']}
    </td>
    <td>${kd['FIHGHTER-POINTS']}</td>
    <td><img src="/static/media/rank/level_${kd['FIGHTING-RANK']}.png" class="stat-icon"></td>
    <td>${kd['KVK-SCORE']}</td>
    <td>${kd['POWER']}</td>
    <td>${kd['KILL']}</td>
    <td>${kd['KVK-HISTORY']}</td>
</tr>
`).join("");
            footer = "</tbody></table>"
            document.getElementById("match_data_table").innerHTML = header + body + footer
            // 更新页码
            currentPage = data.page;
            document.getElementById("pageInfo").innerText =
                ` ${data.page} / ${data.total_page} `;
        });
}

// 输入框防抖（2 秒）
document.getElementById("searchInput").addEventListener("input", function () {
    const keyword = this.value.trim();

    clearTimeout(timer);
    timer = setTimeout(() => {
        loadPage(1, keyword);  // 输入结束 2 秒后搜索
    }, 1000);
});

// 按钮事件
document.getElementById("firstBtn").onclick = () => loadPage(1);
document.getElementById("prevBtn").onclick = () => {
    if (currentPage > 1) loadPage(currentPage - 1);
};
document.getElementById("nextBtn").onclick = () => {
    if (currentPage < totalPage) loadPage(currentPage + 1);
};
document.getElementById("lastBtn").onclick = () => loadPage(totalPage);

// 初始化
loadPage(1);

document.querySelectorAll("details").forEach((d) => {
    d.addEventListener("toggle", function () {
        if (this.open) {
            document.querySelectorAll("details").forEach((other) => {
                if (other !== this) {
                    other.open = false;
                }
            });
        }
    });
});
