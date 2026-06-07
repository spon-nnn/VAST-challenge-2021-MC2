// Force-directed network — employee–location relationships
var node, link, netData, node_text;
var NodeNameToNodeIdMapping = {};

const ICON_MAP = {
  0: "data/icons/circle-15.svg",
  1: "data/icons/square-15.svg",
  2: "data/icons/triangle.svg",
  3: "data/icons/Star.svg",
  4: "data/icons/hexagon.svg",
  5: "data/icons/penta.svg"
};

const LEGEND_LABELS = ['Location','Executive','Security','Facilities','IT','Engineering'];

document.addEventListener('DOMContentLoaded', () => {
  d3.json('data/charts/network-plot.json').then(data => {
    netData = data;
    data.nodes.forEach(n => { NodeNameToNodeIdMapping[n.name] = n.id; });
    renderNetwork(data);
  });
});

function renderNetwork(data) {
  const m = { top: 50, right: 30, bottom: 100, left: 260 };
  const W = 900 - m.left - m.right;
  const H = 900 - m.top  - m.bottom;

  const canvas = d3.select('#network_svg')
    .append('g').attr("transform", `translate(${m.left},${m.top})`);

  link = canvas.selectAll(".net-link").data(data.links).join("line")
    .attr("class", "network_chart_links")
    .attr("id", d => `l${d.source}_${d.target}`)
    .style("stroke", "#2a3a50").style("stroke-width", 1.2);

  node = canvas.selectAll(".net-node").data(data.nodes).join("image")
    .attr("xlink:href", d => ICON_MAP[d.group])
    .attr("width", 24).attr("height", 24)
    .attr("class", "network_nodes").attr("id", d => `a${d.id}`)
    .on("mouseover", ev => nodeHover(ev.target.id))
    .on("mouseout",  ev => nodeHover(ev.target.id, true));

  node_text = canvas.selectAll(".net-label").data(data.nodes).join("text")
    .attr("class", "nodeTexts").attr("id", d => `a${d.id}`)
    .style("opacity", 0.18).style("font-size", "10px")
    .attr("fill", "#8080a0")
    .text(d => d.group === 0 ? d.name : `${d.firstname} ${d.lastname}`);

  // Legend icons
  canvas.selectAll(".leg-icon").data(Object.keys(ICON_MAP)).join("image")
    .attr("xlink:href", d => ICON_MAP[d])
    .attr("id", d => `g${d}`)
    .attr("x", W - 10).attr("y", (_, i) => H - 70 + i * 35)
    .attr("width", 24).attr("height", 24)
    .on("mouseover", function () { groupHover(this.id); })
    .on("mouseout",  function () { groupHover(this.id, true); });

  canvas.selectAll(".leg-text").data(LEGEND_LABELS).join("text")
    .attr("id", (_, i) => `g${i}`)
    .attr("x", W + 20).attr("y", (_, i) => H - 52 + i * 35)
    .attr("fill", "#8888a8").style("font-size", "12px")
    .text(d => d)
    .on("mouseover", function () { groupHover(this.id); })
    .on("mouseout",  function () { groupHover(this.id, true); });

  const sim = d3.forceSimulation(data.nodes)
    .force("link", d3.forceLink().id(d => d.id).links(data.links))
    .force("charge", d3.forceManyBody().strength(-500))
    .force("center", d3.forceCenter(W / 2, H / 2))
    .on("end", () => {
      link
        .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
      node.attr("x", d => d.x - 12).attr("y", d => d.y - 12);
      node_text.attr("x", d => d.x - 12).attr("y", d => d.y - 12);
    });
}

function nodeHover(id, reset = false) {
  if (reset) {
    node.style('filter', 'grayscale(0)').style('opacity', 1);
    node_text.style('opacity', 0.18);
    netData.links.forEach(x => {
      d3.select(`#l${x.source.id}_${x.target.id}`)
        .style("stroke", "#2a3a50").style("stroke-width", "1.2px").style("opacity", 1);
    });
    return;
  }
  node.style('filter', 'grayscale(1)').style('opacity', 0.2);
  d3.selectAll(`#${id}`).style('filter', 'grayscale(0)').style('opacity', 1);

  netData.links.forEach(x => {
    const srcId = `a${x.source.id}`, tgtId = `a${x.target.id}`;
    const linkSel = d3.select(`#l${x.source.id}_${x.target.id}`);
    if (srcId === id || tgtId === id) {
      d3.selectAll(`#${srcId}, #${tgtId}`).style('filter', 'grayscale(0)').style('opacity', 1);
      linkSel.style("stroke", "#00d4aa").style("stroke-width", "2px").style("opacity", 1);
    } else {
      linkSel.style("opacity", 0.15);
    }
  });
}

function highlightInNetworkChartBasedOnSelection(name) {
  d3.selectAll('.network_chart_links').style("stroke", "#2a3a50").style("stroke-width", "1.2px").style("opacity", 1);
  nodeHover("a" + NodeNameToNodeIdMapping[name]);
}

function groupHover(groupId, reset = false) {
  if (reset || groupId === "g0") {
    node.style('filter', 'grayscale(0)').style('opacity', 1);
    node_text.style('opacity', 0.18);
    netData.links.forEach(x => {
      d3.select(`#l${x.source.id}_${x.target.id}`)
        .style("stroke", "#2a3a50").style("stroke-width", "1.2px").style("opacity", 1);
    });
    return;
  }
  node.style('filter', 'grayscale(1)').style('opacity', 0.2);
  netData.links.forEach(x => {
    if (`g${x.source.group}` === groupId) {
      d3.selectAll(`#a${x.source.id}, #a${x.target.id}`).style('filter', 'grayscale(0)').style('opacity', 1);
      d3.select(`#l${x.source.id}_${x.target.id}`)
        .style("stroke", "#7c5cbf").style("stroke-width", "2px").style("opacity", 1);
    } else {
      d3.select(`#l${x.source.id}_${x.target.id}`).style("opacity", 0.1);
    }
  });
}
