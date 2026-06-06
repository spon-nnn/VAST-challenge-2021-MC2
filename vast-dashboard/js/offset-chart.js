// ============================================================
// offset-chart.js — CC-Loyalty 价格偏移证据图
// 展示 $20/$60/$80 系统性偏移
// ============================================================

document.addEventListener('DOMContentLoaded', function () {
    d3.json("data/cc_loyalty_offset.json").then(function (data) {
        drawOffsetChart(data);
    });
});

function drawOffsetChart(data) {
    var margin = { top: 40, right: 30, bottom: 60, left: 60 };
    var width = 520 - margin.left - margin.right;
    var height = 380 - margin.top - margin.bottom;

    var svg = d3.select("#offset_svg")
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // 标题
    svg.append("text")
        .attr("x", width / 2).attr("y", -15)
        .attr("text-anchor", "middle")
        .style("font-size", "13px").style("font-weight", "600").style("fill", "#1e293b")
        .text("CC vs Loyalty Price Differences");

    // 总览文字
    svg.append("text")
        .attr("x", 0).attr("y", 8)
        .style("font-size", "11px").style("fill", "#64748b")
        .text(data.total_matches + " total CC-Loyalty matched pairs | " +
              data.perfect_matches + " exact matches (" +
              (data.perfect_matches / data.total_matches * 100).toFixed(1) + "%) | " +
              data.offset_matches + " with systematic offset");

    // 柱状图
    var categories = data.offset_categories;
    var x = d3.scaleBand().range([0, width]).domain(categories.map(d => d.category)).padding(0.3);
    var y = d3.scaleLinear().range([height, 30]).domain([0, d3.max(categories, d => d.count) * 1.15]);

    svg.append("g")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(x))
        .selectAll("text")
        .style("font-size", "10px").style("fill", "#475569");

    svg.append("g").call(d3.axisLeft(y).ticks(5));

    // 柱
    var bars = svg.selectAll(".offset-bar")
        .data(categories)
        .enter()
        .append("rect")
        .attr("class", "offset-bar")
        .attr("x", d => x(d.category))
        .attr("y", d => y(d.count))
        .attr("width", x.bandwidth())
        .attr("height", d => height - y(d.count))
        .attr("rx", 4)
        .style("fill", function (d, i) { return ["#dc2626", "#f59e0b", "#ea580c", "#94a3b8"][i]; })
        .style("opacity", 0.85);

    // 数值标签
    svg.selectAll(".offset-label")
        .data(categories)
        .enter()
        .append("text")
        .attr("x", d => x(d.category) + x.bandwidth() / 2)
        .attr("y", d => y(d.count) - 6)
        .attr("text-anchor", "middle")
        .style("font-size", "12px").style("font-weight", "700").style("fill", "#1e293b")
        .text(d => d.count + " pairs");

    // Tooltip
    var tooltip = d3.select("#offset_svg").append("div")
        .style("opacity", 0).attr("class", "tooltip")
        .style("background", "white").style("color", "#1e293b")
        .style("border", "1px solid #cbd5e1").style("border-radius", "6px")
        .style("padding", "6px 10px").style("position", "absolute")
        .style("pointer-events", "none").style("font-size", "11px").style("z-index", "1000");

    bars.on("mouseover", function (event, d) {
        tooltip.style("opacity", 1);
        var html = "<b>" + d.category + "</b><br>" + d.count + " pairs";
        if (d.examples && d.examples.length > 0) {
            html += "<br><br>Examples:";
            d.examples.forEach(function (ex) {
                html += "<br>" + ex.date + " @ " + ex.location +
                    "<br>  CC: $" + ex.cc_price.toFixed(2) +
                    " | Loyalty: $" + ex.loyalty_price.toFixed(2) +
                    " | Δ=$" + ex.diff.toFixed(2);
            });
        }
        tooltip.html(html)
            .style("left", event.pageX + 16 + "px").style("top", event.pageY - 10 + "px");
        d3.select(this).style("opacity", 1);
    }).on("mouseout", function () {
        tooltip.style("opacity", 0);
        d3.select(this).style("opacity", 0.85);
    }).on("mousemove", function (event) {
        tooltip.style("left", event.pageX + 16 + "px").style("top", event.pageY - 10 + "px");
    });
}
