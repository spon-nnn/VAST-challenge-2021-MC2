// Box plot — price distribution per location (log scale)
const BP = {
  margin: { top: 50, right: 30, bottom: 130, left: 70 },
  w: 1160,
  h: 900,
  boxW: 28,
  fill: "#7c5cbf",      // purple boxes
  fillHl: "#a07de0",
  stroke: "#b0a4e8",
  medianClr: "#00d4aa", // teal median line
  dotClr: "#e0d0ff",
};
BP.inner_w = BP.w - BP.margin.left - BP.margin.right;
BP.inner_h = BP.h - BP.margin.top - BP.margin.bottom;

const LOC_DOMAIN = [
  "Abila Airport","Abila Scrapyard","Abila Zacharo","Ahaggo Museum",
  "Albert's Fine Clothing","Bean There Done That","Brew've Been Served",
  "Brewed Awakenings","Carlyle Chemical Inc.","Chostus Hotel",
  "Coffee Cameleon","Coffee Shack","Daily Dealz","Desafio Golf Course",
  "Frank's Fuel","Frydos Autosupply n' More","Gelatogalore","General Grocer",
  "Guy's Gyros","Hallowed Grounds","Hippokampos","Jack's Magical Beans",
  "Kalami Kafenion","Katerina's Cafe","Kronos Mart","Kronos Pipe and Irrigation",
  "Maximum Iron and Steel","Nationwide Refinery","Octavio's Office Supplies",
  "Ouzeri Elian","Roberts and Sons","Shoppers' Delight",
  "Stewart and Sons Fabrication","U-Pump"
];

document.addEventListener('DOMContentLoaded', () => {
  const root = d3.select("#box_plot_svg")
    .append("g")
    .attr("transform", `translate(${BP.margin.left},${BP.margin.top})`);

  d3.csv("data/charts/cc_data.csv").then(raw => {
    const stats = d3.rollup(raw, vals => {
      const sorted = vals.map(r => +r.amount).sort(d3.ascending);
      const q1  = d3.quantile(sorted, 0.25);
      const med = d3.quantile(sorted, 0.5);
      const q3  = d3.quantile(sorted, 0.75);
      return { q1, med, q3, lo: d3.quantile(sorted, 0), hi: d3.quantile(sorted, 1) };
    }, r => r.venue);

    const xBand = d3.scaleBand()
      .domain(LOC_DOMAIN).range([0, BP.inner_w])
      .paddingInner(1).paddingOuter(0.5);

    const yLog = d3.scaleLog().domain([2, 12000]).range([BP.inner_h, 0]);

    // Axes
    root.append("g")
      .attr("transform", `translate(0,${BP.inner_h})`)
      .call(d3.axisBottom(xBand))
      .selectAll("text")
      .attr("transform", "translate(-10,0)rotate(-45)")
      .style("text-anchor", "end")
      .style("fill", "#9090b8").style("font-size", "11px");

    root.selectAll(".domain, .tick line").style("stroke", "#3a3a55");
    root.append("g").call(d3.axisLeft(yLog))
      .selectAll("text, .domain, .tick line").style("fill", "#9090b8").style("stroke", "#3a3a55");

    // Whisker lines
    root.selectAll(".whisker").data(stats).join("line")
      .attr("class", "whisker")
      .attr("x1", d => xBand(d[0])).attr("x2", d => xBand(d[0]))
      .attr("y1", d => yLog(d[1].lo)).attr("y2", d => yLog(d[1].hi))
      .attr("stroke", BP.stroke).attr("stroke-width", 1.5);

    // IQR boxes
    root.selectAll(".iqr-box").data(stats).join("rect")
      .attr("class", "iqr-box")
      .attr("x", d => xBand(d[0]) - BP.boxW / 2)
      .attr("y", d => yLog(d[1].q3))
      .attr("height", d => yLog(d[1].q1) - yLog(d[1].q3))
      .attr("width", BP.boxW)
      .attr("fill", BP.fill).attr("stroke", BP.stroke).attr("rx", 2);

    // Median lines
    root.selectAll(".median-line").data(stats).join("line")
      .attr("class", "median-line")
      .attr("x1", d => xBand(d[0]) - BP.boxW / 2)
      .attr("x2", d => xBand(d[0]) + BP.boxW / 2)
      .attr("y1", d => yLog(d[1].med)).attr("y2", d => yLog(d[1].med))
      .attr("stroke", BP.medianClr).attr("stroke-width", 2.5);

    // Axis labels
    root.append("text").attr("class", "xlabel")
      .attr("text-anchor", "middle")
      .attr("x", BP.inner_w / 2).attr("y", BP.inner_h + 110)
      .attr("fill", "#a0a0c8").style("font-size", "16px")
      .text("Locations");

    root.append("text").attr("class", "ylabel")
      .attr("transform", "rotate(-90)")
      .attr("y", -BP.margin.left + 10).attr("x", -(BP.inner_h / 2))
      .attr("text-anchor", "middle").attr("fill", "#a0a0c8")
      .style("font-size", "16px").text("Price (log scale)");

    // Jittered points
    const tip = d3.select("#box_plot_div")
      .append("div").style("opacity", 0)
      .style("background", "#1a1a30").style("color", "#e0e0f0")
      .style("border", "1px solid #7c5cbf").style("border-radius", "6px")
      .style("padding", "7px 10px").style("position", "absolute").style("font-size", "12px");

    const JITTER = 20;
    root.selectAll(".dot").data(raw).join("circle")
      .attr("class", "box_circles")
      .attr("id", d => "box_" + location_index[d.venue])
      .attr("cx", d => xBand(d.venue) - JITTER / 2 + Math.random() * JITTER)
      .attr("cy", d => yLog(d.amount))
      .attr("r", 2.5)
      .attr("fill", BP.dotClr).attr("fill-opacity", 0.55)
      .attr("stroke", "none")
      .on("mousemove", (ev, d) => {
        tip.style("opacity", 1)
          .html(`Price: ${d.amount}<br>Location: ${d.venue}<br>Time: ${d.ts}<br>CC: ${d.cc4}`)
          .style("left", ev.clientX + window.scrollX + 18 + "px")
          .style("top",  ev.clientY + window.scrollY - 18 + "px");
      })
      .on("mouseout", () => tip.html("").style("opacity", 0));
  });
});
