// Sankey diagram — CC → Loyalty card flow, split across 3 columns
var LINK_OPACITY = 0.72;
var carNodeClicked = false;

function selectLinkByCcNum(ccVal) {
  const allLinks = d3.selectAll(".link");
  if (ccVal === '1') {
    allLinks.style("opacity", LINK_OPACITY);
  } else {
    allLinks.style("opacity", 0.08);
    allLinks.filter(d => d.source.name === ccVal).style("opacity", LINK_OPACITY);
  }
}

function buildSankeyPanel(svgId, rows) {
  const m = { top: 10, right: 30, bottom: 10, left: 10 };
  const H = Math.max(rows.length * 20, 110);
  const svgEl = d3.select("#" + svgId)
    .attr("height", H + m.top + m.bottom);

  // measure actual rendered width
  const W = svgEl.node().getBoundingClientRect().width - m.left - m.right || 300;

  const svg = svgEl.append("g").attr("transform", `translate(${m.left},${m.top})`);

  const fmt = d3.format(",.0f");
  const linkColor = d3.scaleOrdinal(d3.schemeTableau10);

  const graph = { nodes: [], links: [] };
  // Key nodes by side so a number that appears as BOTH a cc_num and a
  // loyalty_num (e.g. "4948" in panel 2/3) stays two distinct nodes instead
  // of being merged into one — merging produced links that crossed the panel.
  const nodeIndex = new Map();
  function nodeId(name, side) {
    const key = side + ":" + name;
    if (!nodeIndex.has(key)) {
      nodeIndex.set(key, graph.nodes.length);
      graph.nodes.push({ name: name, side: side });
    }
    return nodeIndex.get(key);
  }
  rows.forEach(r => {
    graph.links.push({
      source: nodeId(r.cc_num, "cc"),
      target: nodeId(r.loyalty_num, "loyalty"),
      value: +r.frequency
    });
  });

  const sankeyGen = d3.sankey()
    .nodeWidth(10).nodePadding(10)
    .size([W, H])
    .nodeAlign(d3.sankeyRight);

  const layout = sankeyGen(graph);

  const pathSel = svg.append("g").selectAll(".link")
    .data(layout.links).join("path")
    .attr("class", "link")
    .attr("d", d3.sankeyLinkHorizontal())
    .attr("stroke-width", d => Math.max(1, d.width))
    .style("opacity", LINK_OPACITY)
    .style("stroke", d => linkColor(d.source.index));

  pathSel.append("title").text(d =>
    `${d.source.name} → ${d.target.name}\nTransactions: ${fmt(d.value)}`
  );
  pathSel
    .on("mouseover", function () { pathSel.style("opacity", 0.08); d3.select(this).style("opacity", 1); })
    .on("mouseleave", () => pathSel.style("opacity", LINK_OPACITY));

  const nodeSel = svg.append("g").selectAll(".node")
    .data(layout.nodes).join("g").attr("class", "node");

  nodeSel.append("rect")
    .attr("x", d => d.x0).attr("y", d => d.y0)
    .attr("height", d => d.y1 - d.y0).attr("width", sankeyGen.nodeWidth())
    .attr("nodeId", d => d.name)
    .attr("fill", "#6a5acd").attr("rx", 2)
    .append("title").text(d => {
      const kind = d.side === "cc" ? "Credit Card" : "Loyalty Card";
      return `${kind}: ${d.name}\nTransactions: ${fmt(d.value)}`;
    });

  nodeSel
    .on("mouseover", ev => {
      const id = ev.target.getAttribute("nodeId");
      pathSel.style("opacity", d =>
        d.source.name === id || d.target.name === id ? LINK_OPACITY : 0.08
      );
    })
    .on("mouseleave", () => pathSel.style("opacity", LINK_OPACITY))
    .on("click", ev => {
      const rect = d3.select(ev.target);
      const name = ev.srcElement.__data__.name;
      const isSelected = rect.style("stroke") !== "none";
      if (!isSelected) {
        rect.style("stroke", "#00d4aa").style("stroke-width", "2px");
        if (name.length < 4) { selected_cars.push(name); updateData(name); plotGPS(); }
        else {
          d3.select("#dropdowncc").property('value', name);
          document.querySelector("#dropdowncc").dispatchEvent(new Event('change'));
        }
      } else {
        rect.style("stroke", null).style("stroke-width", null);
        if (selected_cars.includes(name)) {
          selected_cars.splice(selected_cars.indexOf(name), 1);
          updateData(name); plotGPS();
        } else {
          d3.select("#dropdowncc").property('value', "1");
          document.querySelector("#dropdowncc").dispatchEvent(new Event('change'));
        }
      }
    });

  nodeSel.append("text")
    .attr("x", d => d.x0 - 6).attr("y", d => (d.y1 + d.y0) / 2)
    .attr("dy", "0.35em").attr("text-anchor", "end")
    .attr("fill", "#c0c0e8").style("font-size", "10px")
    .text(d => d.name)
    .filter(d => d.x0 < W / 2)
    .attr("x", d => d.x1 + 6).attr("text-anchor", "start");
}

document.addEventListener('DOMContentLoaded', () => {
  d3.csv("data/charts/sankey_chart_data(car_cc_loyalty_frequency).csv").then(rows => {
    const third = Math.ceil(rows.length / 3);
    buildSankeyPanel("shankey_svg",  rows.slice(0, third));
    buildSankeyPanel("shankey_svg2", rows.slice(third, third * 2));
    buildSankeyPanel("shankey_svg3", rows.slice(third * 2));
  });
});
