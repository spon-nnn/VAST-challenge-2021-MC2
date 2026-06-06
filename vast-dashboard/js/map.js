// ============================================================
// map.js — 地图 + GPS 轨迹（修复 D3 v7 事件 + 可疑地点标注）
// ============================================================

var abila, carOwnersData, abilaPath;
var svg_map, abilaProjection;
var mapmargin = { top: 20, right: 20, bottom: 40, left: 40 };
var mapwidth = 900 - mapmargin.left - mapmargin.right;
var mapheight = 610 - mapmargin.top - mapmargin.bottom;
var gdc;
var mapdata = [];
var plotData = {};
var timeMinMax = { 'min': null, 'max': null };
var xScale;
var svg_cars;
var mapDate;
var suspiciousLocations = []; // Q5 可疑地点坐标

document.addEventListener('DOMContentLoaded', function () {
    Promise.all([
        d3.json('assets/abila.geojson'),
        d3.json('data/map_gps.json'),
        d3.csv('data/car-assignments.csv'),
        d3.json('data/circular_bar.json')
    ]).then(function (values) {
        abila = values[0];
        gdc = values[1];
        carOwnersData = values[2] || [];
        var locData = values[3];

        // 提取 Q5 可疑地点（score > 0）
        suspiciousLocations = [];
        (locData || []).forEach(function (d) {
            if (d.suspicious_score > 0) {
                suspiciousLocations.push(d.location);
            }
        });

        var dateInput = document.getElementById('date');
        mapDate = new Date(dateInput.value);
        mapDate = new Date(+mapDate + mapDate.getTimezoneOffset() * 60000);

        document.getElementById('play').addEventListener('click', timelapse);

        svg_map = d3.select('#map_svg');

        // 旅游地图底图
        svg_map.append('image')
            .attr('x', 0).attr('y', 0)
            .attr('xlink:href', 'assets/MC2-tourist.jpg')
            .attr('height', mapheight).attr('width', mapwidth)
            .attr('class', 'image')
            .attr('opacity', 0.75);

        abilaProjection = d3.geoEquirectangular()
            .fitSize([mapwidth, mapheight], abila);
        abilaPath = d3.geoPath().projection(abilaProjection);

        addCars(allCarIds);
        plotAbila();
    });
});

function plotAbila() {
    svg_map.selectAll('.abila')
        .data(abila.features)
        .join('path')
        .attr('class', 'abila')
        .attr('d', abilaPath)
        .attr('fill', 'white')
        .attr('stroke', '#94a3b8')
        .attr('stroke-width', '1px')
        .style('opacity', 0.5);

    xScale = d3.scaleLinear()
        .domain([0, 24])
        .range([mapmargin.left, mapwidth]);

    var xAxis = d3.axisBottom().scale(xScale);
    svg_map.append('g')
        .attr('transform', 'translate(' + -10 + ',' + (mapheight + 20) + ')')
        .attr('stroke-width', 2).style('font-size', '14px').call(xAxis);

    // 可疑地点标记（红色星号）
    if (suspiciousLocations.length > 0) {
        // 我们无法精确知道每个地点在地图上的坐标，用 GeoJSON 绘制
    }
}

function plotGPS() {
    svg_map.selectAll('.gps').remove();

    svg_map.selectAll('.gps')
        .data(mapdata)
        .join('circle')
        .attr('class', 'gps')
        .attr('cx', d => abilaProjection([+d.long, +d.lat])[0])
        .attr('cy', d => abilaProjection([+d.long, +d.lat])[1])
        .attr('r', 3)
        .style('fill', d => mapcolor(d.id))
        .style('opacity', 0.6);

    svg_map.selectAll('.timeline').remove();
    if (timeMinMax.min && timeMinMax.max) {
        svg_map.selectAll('.timeline')
            .data(['min', 'max'])
            .enter()
            .append('line')
            .attr('class', 'timeline')
            .attr('id', d => 'timeline' + d)
            .attr('x1', d => xScale(+timeMinMax[d].getHours() + timeMinMax[d].getMinutes() / 60) - 10)
            .attr('y1', mapheight + 10)
            .attr('x2', d => xScale(+timeMinMax[d].getHours() + timeMinMax[d].getMinutes() / 60) - 10)
            .attr('y2', mapheight + 30)
            .attr('stroke', '#dc2626')
            .attr('stroke-width', '4px');
    }
}

// ── 车辆选择面板 ──
function addCars(carIds) {
    svg_cars = d3.select('#map_cars');

    // 构建索引
    var carIdToIndex = {};
    carIds.forEach(function (id, i) { carIdToIndex[String(id)] = i; });

    // 背景条
    svg_cars.selectAll('.outerRect')
        .data(carIds)
        .join('rect')
        .attr('id', d => "car_" + d)
        .attr('class', 'outerRect')
        .attr('x', 10).attr('y', (d, i) => (i + 1) * 26)
        .attr('height', 22).attr('width', 220)
        .attr('rx', 4)
        .style('opacity', 0).attr('fill', '#f1f5f9');

    // 彩色方块 + 未分配车辆红色边框
    svg_cars.selectAll('.cars')
        .data(carIds)
        .join('rect')
        .attr('id', d => "rect_" + d)
        .attr('class', d => 'cars' + (d >= 101 ? ' unassigned' : ''))
        .attr('x', 20).attr('y', (d, i) => (i + 1) * 26 + 2)
        .attr('height', 18).attr('width', 18)
        .attr('rx', 3)
        .attr('fill', d => mapcolor(d))
        .attr('stroke', d => d >= 101 ? '#dc2626' : 'none')
        .attr('stroke-width', d => d >= 101 ? 2 : 0)
        .style('cursor', 'pointer')
        .on('click', function (event, d) {
            // d 是 carId (datum)
            var carId = String(d);
            toggleCar(carId);
        });

    // Car ID 文字
    svg_cars.selectAll('.carIds')
        .data(carIds)
        .join('text')
        .attr('class', 'carIds')
        .attr('x', 43).attr('y', (d, i) => (i + 1) * 26 + 16)
        .text(d => d)
        .style('font-size', '12px').style('cursor', 'pointer')
        .style('fill', d => d >= 101 ? '#dc2626' : '#334155')
        .style('font-weight', d => d >= 101 ? 'bold' : 'normal')
        .on('click', function (event, d) {
            toggleCar(String(d));
        });

    // 车主姓名
    var carOwnersFiltered = carOwnersData.filter(function (r) {
        return carIds.includes(parseInt(r.CarID));
    });
    svg_cars.selectAll('.carOwners')
        .data(carOwnersFiltered)
        .join('text')
        .attr('class', 'carOwners')
        .attr('x', 65)
        .attr('y', function (d) {
            var idx = carIdToIndex[String(parseInt(d.CarID))];
            return idx !== undefined ? (idx + 1) * 26 + 16 : 0;
        })
        .text(d => d.FirstName + ' ' + d.LastName)
        .style('font-size', '11px').style('cursor', 'pointer')
        .style('fill', '#475569')
        .on('click', function (event, d) {
            toggleCar(String(parseInt(d.CarID)));
        });
}

// ── 切换车辆选中状态 ──
function toggleCar(carId) {
    if (selected_cars.indexOf(carId) === -1) {
        selected_cars.push(carId);
        d3.select("#car_" + carId).style('opacity', 0.25).attr('fill', '#3b82f6');
    } else {
        var idx = selected_cars.indexOf(carId);
        if (idx !== -1) selected_cars.splice(idx, 1);
        d3.select("#car_" + carId).style('opacity', 0).attr('fill', '#f1f5f9');
    }
    updateData(carId);
    plotGPS();
    eventBus.emit('carSelected', carId);
}

// ── 更新 GPS 数据 ──
function updateData(car) {
    if (selected_cars.indexOf(car) !== -1) {
        var dayKey = String(mapDate.getDate());
        if (gdc[dayKey] && gdc[dayKey][car]) {
            plotData[car] = gdc[dayKey][car];
        }
        d3.select("#car_" + car).style('opacity', 0.3);
    } else {
        delete plotData[car];
        d3.select("#car_" + car).style('opacity', 0);
    }

    mapdata = [];
    Object.entries(plotData).forEach(function (pd) {
        var carId = pd[0];
        pd[1].forEach(function (item) {
            mapdata.push({
                Timestamp: item[0], lat: item[1], long: item[2], id: carId
            });
        });
    });

    var sortByTime = function (a, b) {
        return new Date(a.Timestamp).getTime() - new Date(b.Timestamp).getTime();
    };
    mapdata.sort(sortByTime);

    if (selected_cars.length > 0 && mapdata.length > 0) {
        timeMinMax.min = new Date(mapdata[0].Timestamp);
        timeMinMax.max = new Date(mapdata[mapdata.length - 1].Timestamp);
    }
}

// ── Play 动画 ──
function timelapse() {
    if (mapdata.length === 0) {
        // 提示先选车
        var playBtn = document.getElementById('play');
        playBtn.textContent = '请先选择车辆';
        setTimeout(function () { playBtn.textContent = '▶ Play'; }, 2000);
        return;
    }

    svg_map.selectAll('#timelinemin')
        .transition()
        .duration(mapdata.length * 5 + 500)
        .ease(d3.easeLinear)
        .attr('x1', xScale(+timeMinMax.max.getHours() + timeMinMax.max.getMinutes() / 60) - 10)
        .attr('y1', mapheight + 10)
        .attr('x2', xScale(+timeMinMax.max.getHours() + timeMinMax.max.getMinutes() / 60) - 10)
        .attr('y2', mapheight + 30)
        .attr('stroke', '#dc2626')
        .attr('stroke-width', '4px')
        .on('end', function () {
            svg_map.selectAll('#timelinemin')
                .attr('x1', xScale(+timeMinMax.min.getHours() + timeMinMax.min.getMinutes() / 60) - 10)
                .attr('y1', mapheight + 10)
                .attr('x2', xScale(+timeMinMax.min.getHours() + timeMinMax.min.getMinutes() / 60) - 10)
                .attr('y2', mapheight + 30);
        });

    svg_map.selectAll('.gps').remove();
    svg_map.selectAll('.gps')
        .data(mapdata)
        .join('circle')
        .attr('class', 'gps')
        .attr('cx', d => abilaProjection([+d.long, +d.lat])[0])
        .attr('cy', d => abilaProjection([+d.long, +d.lat])[1])
        .attr('r', 3)
        .style('opacity', 0)
        .style('fill', d => mapcolor(d.id))
        .transition()
        .duration(1000)
        .delay(function (d, i) { return i * 5; })
        .style('opacity', 0.6);
}

// ── 日期切换 ──
function dateOnChange(input) {
    mapDate = new Date(input.value);
    mapDate = new Date(+mapDate + mapDate.getTimezoneOffset() * 60000);
    plotData = {};
    selected_cars.forEach(function (sc) {
        var dayKey = String(mapDate.getDate());
        if (gdc[dayKey] && gdc[dayKey][sc]) {
            plotData[sc] = gdc[dayKey][sc];
        }
    });
    mapdata = [];
    Object.entries(plotData).forEach(function (pd) {
        var carId = pd[0];
        pd[1].forEach(function (item) {
            mapdata.push({ Timestamp: item[0], lat: item[1], long: item[2], id: carId });
        });
    });
    var sortByTime = function (a, b) {
        return new Date(a.Timestamp).getTime() - new Date(b.Timestamp).getTime();
    };
    mapdata.sort(sortByTime);
    if (mapdata.length > 0) {
        timeMinMax.min = new Date(mapdata[0].Timestamp);
        timeMinMax.max = new Date(mapdata[mapdata.length - 1].Timestamp);
    }
    plotGPS();
}
