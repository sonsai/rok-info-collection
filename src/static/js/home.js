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

function loadMatchList(page, keyword="") {
    document.getElementById("match_data_table").innerHTML = "<h2>Data Loading...</h2>"
    fetch(`/api/match-data?page=${page}&keyword=${keyword}`)
        .then(res => res.json())
        .then(data => {
            totalPage = data.total_page;
            currentPage = data.page;
            // 渲染内容
            header = "<table><thead><tr><th>王国<br>KINGDOM</th><th>各击杀评级人数<br>NUMBER OF KP GRADE</th><th>战斗评分<br>FIGHTING POINTS</th><th>战斗综合评级(平均)<br>FIGHT RANK</th><th>匹配积分<br>KVK SCORE</th><th>战力<br>POWER</th><th>击杀<br>KILL</th><th>历届KVK评价<br>KVK EVALUATIONS</th></tr></thead><tbody>"

            body = data.match_data_list.map(kd => `
<tr>
    <td class="kd" onclick="location.href='/kingdom-player?id=${kd['KD']}'">${kd['KD']}</td>
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
        loadMatchList(1, keyword);  // 输入结束 2 秒后搜索
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
loadMatchList(1);

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


function loadKVKList(keyword) {
    fetch(`/api/kvk-data?keyword=${keyword}`)
        .then(res => res.json())
        .then(show_data => {
            renderKVKList(show_data.data.vcr, "vcr-list");
            renderKVKList(show_data.data.on_going, "on-going-list");
            renderKVKList(show_data.data.finished, "finished-list");
        });
}

function renderKVKList(data, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";  // 清空

    const current_date = new Date();

    Object.entries(data).forEach(([key, item]) => {

        // 状态判断
        let status_label = "进行中 · Ongoing";
        if (new Date(item.start) > current_date) {
            status_label = "未开始 · Not Started";
        } else if (new Date(item.end) <= current_date) {
            status_label = "已结束 · Finished";
        }

        // 外层 item
        const itemDiv = document.createElement("div");
        itemDiv.className = `item ${item.kvk_type}`;

        // 卡片
        const card = document.createElement("div");
        card.className = item.vcr ? "item-card-vcr" : "item-card";

        // 标题
        const header = document.createElement("div");
        header.className = "item-header";
        header.innerHTML = `<div class="item-title">${key} — ${status_label}</div>`;

        // 元信息
        const meta = document.createElement("div");
        meta.className = "item-meta";
        meta.innerHTML = `
            类型 Type: ${item.kvk_type_cn || item.kvk_type || "N/A"} |
            时间 Time: ${item.start} ~ ${item.end}
        `;

        // 阵营
        const parent = document.createElement("div");
        parent.className = "parent";

        Object.entries(item.camps).forEach(([camp_name, kds]) => {
            const campDiv = document.createElement("div");
            campDiv.className = camp_name;

            const campLine = document.createElement("div");
            campLine.className = "camp-line";
            campLine.textContent = `${camp_name}:`;

            campDiv.appendChild(campLine);

            kds.sort().forEach(kd => {
                const kdDiv = document.createElement("div");
                kdDiv.className = `kd-item kd${kd}`;
                kdDiv.innerHTML = `
                    <span onclick="location.href='/kingdom-player?id=${kd}'">${kd}</span>
                `;
                campDiv.appendChild(kdDiv);
            });

            parent.appendChild(campDiv);
        });

        // 链接按钮
        const links = document.createElement("div");
        links.innerHTML = `
            <a class="button-link" href="/rok-match-data?kvk_map_id=${key}">匹配数据 Match Data</a>
            <a class="button-link" href="/rok-kvk-dkp-data?kvk_map_id=${key}">DKP 数据 DKP Data</a>
            <a class="button-link" href="/rok-kvk-player-data?kvk_map_id=${key}">玩家数据 Player Data</a>
        `;

        // 组装
        card.appendChild(header);
        card.appendChild(meta);
        card.appendChild(parent);
        card.appendChild(document.createElement("br"));
        card.appendChild(links);

        itemDiv.appendChild(card);
        container.appendChild(itemDiv);
    });
}

// 输入框防抖（2 秒）
document.getElementById("searchKvkInput").addEventListener("input", function () {
    const keyword = this.value.trim();

    clearTimeout(timer);
    timer = setTimeout(() => {
        loadKVKList(keyword);  // 输入结束 2 秒后搜索
    }, 1000);
});

// 初始化
loadKVKList("");