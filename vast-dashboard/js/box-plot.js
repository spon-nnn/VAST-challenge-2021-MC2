// ============================================================
// box-plot.js v2 — 箱线图
// 可疑地点高亮 + 异常交易红色标注 + y轴线性（筛选$2000以内）
// ============================================================

var boxData;
var margin_box = { top: 40, right: 30, bottom: 140, left: 70 };
var width_box = 1100 - margin_box.left - margin_box.right;
var height_box = 560 - margin_box.top - margin_box.bottom;

document.addEventListener('DOMContentLoaded', function () {
    d3.json("data/box_plot.json").then(function (values) {
        boxData = values;
        drawBoxPlot();
    });
});

function drawBoxPlot() {
    var svg = d3.select("#box_plot_svg")
        .append("g")
        .attr("transform", "translate(" + margin_box.left + "," + margin_box.top + ")");

    // 按地点计算统计量
    var sumstat = d3.rollup(boxData,
        function (d) {
            var prices = d.map(function (g) { return g.price; }).sort(d3.ascending);
            return {
                q1: d3.quantile(prices, 0.25), median: d3.quantile(prices, 0.5),
                q3: d3.quantile(prices, 0.75), min: d3.quantile(prices, 0),
                max: d3.quantile(prices, 1), count: prices.length,
                suspicious_score: d[0].suspicious_score || 0,
            };
        },
        function (d) { return d.location; }
    );

    // X 轴
    var x = d3.scaleBand().range([0, width_box]).domain(location_list)
        .paddingInner(1).paddingOuter(0.5);

    svg.append("g")
        .attr("transform", "translate(0," + height_box + ")")
        .call(d3.axisBottom(x))
        .selectAll("text")
        .attr("transform", "translate(-10,0)rotate(-45)")
        .style("text-anchor", "end").style("font-size", "10px").style("fill", "#475569");

    // Y 轴（筛选到 $2000 以内，使大部分数据可见）
    var yMax = 2000;
    var y = d3.scaleLinear().domain([0, yMax]).range([height_box, 0]);

    svg.append("g").call(d3.axisLeft(y).tickFormat(d => "$" + d));
    svg.append("text").attr("class", "ylabel").attr("transform", "rotate(-90)")
        .attr("y", -margin_box.left - 50).attr("x", -height_box / 2)
        .attr("dy", "0.3em").style("text-anchor", "middle")
        .text("Price (USD, capped at $2,000)").style("font-size", "12px").style("fill", "#64748b");

    var boxWidth = 24;

    // 垂直线
    svg.selectAll("vertLines").data(sumstat).enter()
        .append("line")
        .attr("x1", d => x(d[0])).attr("x2", d => x(d[0]))
        .attr("y1", d => y(Math.min(d[1].min, yMax))).attr("y2", d => y(Math.min(d[1].max, yMax)))
        .attr("stroke", d => d[1].suspicious_score > 0 ? "#dc2626" : "#94a3b8")
        .style("stroke-width", d => d[1].suspicious_score > 0 ? 2 : 1);

    // 箱体
    svg.selectAll("boxes").data(sumstat).enter()
        .append("rect")
        .attr("x", d => x(d[0]) - boxWidth / 2)
        .attr("y", d => y(Math.min(d[1].q3, yMax)))
        .attr("height", d => Math.max(1, y(d[1].q1) - y(Math.min(d[1].q3, yMax))))
        .attr("width", boxWidth)
        .attr("stroke", d => d[1].suspicious_score > 10 ? "#dc2626" : "#475569")
        .attr("stroke-width", d => d[1].suspicious_score > 10 ? 2 : 1)
        .attr("rx", 2)
        .style("fill", function (d) {
            if (d[1].suspicious_score > 50) return "#fecaca";
            if (d[1].suspicious_score > 10) return "#fee2e2";
            return "#e0f2fe";
        });

    // 中位线
    svg.selectAll("medianLines").data(sumstat).enter()
        .append("line")
        .attr("x1", d => x(d[0]) - boxWidth / 2).attr("x2", d => x(d[0]) + boxWidth / 2)
        .attr("y1", d => y(Math.min(d[1].median, yMax)))
        .attr("y2", d => y(Math.min(d[1].median, yMax)))
        .attr("stroke", "#1e293b").attr("stroke-width", 2);

    // Tooltip
    var tooltip = d3.select("#box_plot_div").append("div")
        .style("opacity", 0).attr("class", "tooltip")
        .style("background", "white").style("color", "#1e293b")
        .style("border", "1px solid #cbd5e1").style("border-radius", "6px")
        .style("padding", "6px 10px").style("position", "absolute")
        .style("pointer-events", "none").style("font-size", "12px").style("z-index", "1000");

    // 抖动散点
    var jitterW = 18;
    svg.selectAll("indPoints").data(boxData).enter()
        .append("circle")
        .attr("id", d => "box_" + location_index[d.location])
        .attr("class", "box_circles")
        .attr("cx", d => x(d.location) - jitterW / 2 + Math.random() * jitterW)
        .attr("cy", d => y(Math.min(d.price, yMax)))
        .attr("r", function (d) {
            if (d.is_high_price) return 4.5;
            return 2.5;
        })
        .style("fill", function (d) {
            if (d.is_high_price) return "#dc2626";
            if (d.is_anomaly) return "#f59e0b";
            return "#94a3b8";
        })
        .style("opacity", function (d) { return d.is_anomaly ? 0.9 : 0.4; })
        .attr("stroke", function (d) { return d.is_anomaly ? "#1e293b" : "none"; })
        .attr("stroke-width", function (d) { return d.is_anomaly ? 1 : 0; })
        .on("mouseover", function () {
            tooltip.style("opacity", 1);
            d3.select(this).style("opacity", 1).attr("r", 6);
        })
        .on("mouseout", function () {
            tooltip.html("").style("opacity", 0);
            var me = d3.select(this);
            var d = me.datum();
            me.style("opacity", d.is_anomaly ? 0.9 : 0.4)
                .attr("r", d.is_high_price ? 4.5 : 2.5);
        })
        .on("mousemove", function (event, d) {
            var html = "<b>" + d.location + "</b><br>$" + d.price.toFixed(2) +
                " | CC:" + d.last4ccnum + "<br>" + d.timestamp;
            if (d.is_anomaly) html += "<br><span style='color:#dc2626'>⚠ Anomaly</span>";
            if (d.suspicious_score > 0) html += "<br><span style='color:#f59e0b'>Q5 Score: " + d.suspicious_score + "</span>";
            tooltip.html(html)
                .style("left", event.pageX + 16 + "px").style("top", event.pageY - 10 + "px");
        });

    // y=$2000+ 标注
    svg.append("text")
        .attr("x", width_box - 5).attr("y", 10)
        .attr("text-anchor", "end")
        .style("font-size", "9px").style("fill", "#94a3b8")
        .text("(Values > $2,000 clipped; max=$10,000)");
}
