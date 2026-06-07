// Circular bar chart — transaction frequency by location
var activeBar = null;

const CIRC_MARGIN = { top: 100, right: 0, bottom: 0, left: 0 };
const CIRC_W = 560 - CIRC_MARGIN.left - CIRC_MARGIN.right;
const CIRC_H = 660 - CIRC_MARGIN.top - CIRC_MARGIN.bottom;
const INNER_R = 110;
const OUTER_R = Math.min(CIRC_W, CIRC_H) / 2 - 50;

// Dark-theme accent colours: teal for CC, amber for loyalty
const CLR_CC     = "#00d4aa";
const CLR_LOYAL  = "#f5a623";

document.addEventListener('DOMContentLoaded', () => {
  d3.csv("data/charts/popularlocationdata.csv").then(rows => {
    buildCircularChart(rows);
  });
});

function handleBarClick(event, d) {
  const loc = d.location;
  const sel = d3.select("#dropdownloc");

  if (activeBar === event.target.id) {
    // deselect
    d3.selectAll('.cc_bars').style('stroke-width', 1);
    d3.selectAll(".box_circles").style("opacity", 1);
    activeBar = null;
    sel.property('value', 1);
    sel.node().dispatchEvent(new Event('change'));
  } else {
    d3.selectAll('.cc_bars').style('stroke-width', 1);
    d3.select("#" + event.target.id).style("stroke-width", 3);
    d3.selectAll(".box_circles").style("opacity", 0.1);
    d3.selectAll('#box_' + location_index[loc]).style("opacity", 1);
    activeBar = event.target.id;
    sel.property('value', loc);
    sel.node().dispatchEvent(new Event('change'));
  }
}

function buildCircularChart(rows) {
  d3.select("#circular_bar_svg")
    .attr("viewBox", `0 0 ${CIRC_W} ${CIRC_H + CIRC_MARGIN.top}`)
    .attr("preserveAspectRatio", "xMidYMid meet");
  const svg = d3.select("#circular_bar_svg")
    .append("g")
    .attr("transform", `translate(${CIRC_W / 2 + CIRC_MARGIN.left - 45},${CIRC_H / 2 + CIRC_MARGIN.top})`);

  const SQ = 16;
  // Legend
  [{ clr: CLR_CC, label: "Credit Card Transactions", dy: -50 },
   { clr: CLR_LOYAL, label: "Loyalty Card Transactions", dy: -22 }].forEach(({ clr, label, dy }) => {
    svg.append("rect")
      .attr("x", -CIRC_W / 2 + 55).attr("y", -CIRC_H / 2 + dy)
      .attr("width", SQ).attr("height", SQ).attr("fill", clr).attr("rx", 3);
    svg.append("text")
      .attr("x", -CIRC_W / 2 + 78).attr("y", -CIRC_H / 2 + dy + SQ / 2)
      .attr("dominant-baseline", "middle")
      .style("font-size", "12px").attr("fill", "#c0c0e0")
      .text(label);
  });

  const angleScale = d3.scaleBand()
    .range([0, 2 * Math.PI]).align(0)
    .domain(rows.map(d => d.location));

  const radCC = d3.scaleRadial()
    .range([INNER_R, OUTER_R]).domain([2, 220]);

  const radLoy = d3.scaleRadial()
    .range([INNER_R, 3]).domain([1, 220]);

  const tip = d3.select("#left-circular-div")
    .append("div").style("opacity", 0).attr("class", "tooltip")
    .style("background", "#1a1a30").style("color", "#e0e0f0")
    .style("border", "1px solid #7c5cbf").style("border-radius", "6px")
    .style("padding", "7px 10px").style("position", "absolute").style("font-size", "12px");

  const arcCC = d3.arc()
    .innerRadius(INNER_R)
    .outerRadius(d => radCC(d.cc_count))
    .startAngle(d => angleScale(d.location))
    .endAngle(d => angleScale(d.location) + angleScale.bandwidth())
    .padAngle(0.01).padRadius(INNER_R);

  svg.selectAll(".cc_bars").data(rows).join("path")
    .attr("class", "cc_bars")
    .attr("id", d => "bar_" + location_index[d.location])
    .attr("fill", CLR_CC).style("opacity", 0.75)
    .style("stroke", "#1e1e2e").style("stroke-width", 1)
    .attr("d", arcCC)
    .on("mouseover", (_, d) => tip.style("opacity", 1))
    .on("mouseout",  ()    => tip.html("").style("opacity", 0))
    .on("mousemove", (ev, d) => {
      tip.html(`Transactions: ${d.cc_count}<br>Location: ${d.location}`)
        .style("left", ev.clientX + window.scrollX + 18 + "px")
        .style("top",  ev.clientY + window.scrollY - 18 + "px");
    })
    .on("click", handleBarClick);

  // Location labels
  svg.selectAll(".loc-label").data(rows).join("g")
    .attr("text-anchor", d => (angleScale(d.location) + angleScale.bandwidth() / 2 + Math.PI) % (2 * Math.PI) < Math.PI ? "end" : "start")
    .attr("transform", d => `rotate(${(angleScale(d.location) + angleScale.bandwidth() / 2) * 180 / Math.PI - 90})translate(${radCC(d.cc_count) + 10},0)`)
    .append("text")
    .text(d => d.location)
    .attr("transform", d => (angleScale(d.location) + angleScale.bandwidth() / 2 + Math.PI) % (2 * Math.PI) < Math.PI ? "rotate(180)" : "rotate(0)")
    .style("font-size", "12px").attr("fill", "#a0a0c8").attr("dominant-baseline", "middle");

  const arcLoy = d3.arc()
    .innerRadius(d => radLoy(0))
    .outerRadius(d => radLoy(d.loyalty_count))
    .startAngle(d => angleScale(d.location))
    .endAngle(d => angleScale(d.location) + angleScale.bandwidth())
    .padAngle(0.01).padRadius(INNER_R);

  svg.selectAll(".lc_bars").data(rows).join("path")
    .attr("class", "lc_bars")
    .attr("id", d => "bar_u" + location_index[d.location])
    .attr("fill", CLR_LOYAL).style("opacity", 0.75)
    .style("stroke", "#1e1e2e").style("stroke-width", 1)
    .attr("d", arcLoy)
    .on("mouseover", (_, d) => tip.style("opacity", 1))
    .on("mouseout",  ()    => tip.html("").style("opacity", 0))
    .on("mousemove", (ev, d) => {
      tip.html(`Transactions: ${d.loyalty_count}<br>Location: ${d.location}`)
        .style("left", ev.clientX + window.scrollX + 18 + "px")
        .style("top",  ev.clientY + window.scrollY - 18 + "px");
    });
}
