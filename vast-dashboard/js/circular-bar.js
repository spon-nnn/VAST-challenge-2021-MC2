// ============================================================
// circular-bar.js v2 — 环形柱状图
// 外环 CC + 内环 Loyalty + Q5 可疑地点星标
// ============================================================

const cc_color = "#3b82f6";
const loyal_color = "#f59e0b";

var circularBarClicked = null;
var circularBarData;

document.addEventListener('DOMContentLoaded', function () {
    d3.json("data/circular_bar.json").then(function (values) {
        circularBarData = values;
        drawCircularBarPlot();
    });
});

function drawCircularBarPlot() {
    const innerRadius = 100;
    const outerRadius = 230;
    const svgEl = d3.select("#circular_bar_svg");
    const bbox = svgEl.node().getBoundingClientRect();
    const W = bbox.width || 560;
    const cx = W / 2 + 20, cy = 300;

    var svg = svgEl.append("g").attr("transform", "translate(" + cx + "," + cy + ")");

    // 图例
    svg.append("rect").attr("x", -cx + 30).attr("y", -cy + 10)
        .attr("width", 14).attr("height", 14).attr("fill", cc_color).attr("rx", 2);
    svg.append("text").text("Credit Card transactions").attr("x", -cx + 50).attr("y", -cy + 21)
        .style("font-size", "12px").style("fill", "#475569");

    svg.append("rect").attr("x", -cx + 30).attr("y", -cy + 32)
        .attr("width", 14).attr("height", 14).attr("fill", loyal_color).attr("rx", 2);
    svg.append("text").text("Loyalty Card transactions").attr("x", -cx + 50).attr("y", -cy + 43)
        .style("font-size", "12px").style("fill", "#475569");

    svg.append("text").text("★ Suspicious location (Q5)")
        .attr("x", -cx + 30).attr("y", -cy + 68)
        .style("font-size", "11px").style("fill", "#dc2626");

    const x = d3.scaleBand().range([0, 2 * Math.PI]).align(0)
        .domain(circularBarData.map(d => d.location));
    const yCC = d3.scaleRadial().range([innerRadius, outerRadius]).domain([2, 220]);
    const yLoy = d3.scaleRadial().range([innerRadius, 3]).domain([1, 220]);

    // Tooltip
    var tooltip = d3.select("#left-circular-div, .chart-half")
        .append("div")
        .style("opacity", 0).attr("class", "tooltip")
        .style("background", "white").style("color", "#1e293b")
        .style("border", "1px solid #cbd5e1").style("border-radius", "6px")
        .style("padding", "6px 10px").style("position", "absolute")
        .style("pointer-events", "none").style("font-size", "12px").style("z-index", "1000");

    // 外环 CC
    svg.selectAll(".cc_bars")
        .data(circularBarData)
        .join("path")
        .attr("fill", cc_color).attr("class", "cc_bars")
        .attr("id", d => "bar_" + location_index[d.location])
        .style("opacity", 0.75).style("stroke", "white").style("stroke-width", 1)
        .attr("d", d3.arc()
            .innerRadius(innerRadius).outerRadius(d => yCC(d.cc_count))
            .startAngle(d => x(d.location)).endAngle(d => x(d.location) + x.bandwidth())
            .padAngle(0.01).padRadius(innerRadius))
        .on("mouseover", function (_, d) { tooltip.style("opacity", 1); })
        .on("mouseout", function () { tooltip.html("").style("opacity", 0); })
        .on("mousemove", function (event, d) {
            tooltip.html("<b>" + d.location + "</b><br>CC: " + d.cc_count +
                " | Loyalty: " + d.loyalty_count +
                (d.suspicious_score > 0 ? "<br><span style='color:#dc2626'>⚠ Suspicious score: " + d.suspicious_score + "</span>" : ""))
                .style("left", event.pageX + 16 + "px").style("top", event.pageY - 10 + "px");
        })
        .on("click", circularBarInteraction);

    // 可疑地点星标
    svg.selectAll(".suspicious_stars")
        .data(circularBarData.filter(function (d) { return d.suspicious_score > 0; }))
        .join("text")
        .attr("class", "suspicious_stars")
        .attr("x", d => (yCC(d.cc_count) + 8) * Math.cos(x(d.location) + x.bandwidth() / 2 - Math.PI / 2))
        .attr("y", d => (yCC(d.cc_count) + 8) * Math.sin(x(d.location) + x.bandwidth() / 2 - Math.PI / 2))
        .attr("text-anchor", "middle").attr("dominant-baseline", "central")
        .text("★").style("fill", "#dc2626").style("font-size", "14px")
        .append("title").text(d => "Q5 Suspicious: " + d.suspicious_score);

    // 地点标签
    svg.selectAll(".cb_labels")
        .data(circularBarData)
        .join("g")
        .attr("text-anchor", d => (x(d.location) + x.bandwidth() / 2 + Math.PI) % (2 * Math.PI) < Math.PI ? "end" : "start")
        .attr("transform", d => "rotate(" + ((x(d.location) + x.bandwidth() / 2) * 180 / Math.PI - 90) + ")translate(" + (yCC(d.cc_count) + 18) + ",0)")
        .append("text")
        .text(d => d.location)
        .attr("transform", d => (x(d.location) + x.bandwidth() / 2 + Math.PI) % (2 * Math.PI) < Math.PI ? "rotate(180)" : "rotate(0)")
        .style("font-size", "10px").style("fill", "#475569")
        .attr("alignment-baseline", "middle");

    // 内环 Loyalty
    svg.selectAll(".lc_bars")
        .data(circularBarData)
        .join("path")
        .attr("fill", loyal_color).attr("class", "lc_bars")
        .attr("id", d => "bar_u" + location_index[d.location])
        .style("opacity", 0.75).style("stroke", "white").style("stroke-width", 1)
        .attr("d", d3.arc()
            .innerRadius(d => yLoy(0)).outerRadius(d => yLoy(d.loyalty_count))
            .startAngle(d => x(d.location)).endAngle(d => x(d.location) + x.bandwidth())
            .padAngle(0.01).padRadius(innerRadius))
        .on("mouseover", function (_, d) { tooltip.style("opacity", 1); })
        .on("mouseout", function () { tooltip.html("").style("opacity", 0); })
        .on("mousemove", function (event, d) {
            tooltip.html("<b>" + d.location + "</b><br>Loyalty: " + d.loyalty_count)
                .style("left", event.pageX + 16 + "px").style("top", event.pageY - 10 + "px");
        });
}

function circularBarInteraction(event, d) {
    if (circularBarClicked == null) {
        d3.selectAll('.cc_bars').style('stroke-width', 1).style('stroke', 'white');
        d3.select("#" + event.target.id).style("stroke-width", 3).style("stroke", "#dc2626");
        d3.selectAll(".box_circles").style("opacity", 0.08);
        if (location_index[d.location]) {
            d3.selectAll('#box_' + location_index[d.location]).style("opacity", 1);
        }
        circularBarClicked = event.target.id;
        var seldrop = document.querySelector("#dropdownloc");
        if (seldrop) { seldrop.value = d.location; seldrop.dispatchEvent(new Event('change')); }
        eventBus.emit('locationSelected', d.location);
    } else {
        d3.selectAll('.cc_bars').style('stroke-width', 1).style('stroke', 'white');
        d3.selectAll(".box_circles").style("opacity", 0.08);
        if (circularBarClicked !== event.target.id) {
            d3.select("#" + circularBarClicked).style("stroke-width", 1).style("stroke", "white");
            d3.select("#" + event.target.id).style("stroke-width", 3).style("stroke", "#dc2626");
            if (location_index[d.location]) {
                d3.selectAll('#box_' + location_index[d.location]).style("opacity", 1);
            }
            circularBarClicked = event.target.id;
            var s = document.querySelector("#dropdownloc");
            if (s) { s.value = d.location; s.dispatchEvent(new Event('change')); }
            eventBus.emit('locationSelected', d.location);
        } else {
            d3.selectAll(".box_circles").style("opacity", 1);
            circularBarClicked = null;
            var s2 = document.querySelector("#dropdownloc");
            if (s2) { s2.value = "1"; s2.dispatchEvent(new Event('change')); }
            eventBus.emit('locationDeselected', null);
        }
    }
}
