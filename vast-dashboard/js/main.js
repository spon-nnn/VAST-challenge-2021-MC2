// ============================================================
// main.js v2 — 全局状态管理 & 跨图表联动（清爽学术风配色）
// ============================================================

// ── 地点列表 & 索引 ──
var location_list = [
    "Abila Airport", "Abila Scrapyard", "Abila Zacharo", "Ahaggo Museum",
    "Albert's Fine Clothing", "Bean There Done That", "Brew've Been Served",
    "Brewed Awakenings", "Carlyle Chemical Inc.", "Chostus Hotel",
    "Coffee Cameleon", "Coffee Shack", "Daily Dealz", "Desafio Golf Course",
    "Frank's Fuel", "Frydos Autosupply n' More", "Gelatogalore",
    "General Grocer", "Guy's Gyros", "Hallowed Grounds", "Hippokampos",
    "Jack's Magical Beans", "Kalami Kafenion", "Katerina's Cafe",
    "Kronos Mart", "Kronos Pipe and Irrigation", "Maximum Iron and Steel",
    "Nationwide Refinery", "Octavio's Office Supplies", "Ouzeri Elian",
    "Roberts and Sons", "Shoppers' Delight", "Stewart and Sons Fabrication", "U-Pump"
];

var location_index = {};

document.addEventListener('DOMContentLoaded', function () {
    convertLocation();
});

function convertLocation() {
    for (var i = 0; i < location_list.length; i++) {
        location_index[location_list[i]] = "loc" + (i + 1);
    }
}

// ── 地点分类颜色映射（清爽学术风） ──
var loctype = {
    "Abila Airport": "Travel and Accommodation",
    "Abila Scrapyard": "Miscellaneous",
    "Abila Zacharo": "Miscellaneous",
    "Ahaggo Museum": "Travel and Accommodation",
    "Albert's Fine Clothing": "Retail",
    "Bean There Done That": "Food and Beverage",
    "Brew've Been Served": "Food and Beverage",
    "Brewed Awakenings": "Food and Beverage",
    "Carlyle Chemical Inc.": "Industrial",
    "Chostus Hotel": "Travel and Accommodation",
    "Coffee Cameleon": "Food and Beverage",
    "Coffee Shack": "Food and Beverage",
    "Daily Dealz": "Retail",
    "Desafio Golf Course": "Travel and Accommodation",
    "Frank's Fuel": "Miscellaneous",
    "Frydos Autosupply n' More": "Retail",
    "Gelatogalore": "Food and Beverage",
    "General Grocer": "Retail",
    "Guy's Gyros": "Food and Beverage",
    "Hallowed Grounds": "Food and Beverage",
    "Hippokampos": "Food and Beverage",
    "Jack's Magical Beans": "Food and Beverage",
    "Kalami Kafenion": "Food and Beverage",
    "Katerina's Cafe": "Food and Beverage",
    "Kronos Mart": "Retail",
    "Kronos Pipe and Irrigation": "Industrial",
    "Maximum Iron and Steel": "Industrial",
    "Nationwide Refinery": "Industrial",
    "Octavio's Office Supplies": "Retail",
    "Ouzeri Elian": "Food and Beverage",
    "Roberts and Sons": "Miscellaneous",
    "Shoppers' Delight": "Retail",
    "Stewart and Sons Fabrication": "Miscellaneous",
    "U-Pump": "Miscellaneous"
};

// 新配色：食品=红、零售=靛蓝、工业=翠绿、旅行=青、杂项=紫
var colorMap = {
    "Food and Beverage": "#ef4444",
    "Retail": "#6366f1",
    "Industrial": "#10b981",
    "Travel and Accommodation": "#06b6d4",
    "Miscellaneous": "#8b5cf6"
};

// ── 全局选中状态 ──
var selected_cars = [];
var selected_location = null;
var selected_cc = null;

// ── 车辆颜色数组 ──
var colorArray = [
    '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
    '#06b6d4', '#ec4899', '#6366f1', '#14b8a6', '#f97316',
    '#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed',
    '#0891b2', '#db2777', '#4f46e5', '#0d9488', '#ea580c',
    '#1d4ed8', '#b91c1c', '#047857', '#b45309', '#6d28d9',
    '#0e7490', '#be185d', '#4338ca', '#0f766e', '#c2410c',
    '#1e40af', '#991b1b', '#065f46', '#92400e', '#5b21b6',
    '#155e75', '#9d174d', '#3730a3', '#115e59', '#9a3412',
    '#1e3a8a', '#7f1d1d', '#064e3b', '#78350f', '#4c1d95',
    '#164e63', '#831843', '#312e81', '#134e4a', '#7c2d12',
];

// 所有 car ID
var allCarIds = [];
for (var i = 1; i <= 35; i++) allCarIds.push(i);
[101, 104, 105, 106, 107].forEach(function (v) { allCarIds.push(v); });

var mapcolor = d3.scaleOrdinal().domain(allCarIds).range(colorArray);

// ── 事件总线 ──
var eventBus = {
    _listeners: {},
    on: function (event, callback) {
        if (!this._listeners[event]) this._listeners[event] = [];
        this._listeners[event].push(callback);
    },
    emit: function (event, data) {
        if (!this._listeners[event]) return;
        this._listeners[event].forEach(function (cb) { cb(data); });
    }
};

// ── 日期工具 ──
function parseDateMDY(str) {
    var parts = str.split(" ")[0].split("/");
    return new Date(+parts[2], +parts[0] - 1, +parts[1]);
}

function fmtDate(date) {
    var y = date.getFullYear();
    var m = String(date.getMonth() + 1).padStart(2, "0");
    var d = String(date.getDate()).padStart(2, "0");
    return y + "-" + m + "-" + d;
}
