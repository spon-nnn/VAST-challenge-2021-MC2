// Ring / polar chart — CC transactions by date & time
var ringdata, ringsvg, filtereddata, ringheight, ringwidth;
var inwidth, inringheight, maxRadius, minRadius;
var parseTime, parsedate, dateToRadius, timeScale;
var uniquedates, loc, cc, selected_cc, selected_location;
var days, daylabel, timelabelangles, timelabel, time;

// Category → colour (dark theme palette)
const CAT_COLORS = {
  "Travel and Accommodation": "#00d4aa",
  "Miscellaneous":            "#f5a623",
  "Retail":                   "#7c5cbf",
  "Food and Beverage":        "#e05c8a",
  "Industrial":               "#4db8e8",
};

const LOC_CATEGORY = {
  "Abila Airport":"Travel and Accommodation","Abila Scrapyard":"Miscellaneous",
  "Abila Zacharo":"Miscellaneous","Ahaggo Museum":"Travel and Accommodation",
  "Albert's Fine Clothing":"Retail","Bean There Done That":"Food and Beverage",
  "Brew've Been Served":"Food and Beverage","Brewed Awakenings":"Food and Beverage",
  "Carlyle Chemical Inc.":"Industrial","Chostus Hotel":"Travel and Accommodation",
  "Coffee Cameleon":"Food and Beverage","Coffee Shack":"Food and Beverage",
  "Daily Dealz":"Retail","Desafio Golf Course":"Travel and Accommodation",
  "Frank's Fuel":"Miscellaneous","Frydos Autosupply n' More":"Retail",
  "Gelatogalore":"Food and Beverage","General Grocer":"Retail",
  "Guy's Gyros":"Food and Beverage","Hallowed Grounds":"Food and Beverage",
  "Hippokampos":"Food and Beverage","Jack's Magical Beans":"Food and Beverage",
  "Kalami Kafenion":"Food and Beverage","Katerina's Cafe":"Food and Beverage",
  "Kronos Mart":"Retail","Kronos Pipe and Irrigation":"Industrial",
  "Maximum Iron and Steel":"Industrial","Nationwide Refinery":"Industrial",
  "Octavio's Office Supplies":"Retail","Ouzeri Elian":"Food and Beverage",
  "Roberts and Sons":"Miscellaneous","Shoppers' Delight":"Retail",
  "Stewart and Sons Fabrication":"Miscellaneous","U-Pump":"Miscellaneous"
};

document.addEventListener('DOMContentLoaded', () => {
  Promise.all([d3.csv('data/charts/cctime_data.csv', d => ({
    date: d.date,
    price: +d.price,
    last4ccnum: +d.last4ccnum,
    location: d.location,
    time: d.time
  }))]).then(([rows]) => {
    ringdata = rows;
    ringwidth = 750; ringheight = 750;
    const pad = { top: 30, right: 30, bottom: 30, left: 100 };
    inwidth      = ringwidth  - pad.left - pad.right;
    inringheight = ringheight - pad.top  - pad.bottom;
    ringsvg = d3.select("#ring_svg");
    ringsvg.attr("viewBox", `0 0 ${ringwidth} ${ringheight}`)
           .attr("preserveAspectRatio", "xMidYMid meet");
    uniquedates = new Set(ringdata.map(d => d.date));
    buildCalendar();
    document.getElementById('dropdownloc').addEventListener('change', refreshRing);
    document.getElementById('dropdowncc').addEventListener('change', refreshRing);
    selected_location = document.getElementById("dropdownloc").value;
    selected_cc       = document.getElementById("dropdowncc").value;
    UpdateData(selected_location, selected_cc);
    buildLegend();
    drawRing();
  });
});

function UpdateData(selLoc, selCC) {
  d3.selectAll(".box_circles").style("opacity", selLoc === '1' ? 1 : 0.1);
  if (selLoc !== '1') {
    d3.selectAll('#box_' + location_index[selLoc]).style("opacity", 1);
    d3.select("#bar_" + location_index[selLoc]).style("stroke-width", 4);
  }
  d3.selectAll('.cc_bars').style('stroke-width', 1);
  selectLinkByCcNum(selCC);
  const allCC  = selCC  === '1';
  const allLoc = selLoc === '1';
  filtereddata = ringdata.filter(d =>
    ((d.last4ccnum == selCC) || allCC) &&
    ((d.location   == selLoc) || allLoc)
  );
}

function refreshRing() {
  selected_location = document.getElementById("dropdownloc").value;
  selected_cc       = document.getElementById("dropdowncc").value;
  UpdateData(selected_location, selected_cc);
  [days, timelabel, time].forEach(s => s && s.remove());
  drawRing();
  highlightInNetworkChartBasedOnSelection(selected_location);
}

function filterByRingId(token) {
  ringsvg.selectAll(".transactions").style("visibility", "hidden");
  if (token === 'dALL') {
    ringsvg.selectAll(".transactions")
      .style("stroke", "#fff").style("stroke-width", 0.5).style("visibility", "visible");
  } else {
    d3.selectAll(`[id*="${token}"]`)
      .style("stroke", "#fff").style("stroke-width", 0.5).style("visibility", "visible");
  }
}

function toAngle(t) { return (timeScale(parseTime(t)) * Math.PI) / 180; }

function drawRing() {
  parsedate = d3.timeParse("%Y-%m-%d");
  parseTime = d3.timeParse("%H:%M:%S");
  maxRadius = Math.min(inwidth, inringheight) / 2 - 30;
  minRadius = 50;

  const tip = d3.select("#right-ring-div")
    .append("div").style("opacity", 0).attr("class", "tooltipring")
    .style("background", "#1a1a30").style("color", "#e0e0f0")
    .style("border", "1px solid #7c5cbf").style("border-radius", "6px")
    .style("padding", "7px 10px").style("position", "absolute").style("font-size", "12px");

  dateToRadius = d3.scaleTime()
    .domain(d3.extent(ringdata, d => parsedate(d.date)))
    .range([minRadius, maxRadius]);

  timeScale = d3.scaleLinear()
    .domain([parseTime("00:00:00"), parseTime("23:59:59")])
    .range([360, 0]);

  days = ringsvg.selectAll(".days").data(Array.from(uniquedates)).join("circle")
    .attr("class", "days")
    .attr("cx", inwidth / 2).attr("cy", inringheight / 2)
    .attr("r", d => dateToRadius(parsedate(d)))
    .style("fill", "none").style("stroke", "#3a4a6a").style("opacity", 0.5);

  daylabel = ringsvg.selectAll(".day-label").data(Array.from(uniquedates)).join("text")
    .attr("class", "day-label").attr("text-anchor", "middle")
    .attr("x", inwidth / 2).attr("y", d => inringheight / 2 - dateToRadius(parsedate(d)) + 9)
    .text(d => d.slice(5).replace("-", "/"))
    .attr("opacity", 0.5).style("font-size", "9px").attr("fill", "#8888aa");

  ringsvg.selectAll(".axis-line").data(d3.range(2)).join("line")
    .attr("class", "axis-line")
    .attr("x1", d => inwidth / 2 + Math.cos(d * Math.PI / 2) * maxRadius)
    .attr("y1", d => inringheight / 2 + Math.sin(d * Math.PI / 2) * maxRadius)
    .attr("x2", d => inwidth / 2 + Math.cos(d * Math.PI / 2 + Math.PI) * maxRadius)
    .attr("y2", d => inringheight / 2 + Math.sin(d * Math.PI / 2 + Math.PI) * maxRadius)
    .attr("stroke", "#3a3a55").style("stroke-dasharray", "6,6").attr("opacity", 0.4);

  const angles = d3.range(360, 0, -45).map(x => x * Math.PI / 180);
  timelabel = ringsvg.selectAll(".time-label").data(angles).join("text")
    .attr("class", "time-label").attr("text-anchor", "middle").attr("fill", "#7070a0")
    .attr("x", d => inwidth / 2 + (maxRadius + 15) * Math.cos(d))
    .attr("y", d => inringheight / 2 + (maxRadius + 15) * Math.sin(d) + 5)
    .style("font-size", "11px")
    .text((_, i) => `${i * 3}h`);

  time = ringsvg.selectAll(".transactions").data(filtereddata).join("circle")
    .attr("class", "transactions")
    .attr("id", d => `c${d.last4ccnum}_t${d.time}_d${d.date}_l${d.location}_ty${LOC_CATEGORY[d.location]}`)
    .attr("cx", d => inwidth  / 2 + dateToRadius(parsedate(d.date)) * Math.cos(toAngle(d.time)))
    .attr("cy", d => inringheight / 2 + dateToRadius(parsedate(d.date)) * Math.sin(toAngle(d.time)))
    .attr("r", 3.5)
    .attr("fill", d => CAT_COLORS[LOC_CATEGORY[d.location]])
    .style("visibility", "visible").style("opacity", 0.85)
    .on("mouseover", function () { time.style("opacity", 0.2); d3.select(this).style("opacity", 1); })
    .on("mouseout",  function () { time.style("opacity", 0.85); tip.html("").style("opacity", 0); })
    .on("mousemove", (ev, d) => {
      tip.style("opacity", 1)
        .html(`CC: ${d.last4ccnum}<br>Spending: ${d.price}<br>Location: ${d.location}<br>Time: ${d.time}<br>Date: ${d.date}`)
        .style("left", ev.clientX + window.scrollX + 18 + "px")
        .style("top",  ev.clientY + window.scrollY - 18 + "px");
    });
}

function buildLegend() {
  cc  = new Set(ringdata.map(d => d.last4ccnum));
  loc = new Set(ringdata.map(d => d.location));

  const locSel = document.getElementById("dropdownloc");
  loc.forEach(v => { const o = document.createElement("option"); o.text = o.value = v; locSel.add(o); });
  const ccSel = document.getElementById("dropdowncc");
  cc.forEach(v => { const o = document.createElement("option"); o.text = o.value = v; ccSel.add(o); });

  const LW = 150;
  const legend = ringsvg.append("g").attr("class", "legend").attr("transform", "translate(600,10)");
  legend.append("text").attr("x", -65).attr("y", 3)
    .attr("text-anchor", "middle").attr("fill", "#a0a0c0")
    .style("font-size", "11px").text("Categories");

  let activeCat = null;
  const rects = legend.selectAll(".leg-rect").data(Object.keys(CAT_COLORS)).join("rect")
    .attr("class", "leg-rect")
    .attr("x", -120).attr("y", (_, i) => i * 20 + 8)
    .attr("width", 12).attr("height", 12).attr("rx", 2)
    .attr("fill", d => CAT_COLORS[d]).attr("stroke", "#555").attr("stroke-width", 1)
    .on("click", function (_, cat) {
      if (activeCat === cat) {
        rects.attr("stroke", "#555").attr("stroke-width", 1);
        d3.selectAll(".transactions").style("visibility", "visible").style("stroke", "none");
        activeCat = null;
      } else {
        rects.attr("stroke", "#555").attr("stroke-width", 1);
        d3.select(this).attr("stroke", "#00d4aa").attr("stroke-width", 2);
        activeCat = cat;
        filterByRingId("ty" + Object.keys(CAT_COLORS).indexOf(cat));
      }
    });

  legend.selectAll(".leg-text").data(Object.keys(CAT_COLORS)).join("text")
    .attr("class", "leg-text")
    .attr("x", -100).attr("y", (_, i) => i * 20 + 19)
    .attr("fill", "#9090b8").style("font-size", "10px")
    .text(d => d);
}

function buildCalendar() {
  const cal = ringsvg.append("g");
  const SZ = 22, PAD = 5;
  uniquedates.add('ALL');

  cal.append("text").attr("x", 60).attr("y", 130)
    .attr("text-anchor", "middle").attr("fill", "#00d4aa")
    .style("font-size", "13px").style("font-weight", "600")
    .text("Calendar");

  let activeCal = null;
  const squares = cal.selectAll(".cal-cell").data(Array.from(uniquedates)).join("rect")
    .attr("class", "cal-cell")
    .attr("x", (_, i) => (i % 4) * (SZ + PAD) + 10)
    .attr("y", (_, i) => Math.floor(i / 4) * (SZ + PAD) + 10)
    .attr("width", SZ).attr("height", SZ).attr("rx", 3)
    .attr("fill", "#2d2d50").attr("stroke", "#3a3a65")
    .on("click", function (_, d) {
      if (activeCal === d) {
        squares.attr("stroke", "#3a3a65");
        d3.selectAll(".transactions").style("visibility", "visible").style("stroke", "none");
        activeCal = null;
      } else {
        squares.attr("stroke", "#3a3a65");
        d3.select(this).attr("stroke", "#00d4aa");
        activeCal = d;
        filterByRingId("d" + Array.from(uniquedates).indexOf(d));
      }
    });

  cal.selectAll(".cal-label").data(Array.from(uniquedates)).join("text")
    .attr("class", "cal-label").style("pointer-events", "none")
    .attr("x", (_, i) => (i % 4) * (SZ + PAD) + SZ / 2 + 10)
    .attr("y", (_, i) => Math.floor(i / 4) * (SZ + PAD) + SZ / 2 + 10)
    .attr("text-anchor", "middle").attr("dominant-baseline", "central")
    .attr("fill", "#b0b0d0").style("font-size", "11px")
    .text(d => d.slice(-3).replace('-', ''));
}
