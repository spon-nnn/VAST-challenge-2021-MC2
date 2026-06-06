// ============================================================
// ring-chart.js v2 — 环形时间图
// + 异常交易高亮 (大半径/菱形)、异常筛选按钮、新配色
// ============================================================

var ringdata, ringsvg, filtereddata, ringwidth, ringheight, inwidth, inringheight;
var maxRadius, minRadius, parseTime, parsedate;
var dateToRadius, timeScale, uniquedates;
var selected_location_ring = "1", selected_cc_ring = "1";
var showAnomalyOnly = false;
var days, timelabel, time;

document.addEventListener('DOMContentLoaded', function () {
    d3.json("data/ring_chart.json").then(function (values) {
        ringdata = values;
        // 获取父容器实际尺寸确保居中
        var parent = document.getElementById("ring_svg").parentNode;
        ringwidth = parent.clientWidth || 650;
        ringheight = Math.max(520, ringwidth * 0.88);
        ringsvg = d3.select("#ring_svg");
        inwidth = ringwidth - 20;
        inringheight = ringheight - 20;
        uniquedates = new Set(ringdata.map(function (d) { return d.date; }));
        calend();
        legendsAndDropdowns();
        UpdateChart();
    });
});

function legendsAndDropdowns() {
    var locSelect = document.getElementById("dropdownloc");
    var locs = Array.from(new Set(ringdata.map(d => d.location))).sort();
    locs.forEach(function (d) {
        var o = document.createElement("option"); o.text = d; o.value = d; locSelect.add(o);
    });
    var ccSelect = document.getElementById("dropdowncc");
    var ccs = Array.from(new Set(ringdata.map(d => d.last4ccnum))).sort();
    ccs.forEach(function (d) {
        var o = document.createElement("option"); o.text = d; o.value = d; ccSelect.add(o);
    });
    document.getElementById('dropdownloc').addEventListener('change', UpdateChart);
    document.getElementById('dropdowncc').addEventListener('change', UpdateChart);

    // 异常筛选按钮
    var anomalyBtn = document.getElementById('anomaly-filter-btn');
    if (anomalyBtn) {
        anomalyBtn.addEventListener('click', function () {
            showAnomalyOnly = !showAnomalyOnly;
            this.textContent = showAnomalyOnly ? '✓ 仅异常' : '仅异常交易';
            this.className = showAnomalyOnly ? 'btn-danger' : 'outline';
            UpdateChart();
        });
    }

    // 图例
    var legendr = ringsvg.append("g").attr("class", "legend").attr("transform", "translate(580,10)");
    legendr.append("text").attr("x", -50).attr("y", 0)
        .attr("text-anchor", "middle").attr("fill", "#475569")
        .style("font-weight", "600").style("font-size", "11px").text("Categories");

    var clickedty = null;
    var items = Object.keys(colorMap);
    var rectty = legendr.selectAll("legrect").data(items).enter()
        .append("rect").attr("x", -90).attr("y", (d, i) => i * 20 + 8)
        .attr("width", 12).attr("height", 12).attr("rx", 2)
        .style("fill", d => colorMap[d]).style("stroke", "#cbd5e1").style("cursor", "pointer")
        .on("click", function (d, i) {
            if (clickedty === i) {
                rectty.style("stroke", "#cbd5e1");
                d3.selectAll(".transactions").style("visibility", "visible").style("stroke", "none");
                clickedty = null;
            } else {
                rectty.style("stroke", "#cbd5e1");
                d3.select(this).style("stroke", "#1e293b");
                clickedty = i;
                categoryFilter("ty" + i);
            }
        });
    legendr.selectAll(".legtext").data(items).enter()
        .append("text").attr("x", -74).attr("y", (d, i) => i * 20 + 18)
        .text(d => d).style("font-size", "10px").style("fill", "#475569");
}

function calend() {
    var cal = ringsvg.append("g").attr("width", 120).attr("height", 120);
    var clickedcal = null, gridSize = 20, padding = 4;
    var datesArr = Array.from(uniquedates).sort();
    datesArr.unshift("ALL");

    cal.append("text").attr("x", 45).attr("y", 130)
        .attr("text-anchor", "middle").style("fill", "#10b981")
        .style("font-size", "12px").style("font-weight", "600").text("Calendar");

    var squares = cal.selectAll(".square").data(datesArr).join("rect")
        .attr("class", "square")
        .attr("x", (d, i) => i % 4 * (gridSize + padding) + 5)
        .attr("y", (d, i) => Math.floor(i / 4) * (gridSize + padding) + 5)
        .attr("width", gridSize).attr("height", gridSize).attr("rx", 3)
        .style("fill", d => d === "ALL" ? "#fee2e2" : "#dcfce7")
        .style("stroke", "#cbd5e1").style("cursor", "pointer")
        .on("click", function (d, i) {
            if (clickedcal === i) {
                squares.style("stroke", "#cbd5e1");
                d3.selectAll(".transactions").style("visibility", "visible").style("stroke", "none");
                clickedcal = null;
            } else {
                squares.style("stroke", "#cbd5e1");
                d3.select(this).style("stroke", "#dc2626");
                clickedcal = i;
                categoryFilter("d" + i);
            }
        });

    cal.selectAll(".label").data(datesArr).join("text")
        .attr("class", "label").style("pointer-events", "none")
        .attr("x", (d, i) => i % 4 * (gridSize + padding) + gridSize / 2 + 5)
        .attr("y", (d, i) => Math.floor(i / 4) * (gridSize + padding) + gridSize / 2 + 10)
        .text(d => d === "ALL" ? "ALL" : d.slice(5).replace("-", "/"))
        .style("text-anchor", "middle").style("font-size", "9px").style("fill", "#475569");
}

function categoryFilter(id) {
    ringsvg.selectAll(".transactions").style("visibility", "hidden");
    if (id === "d0") {
        ringsvg.selectAll(".transactions").style("visibility", "visible").style("stroke", "none");
    } else {
        d3.selectAll('[id*="' + id + '"]').style("visibility", "visible").style("stroke", "#cbd5e1");
    }
}

function UpdateData() {
    d3.selectAll(".box_circles").style("opacity", 0.08);
    if (selected_location_ring === "1") {
        d3.selectAll(".box_circles").style("opacity", 1);
        d3.selectAll('.cc_bars').style('stroke-width', 1).style('stroke', 'white');
    } else {
        if (location_index[selected_location_ring]) {
            d3.selectAll('#box_' + location_index[selected_location_ring]).style("opacity", 1);
        }
        d3.selectAll('.cc_bars').style('stroke-width', 1).style('stroke', 'white');
        var barId = "bar_" + location_index[selected_location_ring];
        d3.select("#" + barId).style("stroke-width", 3).style("stroke", "#dc2626");
    }
    var allcc = (selected_cc_ring === '1');
    var alloc = (selected_location_ring === '1');

    filtereddata = ringdata.filter(function (d) {
        var match = ((d.last4ccnum === selected_cc_ring) || allcc) &&
            ((d.location === selected_location_ring) || alloc);
        if (showAnomalyOnly) match = match && d.is_anomaly;
        return match;
    });
}

function UpdateChart() {
    selected_location_ring = document.getElementById("dropdownloc").value;
    selected_cc_ring = document.getElementById("dropdowncc").value;
    UpdateData();
    if (days) days.remove();
    if (timelabel) timelabel.remove();
    if (time) time.remove();
    DrawChart();
}

function timetoangle(time) {
    return (timeScale(parseTime(time)) * Math.PI) / 180;
}

function DrawChart() {
    parsedate = d3.timeParse("%Y-%m-%d");
    parseTime = d3.timeParse("%H:%M:%S");
    maxRadius = (Math.min(inwidth, inringheight)) / 2 - 35;
    minRadius = 40;

    var tooltipring = d3.select("#right-ring-div, .chart-half").append("div")
        .style("opacity", 0).attr("class", "tooltip")
        .style("background", "white").style("color", "#1e293b")
        .style("border", "1px solid #cbd5e1").style("border-radius", "6px")
        .style("padding", "6px 10px").style("position", "absolute")
        .style("pointer-events", "none").style("font-size", "12px").style("z-index", "1000");

    dateToRadius = d3.scaleTime()
        .domain(d3.extent(ringdata, d => parsedate(d.date)))
        .range([minRadius, maxRadius]);
    timeScale = d3.scaleLinear()
        .domain([parseTime("00:00:00"), parseTime("23:59:59")])
        .range([360, 0]);

    var centerX = inwidth / 2, centerY = inringheight / 2;

    // 日期圈
    days = ringsvg.selectAll(".days")
        .data(Array.from(uniquedates))
        .join("circle")
        .attr("cx", centerX).attr("cy", centerY)
        .attr("r", d => dateToRadius(parsedate(d)))
        .style("fill", "none").style("stroke", "#cbd5e1")
        .style("stroke-width", 1).style("opacity", 0.4);

    // 日期标签
    ringsvg.selectAll(".day-label")
        .data(Array.from(uniquedates))
        .join("text")
        .attr("text-anchor", "middle")
        .attr("x", centerX)
        .attr("y", d => centerY - dateToRadius(parsedate(d)) + 10)
        .text(d => d.slice(5).replace("-", "/"))
        .style("font-size", "8px").style("fill", "#94a3b8");

    // 十字参考线
    ringsvg.selectAll('.ref-line')
        .data([0, 1])
        .join('line')
        .attr('x1', d => centerX + Math.cos(d * Math.PI / 2) * maxRadius)
        .attr('y1', d => centerY + Math.sin(d * Math.PI / 2) * maxRadius)
        .attr('x2', d => centerX + Math.cos(d * Math.PI / 2 + Math.PI) * maxRadius)
        .attr('y2', d => centerY + Math.sin(d * Math.PI / 2 + Math.PI) * maxRadius)
        .attr('stroke', '#e2e8f0').style('stroke-dasharray', '8,8');

    // 时间标签
    var tlAngles = d3.range(360, 0, -45).map(function (x) { return x * Math.PI / 180; });
    timelabel = ringsvg.selectAll(".time-label").data(tlAngles).join("text")
        .attr("text-anchor", "middle")
        .attr("x", d => centerX + (maxRadius + 12) * Math.cos(d))
        .attr("y", d => centerY + (maxRadius + 12) * Math.sin(d) + 4)
        .text((d, i) => i * 3 + "h")
        .style("font-size", "9px").style("fill", "#94a3b8");

    // 形状生成器（异常点用菱形/更大）
    var shapePath = function (d, r) {
        if (d.is_anomaly && d.spending_pattern === "Corporate") {
            // 菱形
            var size = r * 2;
            return "M0," + (-size) + " L" + size + ",0 L0," + size + " L" + (-size) + ",0 Z";
        }
        return null; // 默认圆形
    };

    // 交易点
    time = ringsvg.selectAll(".transactions")
        .data(filtereddata)
        .join("circle")
        .attr("class", "transactions")
        .attr("cx", d => centerX + dateToRadius(parsedate(d.date)) * Math.cos(timetoangle(d.time)))
        .attr("cy", d => centerY + dateToRadius(parsedate(d.date)) * Math.sin(timetoangle(d.time)))
        .attr("r", function (d) {
            if (d.is_extreme_price) return 8;
            if (d.is_high_price) return 5.5;
            if (d.is_anomaly) return 5;
            return 3.5;
        })
        .attr("id", d => "c" + d.last4ccnum + "_d" + d.date + "_ty" + colorMap[loctype[d.location]])
        .attr("fill", function (d) {
            if (d.spending_pattern === "Corporate") return "#ea580c";
            return colorMap[loctype[d.location]] || "#94a3b8";
        })
        .attr("stroke", function (d) {
            if (d.is_early_morning) return "#dc2626";
            if (d.is_anomaly) return "#f59e0b";
            return "none";
        })
        .attr("stroke-width", function (d) {
            if (d.is_early_morning) return 2;
            if (d.is_anomaly) return 1;
            return 0;
        })
        .style("opacity", function (d) { return d.is_anomaly ? 1 : 0.75; })
        .style("cursor", "pointer")
        .on("mouseover", function (_, d) {
            tooltipring.style("opacity", 1);
            time.style("opacity", 0.2);
            d3.select(this).style("opacity", 1);
        })
        .on("mouseout", function () {
            time.style("opacity", function (d) { return d.is_anomaly ? 1 : 0.75; });
            tooltipring.html("").style("opacity", 0);
        })
        .on("mousemove", function (event, d) {
            var html = "<b>" + d.location + "</b><br>$" + d.price.toFixed(2) +
                " | CC:" + d.last4ccnum + "<br>" + d.date + " " + d.time;
            if (d.spending_pattern === "Corporate") html += "<br><span style='color:#ea580c'>Corporate card</span>";
            if (d.is_anomaly) html += "<br><span style='color:#dc2626'>⚠ " + d.anomaly_reason + "</span>";
            tooltipring.html(html)
                .style("left", event.pageX + 16 + "px").style("top", event.pageY - 10 + "px");
        });
}
