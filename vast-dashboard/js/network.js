// ============================================================
// network.js — 力导向网络图 v2
// 修复：margin 调整、tooltip、夜间边着色、关键人物高亮
// ============================================================

var netNode, netLink, netData, netSvg, netSimulation;
var NodeNameToNodeIdMapping = {};
var networkWidth, networkHeight;

document.addEventListener('DOMContentLoaded', function () {
    d3.json("data/network.json").then(function (values) {
        netData = values;
        drawNetworkPlot(values);
    });
});

function drawNetworkPlot(netData) {
    // 构建节点查找
    NodeNameToNodeIdMapping = {};
    netData.nodes.forEach(function (n) { NodeNameToNodeIdMapping[n.name] = n.id; });

    var margin = { top: 30, right: 180, bottom: 30, left: 30 };
    networkWidth = 960 - margin.left - margin.right;
    networkHeight = 550 - margin.top - margin.bottom;

    netSvg = d3.select('#network_svg')
        .attr("viewBox", "0 0 960 550")
        .append('g')
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Tooltip
    var tooltip = d3.select("#network_div")
        .append("div")
        .style("opacity", 0)
        .attr("class", "tooltip")
        .style("background-color", "white")
        .style("color", "#1e293b")
        .style("border", "1px solid #cbd5e1")
        .style("border-radius", "6px")
        .style("padding", "8px 12px")
        .style("position", "absolute")
        .style("pointer-events", "none")
        .style("font-size", "13px")
        .style("z-index", "1000")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.12)");

    var image_ref = {
        0: "assets/icons/circle-15.svg",
        1: "assets/icons/square-15.svg",
        2: "assets/icons/triangle.svg",
        3: "assets/icons/Star.svg",
        4: "assets/icons/hexagon.svg",
        5: "assets/icons/penta.svg"
    };

    // 边（区分夜间/非工作时段）
    netLink = netSvg.selectAll("line")
        .data(netData.links)
        .enter()
        .append("line")
        .attr('class', 'network_chart_links')
        .attr("id", d => "l" + d.source.id + "_" + d.target.id)
        .style("stroke", function (d) {
            if (d.is_night) return "#dc2626";
            if (d.after_hours) return "#f59e0b";
            return "#cbd5e1";
        })
        .style("stroke-width", function (d) {
            return d.is_night ? 2.5 : d.after_hours ? 1.8 : 1;
        })
        .style("stroke-dasharray", function (d) {
            return d.is_night ? "5,3" : d.after_hours ? "3,3" : "none";
        })
        .style("opacity", function (d) {
            return d.is_night ? 0.8 : d.after_hours ? 0.7 : 0.5;
        });

    // 节点
    netNode = netSvg.selectAll(".network_nodes")
        .data(netData.nodes)
        .enter()
        .append('image')
        .attr("xlink:href", d => image_ref[d.group] || image_ref[0])
        .attr("width", d => d.is_key_person ? 30 : 22)
        .attr("height", d => d.is_key_person ? 30 : 22)
        .attr("class", "network_nodes")
        .attr("id", d => "a" + d.id)
        .style("cursor", "pointer")
        // 关键人物金色光晕
        .style("filter", d => d.is_key_person
            ? "drop-shadow(0 0 4px #f59e0b)" : "none")
        .on("mouseover", function (event, d) {
            var id = "a" + d.id;
            highlightBasedOnNodeId(id);
            // Tooltip
            var content = d.group === 0
                ? "<b>" + d.name + "</b><br>Location"
                : "<b>" + d.firstname + " " + d.lastname + "</b><br>" +
                  (d.department || "") + " · " + (d.title || "");
            if (d.is_key_person) content += '<br><span style="color:#f59e0b">★ Key Person</span>';
            tooltip.style("opacity", 1)
                .html(content)
                .style("left", event.pageX + 16 + "px")
                .style("top", event.pageY - 10 + "px");
        })
        .on("mousemove", function (event) {
            tooltip.style("left", event.pageX + 16 + "px")
                .style("top", event.pageY - 10 + "px");
        })
        .on("mouseout", function (event, d) {
            var id = "a" + d.id;
            highlightBasedOnNodeId(id, true);
            tooltip.style("opacity", 0);
        });

    // 节点文字（只显示地点名和关键人物）
    netSvg.selectAll(".nodeTexts")
        .data(netData.nodes)
        .enter()
        .append('text')
        .attr("class", 'nodeTexts')
        .style("font-size", function (d) { return d.is_key_person ? "10px" : "8px"; })
        .style("font-weight", function (d) { return d.is_key_person ? "bold" : "normal"; })
        .style("fill", function (d) { return d.is_key_person ? "#dc2626" : "#64748b"; })
        .text(function (d) {
            if (d.group === 0) return d.name.length > 14 ? d.name.slice(0, 12) + ".." : d.name;
            if (d.is_key_person) return d.lastname;
            return "";
        });

    // 图例
    var legendX = networkWidth + 20;
    Object.keys(image_ref).forEach(function (g, i) {
        netSvg.append('image')
            .attr("xlink:href", image_ref[g])
            .attr("x", legendX).attr("y", 20 + i * 40)
            .attr("width", 20).attr("height", 20)
            .attr("id", "g" + g)
            .style("cursor", "pointer")
            .on("mouseover", function () { highlightBasedOnGroupId(this.id); })
            .on("mouseout", function () { highlightBasedOnGroupId(this.id, true); });
    });

    var legendNames = ['Location', 'Executive', 'Security', 'Facilities', 'IT', 'Engineering'];
    legendNames.forEach(function (name, i) {
        netSvg.append('text')
            .text(name)
            .attr("x", legendX + 26).attr("y", 35 + i * 40)
            .style("font-size", "12px").style("fill", "#475569")
            .style("cursor", "pointer")
            .attr("id", "g" + i)
            .on("mouseover", function () { highlightBasedOnGroupId(this.id); })
            .on("mouseout", function () { highlightBasedOnGroupId(this.id, true); });
    });

    // 边图例
    var edgeLegendY = 20 + 6 * 40 + 20;
    netSvg.append('line').attr("x1", legendX).attr("y1", edgeLegendY)
        .attr("x2", legendX + 30).attr("y2", edgeLegendY)
        .style("stroke", "#dc2626").style("stroke-width", 2.5).style("stroke-dasharray", "5,3");
    netSvg.append('text').text("Night (0-5h)").attr("x", legendX + 38).attr("y", edgeLegendY + 4)
        .style("font-size", "10px").style("fill", "#dc2626");

    netSvg.append('line').attr("x1", legendX).attr("y1", edgeLegendY + 18)
        .attr("x2", legendX + 30).attr("y2", edgeLegendY + 18)
        .style("stroke", "#f59e0b").style("stroke-width", 1.8).style("stroke-dasharray", "3,3");
    netSvg.append('text').text("After hours").attr("x", legendX + 38).attr("y", edgeLegendY + 22)
        .style("font-size", "10px").style("fill", "#f59e0b");

    netSvg.append('line').attr("x1", legendX).attr("y1", edgeLegendY + 36)
        .attr("x2", legendX + 30).attr("y2", edgeLegendY + 36)
        .style("stroke", "#cbd5e1").style("stroke-width", 1);
    netSvg.append('text').text("Work hours").attr("x", legendX + 38).attr("y", edgeLegendY + 40)
        .style("font-size", "10px").style("fill", "#94a3b8");

    // 力布局
    netSimulation = d3.forceSimulation(netData.nodes)
        .force("link", d3.forceLink().id(d => d.id).links(netData.links).distance(80))
        .force("charge", d3.forceManyBody().strength(-400))
        .force("center", d3.forceCenter((networkWidth) / 2, (networkHeight) / 2))
        .force("collision", d3.forceCollide().radius(20))
        .on("tick", ticked)
        .on("end", function () { console.log("Force simulation ended"); });

    function ticked() {
        netLink
            .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x).attr("y2", d => d.target.y);

        netNode.attr("x", d => d.x - 11).attr("y", d => d.y - 11);

        netSvg.selectAll('.nodeTexts')
            .attr("x", d => d.x + 14).attr("y", d => d.y + 4);
    }
}

// ── 节点高亮 ──
function highlightBasedOnNodeId(id, reset) {
    if (reset === undefined) reset = false;
    if (reset) {
        netNode.style('filter', function (d) {
            return d.is_key_person ? "drop-shadow(0 0 4px #f59e0b)" : "none";
        }).style('opacity', 1);
        netLink.style("opacity", function (d) {
            return d.is_night ? 0.8 : d.after_hours ? 0.7 : 0.5;
        });
        d3.selectAll('.nodeTexts').style('opacity', 1);
        return;
    }

    netNode.style('opacity', 0.15).style('filter', "none");
    d3.selectAll('#' + id).style('opacity', 1);
    // 保持关键人物光晕
    var selNode = netData.nodes.find(function (n) { return "a" + n.id === id; });
    if (selNode && selNode.is_key_person) {
        d3.selectAll('#' + id).style('filter', "drop-shadow(0 0 4px #f59e0b)");
    }

    netLink.each(function (l) {
        var linkId = "l" + l.source.id + "_" + l.target.id;
        if ("a" + l.source.id === id || "a" + l.target.id === id) {
            d3.select("#" + linkId).style("opacity", 1).style("stroke", "#3b82f6");
            d3.select("#a" + l.source.id).style("opacity", 1);
            d3.select("#a" + l.target.id).style("opacity", 1);
        } else {
            d3.select("#" + linkId).style("opacity", 0.05);
        }
    });
}

// ── 部门分组高亮 ──
function highlightBasedOnGroupId(groupId, reset) {
    if (reset === undefined) reset = false;
    if (groupId === "g0") reset = true;

    if (reset) {
        netNode.style('filter', function (d) {
            return d.is_key_person ? "drop-shadow(0 0 4px #f59e0b)" : "none";
        }).style('opacity', 1);
        netLink.style("opacity", function (d) {
            return d.is_night ? 0.8 : d.after_hours ? 0.7 : 0.5;
        });
        return;
    }

    var groupNum = parseInt(groupId.replace("g", ""));
    netNode.style('opacity', 0.1).style('filter', "none");
    netLink.style('opacity', 0.03);

    netData.links.forEach(function (l) {
        if (l.source.group === groupNum || l.target.group === groupNum) {
            d3.select("#a" + l.source.id).style('opacity', 1);
            d3.select("#a" + l.target.id).style('opacity', 1);
            d3.select("#l" + l.source.id + "_" + l.target.id).style("opacity", 1);
        }
    });

    // 保持关键人物光晕
    netData.nodes.forEach(function (n) {
        if (n.group === groupNum && n.is_key_person) {
            d3.select("#a" + n.id).style('filter', "drop-shadow(0 0 4px #f59e0b)");
        }
    });
}

// ── 外部联动接口 ──
function highlightInNetworkChartBasedOnSelection(selectedName) {
    d3.selectAll('.network_chart_links')
        .style("stroke", "#cbd5e1").style("stroke-width", "1px")
        .style("opacity", 0.5).style("stroke-dasharray", "none");

    if (NodeNameToNodeIdMapping[selectedName] !== undefined) {
        highlightBasedOnNodeId("a" + NodeNameToNodeIdMapping[selectedName]);
    }
}
