// GPS map — vehicle movement visualization
var abila, carOwners, abilaPath, svg_map, abilaProjection;
var mapmargin = { top: 20, right: 20, bottom: 40, left: 40 };
var mapwidth, mapheight;   // computed at load from the rendered SVG width
var MAP_ASPECT = 1535 / 2740; // keep the tourist-map image's native ratio

var gpsData, mapdata = [], mapcolor, svg_cars;
var selected_cars = [], date, gdc, homes, plotData = {};
var xScale, drag;

var timeMinMax = {
  min: new Date('January 06, 2014 00:00:00'),
  max: new Date('January 06, 2014 23:59:59')
};

const sortByTime = (a, b) =>
  new Date(a.Timestamp).getTime() - new Date(b.Timestamp).getTime();

const carIds = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,
  22,23,24,25,26,27,28,29,30,31,32,33,34,35,101,104,105,106,107];

// 50-colour dark-friendly palette
const CAR_PALETTE = [
  '#e63946','#f4a261','#e9c46a','#2ec4b6','#84bc9c','#a8dadc',
  '#457b9d','#1d3557','#f72585','#b5179e','#7209b7','#3a0ca3',
  '#4361ee','#4cc9f0','#06d6a0','#ffd166','#ef476f','#118ab2',
  '#073b4c','#cbf3f0','#ffafcc','#bde0fe','#a2d2ff','#cdb4db',
  '#ffc8dd','#ffb703','#fb8500','#8ecae6','#219ebc','#023047',
  '#e76f51','#f4a261','#2a9d8f','#264653','#6d6875','#b5838d',
  '#e5989b','#ffb4a2','#ffcb69','#d4a373','#a7c957','#6a994e',
  '#386641','#bc4749','#c77dff','#9d4edd','#5a189a','#3c096c',
  '#10002b','#e0aaff'
];

document.addEventListener('DOMContentLoaded', () => {
  Promise.all([
    d3.json('data/map/abila.geojson'),
    d3.csv('data/map/gps.csv'),
    d3.csv('data/map/car-assignments.csv'),
    d3.json('data/map/day_car_gps_mapping.json'),
    d3.json('data/map/house_coordinates.json')
  ]).then(([geo, gps, owners, dayMap, houseData]) => {
    abila = geo; gpsData = gps; carOwners = owners; gdc = dayMap; homes = houseData;

    document.getElementById('play').addEventListener('click', timelapse);
    mapcolor  = d3.scaleOrdinal().domain(carIds).range(CAR_PALETTE);
    svg_map   = d3.select('#map_svg');

    // Size the drawing area to the rendered SVG width, keeping the image's
    // aspect ratio, and grow the SVG height to fit the map + time axis below.
    const svgW = svg_map.node().getBoundingClientRect().width || 900;
    mapwidth  = svgW - mapmargin.left - mapmargin.right;
    mapheight = mapwidth * MAP_ASPECT;
    svg_map.attr('height', mapheight + mapmargin.top + mapmargin.bottom + 30);

    date      = new Date(document.getElementById('date').value);
    date      = new Date(+date + date.getTimezoneOffset() * 60000);
    drag      = d3.drag();

    svg_map.append('image')
      .attr('x', 0).attr('y', 0)
      .attr('xlink:href', 'data/map/MC2-tourist.jpg')
      .attr('height', mapheight).attr('width', mapwidth)
      .attr('opacity', 0.6);

    abilaProjection = d3.geoEquirectangular().fitSize([mapwidth, mapheight], abila);
    abilaPath = d3.geoPath().projection(abilaProjection);

    addCars(carIds);
    renderMap();
    plotGPS();
  });
});

function renderMap() {
  svg_map.selectAll('.abila').data(abila.features).join('path')
    .attr('class', 'abila')
    .attr('d', abilaPath)
    .attr('fill', '#1e2a3a')
    .attr('stroke', '#4a6080')
    .attr('stroke-width', '1px')
    .style('opacity', 0.6);

  xScale = d3.scaleLinear().domain([0, 24]).range([mapmargin.left, mapwidth]);
  const xAxisG = svg_map.append('g')
    .attr('transform', `translate(-10,${mapheight + 20})`)
    .call(d3.axisBottom(xScale));
  xAxisG.selectAll('text').style('fill', '#8090a8').style('font-size', '13px');
  xAxisG.selectAll('.domain, .tick line').style('stroke', '#3a4a5a');

  svg_map.selectAll('.home-marker').data(Object.entries(homes)).join('rect')
    .attr('class', 'home-marker')
    .attr('x', d => abilaProjection([+d[1].range[0][0], +d[1].range[0][1]])[0])
    .attr('y', d => abilaProjection([+d[1].range[0][0], +d[1].range[0][1]])[1])
    .attr('height', 18).attr('width', 18).attr('rx', 2)
    .attr('fill', '#7c5cbf').style('opacity', 0.7)
    .append('title').text(d => d[1].name);
}

function plotGPS() {
  svg_map.selectAll('.gps').data(mapdata)
    .join(enter => enter.append('circle'))
    .attr('class', 'gps')
    .attr('cx', d => abilaProjection([+d.long, +d.lat])[0])
    .attr('cy', d => abilaProjection([+d.long, +d.lat])[1])
    .attr('r', 3.5)
    .style('fill', d => mapcolor(d.id))
    .style('opacity', 0.65)
    .call(drag);

  svg_map.selectAll('.timeline').remove();
  svg_map.selectAll('.tl-mark').data(Object.entries(timeMinMax)).enter()
    .append('line').attr('class', 'timeline')
    .attr('id', d => 'timeline' + d[0])
    .attr('x1', d => xScale(+d[1].getHours() + d[1].getMinutes() / 60) - 10)
    .attr('y1', mapheight + 10)
    .attr('x2', d => xScale(+d[1].getHours() + d[1].getMinutes() / 60) - 10)
    .attr('y2', mapheight + 30)
    .attr('stroke', '#00d4aa').attr('stroke-width', '4px');
}

function addCars(ids) {
  svg_cars = d3.select('#map_cars');

  svg_cars.selectAll('.highlight-bg').data(ids).join('rect')
    .attr('id', d => `car_${d}`).attr('class', 'highlight-bg')
    .attr('x', 40).attr('y', (_, i) => (i + 1) * 25)
    .attr('height', 20).attr('width', 200)
    .style('opacity', 0).attr('fill', '#7c5cbf');

  svg_cars.selectAll('.car-swatch').data(ids).join('rect')
    .attr('id', d => d).attr('class', 'cars')
    .attr('x', 20).attr('y', (_, i) => (i + 1) * 25)
    .attr('height', 20).attr('width', 20).attr('rx', 3)
    .attr('fill', d => mapcolor(d))
    .on('click', (ev) => {
      const id = ev.target.id;
      selected_cars.includes(id) ? selected_cars.splice(selected_cars.indexOf(id), 1) : selected_cars.push(id);
      updateData(id); plotGPS();
    });

  const filtered = carOwners.filter(o => ids.includes(parseInt(o.CarID)));

  svg_cars.selectAll('.car-id-label').data(ids).join('text')
    .attr('class', 'carIds').attr('x', 46).attr('y', (_, i) => (i + 1) * 25 + 15)
    .attr('fill', '#b0b8d0').style('font-size', '12px')
    .text(d => d)
    .on('click', ev => {
      const id = ev.target.innerHTML;
      selected_cars.includes(id)
        ? (selected_cars.splice(selected_cars.indexOf(id), 1), d3.selectAll(`#car_${id}`).style('opacity', 0))
        : (selected_cars.push(id), d3.selectAll(`#car_${id}`).style('opacity', 0.5));
      updateData(id); plotGPS();
    });

  svg_cars.selectAll('.owner-label').data(filtered).join('text')
    .attr('class', 'carOwners').attr('x', 72).attr('y', (_, i) => (i + 1) * 25 + 15)
    .attr('fill', '#8890a8').style('font-size', '11px')
    .text(d => `${d.FirstName} ${d.LastName}`)
    .on('click', ev => {
      const cid = ev.target.__data__.CarID;
      selected_cars.includes(cid)
        ? (selected_cars.splice(selected_cars.indexOf(cid), 1), d3.selectAll(`#car_${cid}`).style('opacity', 0))
        : (selected_cars.push(cid), d3.selectAll(`#car_${cid}`).style('opacity', 0.5));
      updateData(cid); plotGPS();
    });
}

function updateData(carId) {
  highlightInNetworkChartBasedOnSelection(carId);
  if (selected_cars.includes(carId)) {
    plotData[carId] = gdc[date.getDate()][carId];
    d3.selectAll(`#car_${carId}`).style('opacity', 0.5);
  } else {
    delete plotData[carId];
    d3.selectAll(`#car_${carId}`).style('opacity', 0);
  }
  mapdata = [];
  Object.values(plotData).forEach(pts => pts.forEach(p => mapdata.push(p)));
  mapdata.sort(sortByTime);
  if (selected_cars.length > 0) {
    timeMinMax.min = new Date(mapdata[0].Timestamp);
    timeMinMax.max = new Date(mapdata[mapdata.length - 1].Timestamp);
  }
}

function timelapse() {
  svg_map.select('#timelinemin')
    .transition().duration(mapdata.length * 5 + 500).ease(d3.easeLinear)
    .attr('x1', xScale(+timeMinMax.max.getHours() + timeMinMax.max.getMinutes() / 60) - 10)
    .attr('y1', mapheight + 10)
    .attr('x2', xScale(+timeMinMax.max.getHours() + timeMinMax.max.getMinutes() / 60) - 10)
    .attr('y2', mapheight + 30)
    .on('end', () => {
      svg_map.select('#timelinemin')
        .attr('x1', xScale(+timeMinMax.min.getHours() + timeMinMax.min.getMinutes() / 60) - 10)
        .attr('y1', mapheight + 10)
        .attr('x2', xScale(+timeMinMax.min.getHours() + timeMinMax.min.getMinutes() / 60) - 10)
        .attr('y2', mapheight + 30);
    });

  svg_map.selectAll('.gps').remove();
  svg_map.selectAll('.gps').data(mapdata)
    .join(enter => enter.append('circle').style('opacity', 0).style('fill', '#333'))
    .attr('class', 'gps')
    .attr('cx', d => abilaProjection([+d.long, +d.lat])[0])
    .attr('cy', d => abilaProjection([+d.long, +d.lat])[1])
    .attr('r', 3.5)
    .transition().duration(900).delay((_, i) => i * 5)
    .style('opacity', 0.65).style('fill', d => mapcolor(d.id));
}

function dateOnChange(input) {
  date = new Date(input.value);
  date = new Date(+date + date.getTimezoneOffset() * 60000);
  plotData = {};
  selected_cars.forEach(sc => { plotData[sc] = gdc[date.getDate()][sc]; });
  mapdata = [];
  Object.values(plotData).forEach(pts => pts.forEach(p => mapdata.push(p)));
  mapdata.sort(sortByTime);
  if (mapdata.length > 0) {
    timeMinMax.min = new Date(mapdata[0].Timestamp);
    timeMinMax.max = new Date(mapdata[mapdata.length - 1].Timestamp);
  }
  plotGPS();
}

function dragstarted() {}
function dragged() {}
function dragended() {}
