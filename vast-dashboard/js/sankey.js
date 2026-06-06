// ============================================================
// sankey.js — 桑基图（还原参考方案）
// 全数据、大高度、无过滤
// ============================================================

document.addEventListener('DOMContentLoaded', function () {
    var margin = { top: 10, right: 20, bottom: 10, left: 10 };
    var width = 260 - margin.left - margin.right;
    var height = 2500 - margin.top - margin.bottom;

    var formatNumber = d3.format(",.0f");
    var color = d3.scaleOrdinal(d3.schemeSet3);

    var svg = d3.select("#sankey_svg")
        .attr("viewBox", "0 0 280 2500")
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var sankey = d3.sankey()
        .nodeWidth(10)
        .nodePadding(8)
        .size([width, height])
        .nodeAlign(d3.sankeyRight);

    d3.json("data/sankey.json").then(function (data) {
        var graph = sankey(data);

        // 链接
        var link = svg.append("g").selectAll(".link")
            .data(graph.links)
            .enter().append("path")
            .attr("class", "link")
            .attr("d", d3.sankeyLinkHorizontal())
            .attr("stroke-width", function (d) { return Math.max(1, d.width); })
            .style("opacity", 0.75)
            .style("stroke", function (d) {
                var srcNode = graph.nodes[d.source.index !== undefined ? d.source.index : d.source];
                if (srcNode && srcNode.spending_pattern === "Corporate") return "#ea580c";
                return d.source.name && d.source.name.startsWith("car_") ? "#66c2a5" :
                       d.source.name && d.source.name.startsWith("CC_") ? "#fc8d62" : "#8da0cb";
            });

        link.append("title")
            .text(function (d) {
                return d.source.name + " → " + d.target.name + "\n" + d.value;
            });

        // 节点
        var node = svg.append("g").selectAll(".node")
            .data(graph.nodes)
            .enter().append("g")
            .attr("class", "node");

        node.append("rect")
            .attr("x", function (d) { return d.x0; })
            .attr("y", function (d) { return d.y0; })
            .attr("height", function (d) { return Math.max(1, d.y1 - d.y0); })
            .attr("width", sankey.nodeWidth())
            .style("fill", function (d) {
                if (d.spending_pattern === "Corporate") return "#ea580c";
                if (d.name && d.name.startsWith("car_")) return "#66c2a5";
                if (d.name && d.name.startsWith("CC_")) return "#fc8d62";
                return "#8da0cb";
            })
            .style("opacity", 0.85)
            .append("title")
            .text(function (d) {
                var txt = d.name;
                if (d.spending_pattern) txt += "\n" + d.spending_pattern;
                if (d.primary_employee) txt += "\n" + d.primary_employee;
                return txt;
            });

        // 节点标签
        node.append("text")
            .attr("x", function (d) { return d.x0 - 6; })
            .attr("y", function (d) { return (d.y1 + d.y0) / 2; })
            .attr("dy", "0.35em")
            .attr("text-anchor", "end")
            .text(function (d) { return d.name; })
            .filter(function (d) { return d.x0 < width / 2; })
            .attr("x", function (d) { return d.x1 + 6; })
            .attr("text-anchor", "start")
            .style("font-size", "9px").style("fill", "#475569");

        // 悬停
        node.on("mouseover", function (d) {
            link.style("opacity", 0.1);
            d3.selectAll('.link').data(graph.links).style("opacity", function (l) {
                return (l.source.name === d.name || l.target.name === d.name) ? 1 : 0.1;
            });
        }).on("mouseleave", function () {
            link.style("opacity", 0.75);
        });

        link.on("mouseover", function () {
            link.style("opacity", 0.1);
            d3.select(this).style("opacity", 1);
        }).on("mouseleave", function () {
            link.style("opacity", 0.75);
        });
    });
});
