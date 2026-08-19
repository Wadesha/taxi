// 全站运行时验证：jsdom 加载每个 HTML，断言结构/内容，并校验内部链接与图片存在性。
// 用法: node scripts/verify_taxi_site.js
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("C:/Users/wade/.workbuddy/binaries/node/workspace/node_modules/jsdom");

const ROOT = "C:/Users/wade/Documents/taxi";
const pages = [
  "index.html",
  "guide/gps.html", "guide/sensing.html", "guide/trajectory.html",
  "datasets/beijing.html", "datasets/shenzhen.html", "datasets/wuxi.html",
  "datasets/simulation.html", "datasets/taxonomy.html",
  "analysis/overview.html", "analysis/trajectory.html", "analysis/od.html", "analysis/hotspot.html",
  "methodology/pipeline.html", "methodology/deploy.html",
];

let pass = 0, fail = 0;
const errors = [];

function check(cond, msg) {
  if (cond) pass++;
  else { fail++; errors.push(msg); }
}

function walk(dir) {
  let out = new Set();
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (e.name === ".git" || e.name === "raw") continue;
      out = new Set([...out, ...walk(p)]);
    } else out.add(p);
  }
  return out;
}
const allFiles = walk(ROOT);

for (const rel of pages) {
  const file = path.join(ROOT, rel);
  const html = fs.readFileSync(file, "utf-8");
  const dom = new JSDOM(html, { runScripts: "dangerously", resources: "usable" });
  const { document } = dom.window;
  const title = document.title;
  check(title && title.trim().length > 4, `${rel}: title 为空或过短`);

  // 内部链接可解析
  for (const a of document.querySelectorAll("a[href]")) {
    const href = a.getAttribute("href");
    if (/^(https?:|mailto:|data:|#)/.test(href)) continue;
    const target = path.normalize(path.join(path.dirname(file), href.split("#")[0]));
    check(allFiles.has(target) || fs.existsSync(target), `${rel}: 坏链 ${href}`);
  }
  // 图片存在
  for (const img of document.querySelectorAll("img[src]")) {
    const src = img.getAttribute("src");
    if (/^(https?:|data:)/.test(src)) continue;
    const target = path.normalize(path.join(path.dirname(file), src));
    check(fs.existsSync(target), `${rel}: 缺图 ${src}`);
  }

  if (rel === "datasets/taxonomy.html") {
    check(document.querySelectorAll(".tax-card").length === 17, "taxonomy: 应恰好 17 张卡片");
    check(document.querySelectorAll("svg").length === 2, "taxonomy: 应有 2 个 SVG（框架+痕迹）");
    for (const c of ["A", "B", "C", "D", "E", "F"]) {
      check(document.querySelector(`h3#cat-${c}`) !== null, `taxonomy: 缺类别段 ${c}`);
    }
    check(document.querySelectorAll("table.bigtable tbody tr").length === 17, "taxonomy: 大对照表应 17 行");
    for (const img of ["tax_cat_coverage.png", "tax_sampling.png", "tax_spatial.png"]) {
      check(fs.existsSync(path.join(ROOT, "assets/img", img)), `taxonomy: 缺图 ${img}`);
    }
  }
  if (rel === "guide/sensing.html") {
    for (const kw of ["GNSS", "误差", "上报链路", "采样间隔", "WGS-84", "GCJ-02", "BD-09", "隐私"]) {
      check(html.includes(kw), `sensing: 缺关键词 ${kw}`);
    }
    check(document.querySelectorAll("svg").length >= 1, "sensing: 应有 SVG 图");
    check(document.querySelectorAll("table.mat").length >= 3, "sensing: 应有 3+ 张表");
  }
}

console.log(`\n结果: ${pass} 项通过, ${fail} 项失败 (页面 ${pages.length})`);
if (errors.length) {
  console.log("\n失败项:");
  errors.forEach(e => console.log("  ✗ " + e));
  process.exit(1);
}
console.log("全站验证通过 ✔");
