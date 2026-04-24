function parseKMN(value) {
    if (typeof value === "number") return value; // 已经是数字

    const str = String(value).trim().toUpperCase();

    if (str.endsWith("K")) {
        return parseFloat(str) * 1_000;
    }
    if (str.endsWith("M")) {
        return parseFloat(str) * 1_000_000;
    }
    if (str.endsWith("B")) {
        return parseFloat(str) * 1_000_000_000;
    }

    return Number(str); // 普通数字字符串
}
function formatKMN(num) {
    if (typeof num !== "number" || isNaN(num)) return num;

    if (num >= 1_000_000_000) {
        return (num / 1_000_000_000).toFixed(2).replace(/\.00$/, "") + "B";
    }
    if (num >= 1_000_000) {
        return (num / 1_000_000).toFixed(2).replace(/\.00$/, "") + "M";
    }
    if (num >= 1_000) {
        return (num / 1_000).toFixed(2).replace(/\.00$/, "") + "K";
    }

    return String(num);
}

let killsChart = null;
let helpChart = null;
let collectChart = null;
document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("playerModal");
    const modalBody = document.getElementById("modal-body");
    const closeBtn = document.querySelector(".close-btn");

    document.querySelectorAll(".card").forEach(card => {
        card.addEventListener("click", function () {

            const p = JSON.parse(this.dataset.player);
            const kill_30 = JSON.parse(p.kill);
            const cumulativeKills = kill_30.reduce((acc, cur) => {
                const last = acc.length > 0 ? acc[acc.length - 1] : 0;
                acc.push(last + cur);
                return acc;
            }, []);
            const kill_days = kill_30.length
            const kill_labels = kill_30.map((_, i) => `${kill_days - i}天前`);
            const collect_30 = JSON.parse(p.collect);
            const collect_days = collect_30.length
            const collect_labels = collect_30.map((_, i) => `${collect_days - i}天前`);
            const help_30 = JSON.parse(p.help);
            const help_days = help_30.length
            const help_labels = help_30.map((_, i) => `${help_days - i}天前`);
            // 计算 T1~T5 最大值用于比例
            const kills = [p.t1, p.t2, p.t3, p.t4, p.t5].map(parseKMN);
            const maxKill = Math.max(...kills, 1);

            const killBars = kills.map((v, i) => {
                const percent = (v / maxKill) * 100;
                fv = formatKMN(v)
                return `
                    <div class="modal-row">
                        <span>T${i + 1}：${fv}</span>
                        <span>${percent.toFixed(0)}%</span>
                    </div>
                    <div class="bar-container">
                        <div class="bar" style="width:${percent}%;"></div>
                    </div>
                `;
            }).join("");

            // 计算 阵亡T1~T5 最大值用于比例
            const death = [
                p.dead_t1,
                p.dead_t2 || 0,
                p.dead_t3 || 0,
                p.dead_t4 || 0,
                p.dead_t5 || 0
            ].map(parseKMN);
            const maxDeath = Math.max(...death, 1);
            const deadBars = death.map((v, i) => {
                const percent1 = (v / maxDeath) * 100;
                fv = formatKMN(v)
                return `
                    <div class="modal-row">
                        <span>T${i + 1}：${fv}</span>
                        <span>${percent1.toFixed(0)}%</span>
                    </div>
                    <div class="bar-container">
                        <div class="bar" style="width:${percent1}%;"></div>
                    </div>
                `;
            }).join("");
            modalBody.innerHTML = `
                <div class="modal-row"><span>ID:${p.id}</span></div>
                <h2>${p.name}</h2>
                <h4>最近${kill_days}天每天获得的击杀积分(S Rank 10B in 60 days)</h4>
                <div id="chartBox">
                    <canvas id="killsChart"></canvas>
                </div>
                <h4>最近${collect_days}天每天的采集量(S Rank 25M per day)</h4>
                <div id="chartBox">
                    <canvas id="collectChart"></canvas>
                </div>
                <h4>最近${help_days}天每天的帮助次数(S Rank 100 per day)</h4>
                <div id="chartBox">
                    <canvas id="helpChart"></canvas>
                </div>`;

            // 等 DOM 插入后再画图
            setTimeout(() => {
                Chart.defaults.color = '#ffffff';
                const ctx_kill = document.getElementById('killsChart').getContext('2d');
                const ctx_collect = document.getElementById('collectChart').getContext('2d');
                const ctx_help = document.getElementById('helpChart').getContext('2d');
                if (killsChart) killsChart.destroy();
                if (collectChart) collectChart.destroy();
                if (helpChart) helpChart.destroy();
                killsChart = new Chart(ctx_kill, {
                    data: {
                        labels: kill_labels,
                        datasets: [{
                            type: 'bar',
                            label: 'kp per day',
                            data: kill_30,
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        },
                        {
                            type: 'line',
                            label: '累加击杀数',
                            data: cumulativeKills,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(141, 94, 6, 0.2)',
                            tension: 0.25,
                            pointRadius: 3
                        },
                        {
                            type: 'line',
                            label: '10B Line',
                            data: kill_30.map(() => 1_000_000_000), // 每个点都固定值
                            borderColor: 'red',
                            borderWidth: 1.5,
                            borderDash: [6, 6], // 虚线
                            pointRadius: 0,     // 不显示点
                            hitRadius: 0,       // 鼠标不触发
                            hoverRadius: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    callback: function (value) {
                                        if (value >= 1_000_000_000) return (value / 1_000_000_000) + 'B';
                                        if (value >= 1_000_000) return (value / 1_000_000) + 'M';
                                        if (value >= 1_000) return (value / 1_000) + 'K';
                                        return value;
                                    }
                                }
                            }
                        },
                        plugins: {
                            tooltip: {
                                callbacks: {
                                    label: function (context) {
                                        const value = context.parsed.y;
                                        if (value >= 1_000_000_000) return (value / 1_000_000_000).toFixed(1) + 'B';
                                        if (value >= 1_000_000) return (value / 1_000_000).toFixed(1) + 'M';
                                        if (value >= 1_000) return (value / 1_000).toFixed(1) + 'K';
                                        return value;
                                    }
                                }
                            },
                            legend: {
                                display: false   // 如果你也想隐藏图例
                            }
                        }
                    }
                });

                collectChart = new Chart(ctx_collect, {
                    type: 'line',
                    data: {
                        labels: collect_labels,
                        datasets: [{
                            label: 'collect per day',
                            data: collect_30,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            tension: 0.25,
                            pointRadius: 4
                        },
                        {
                            label: '30M Line',
                            data: collect_labels.map(() => 25_000_000), // 每个点都固定值
                            borderColor: 'red',
                            borderWidth: 1.5,
                            borderDash: [6, 6], // 虚线
                            pointRadius: 0,     // 不显示点
                            hitRadius: 0,       // 鼠标不触发
                            hoverRadius: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    callback: function (value) {
                                        if (value >= 1_000_000_000) return (value / 1_000_000_000) + 'B';
                                        if (value >= 1_000_000) return (value / 1_000_000) + 'M';
                                        if (value >= 1_000) return (value / 1_000) + 'K';
                                        return value;
                                    }
                                }
                            }
                        },
                        plugins: {
                            tooltip: {
                                callbacks: {
                                    label: function (context) {
                                        const value = context.parsed.y;
                                        if (value >= 1_000_000_000) return (value / 1_000_000_000).toFixed(1) + 'B';
                                        if (value >= 1_000_000) return (value / 1_000_000).toFixed(1) + 'M';
                                        if (value >= 1_000) return (value / 1_000).toFixed(1) + 'K';
                                        return value;
                                    }
                                }
                            },
                            legend: {
                                display: false   // 如果你也想隐藏图例
                            }
                        }
                    }
                });

                helpChart = new Chart(ctx_help, {
                    type: 'line',
                    data: {
                        labels: help_labels,
                        datasets: [{
                            label: 'help per day',
                            data: help_30,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            tension: 0.25,
                            pointRadius: 4
                        },
                        {
                            label: '60 Line',
                            data: help_labels.map(() => 100), // 每个点都固定值
                            borderColor: 'red',
                            borderWidth: 1.5,
                            borderDash: [6, 6], // 虚线
                            pointRadius: 0,     // 不显示点
                            hitRadius: 0,       // 鼠标不触发
                            hoverRadius: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    callback: function (value) {
                                        if (value >= 1_000_000_000) return (value / 1_000_000_000) + 'B';
                                        if (value >= 1_000_000) return (value / 1_000_000) + 'M';
                                        if (value >= 1_000) return (value / 1_000) + 'K';
                                        return value;
                                    }
                                }
                            }
                        },
                        plugins: {
                            tooltip: {
                                callbacks: {
                                    label: function (context) {
                                        const value = context.parsed.y;
                                        if (value >= 1_000_000_000) return (value / 1_000_000_000).toFixed(1) + 'B';
                                        if (value >= 1_000_000) return (value / 1_000_000).toFixed(1) + 'M';
                                        if (value >= 1_000) return (value / 1_000).toFixed(1) + 'K';
                                        return value;
                                    }
                                }
                            },
                            legend: {
                                display: false   // 如果你也想隐藏图例
                            }
                        }
                    }
                });
            }, 0);
            // 再 append 其他内容
            // modalBody.insertAdjacentHTML("beforeend", `
            //     <div class="modal-section">
            //         <h4>最近60天击杀单位数（T1 - T5）</h4>
            //         ${killBars}
            //     </div>

            //     <div class="modal-section">
            //         <h4>最近60天阵亡单位数（T1 - T5）</h4>
            //         ${deadBars}
            //     </div>
            // `);

            modal.style.display = "block";
        });
    });

    closeBtn.onclick = () => modal.style.display = "none";
    window.onclick = e => { if (e.target === modal) modal.style.display = "none"; };
});