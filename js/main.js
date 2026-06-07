// Location index registry — assigns stable IDs to each location
var location_index = {};

const LOCATIONS = [
  "Abila Airport", "Abila Scrapyard", "Abila Zacharo", "Ahaggo Museum",
  "Albert's Fine Clothing", "Bean There Done That", "Brew've Been Served",
  "Brewed Awakenings", "Carlyle Chemical Inc.", "Chostus Hotel",
  "Coffee Cameleon", "Coffee Shack", "Daily Dealz", "Desafio Golf Course",
  "Frank's Fuel", "Frydos Autosupply n' More", "Gelatogalore",
  "General Grocer", "Guy's Gyros", "Hallowed Grounds", "Hippokampos",
  "Jack's Magical Beans", "Kalami Kafenion", "Katerina's Cafe",
  "Kronos Mart", "Kronos Pipe and Irrigation", "Maximum Iron and Steel",
  "Nationwide Refinery", "Octavio's Office Supplies", "Ouzeri Elian",
  "Roberts and Sons", "Shoppers' Delight", "Stewart and Sons Fabrication",
  "U-Pump"
];

document.addEventListener('DOMContentLoaded', () => {
  LOCATIONS.forEach((name, i) => { location_index[name] = `loc${i + 1}`; });
});
