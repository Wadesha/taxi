# -*- coding: utf-8 -*-
"""构建 datasets/simulation.html：模拟数据集图鉴。
读取 data/sim/manifest.json + 12 个 CSV，生成自包含页面：
- 介绍"轨迹数据"这类数据的家族与可能出现的全部情况
- 将北京/深圳/无锡定位为"真实且较全面"的参照
- 12 张卡片：描述 + 影响 + 检测规则 + 样本表 + 下载
- 3 张 matplotlib 图表（越界散点 / 常量传感器 / 零速分布）
"""
import os, json, csv, random
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = r"C:\Users\wade\Documents\taxi"
SIM = os.path.join(ROOT, "data", "sim")
IMG = os.path.join(ROOT, "assets", "img")
OUT = os.path.join(ROOT, "datasets", "simulation.html")

manifest = json.load(open(os.path.join(SIM, "manifest.json"), encoding="utf-8"))
# 每个数据集的检测规则
DETECT = {
    "sim_comprehensive.csv": "各字段非空、坐标落在城市范围内、时间戳单调递增 → 通过。",
    "sim_minimal.csv": "只有 id/时间/经纬度，无法计算速度/载客；用之前先确认够不够。",
    "sim_missing.csv": "筛选 lon/lat 为空的行；缺失率 = 空行数 / 总行数。",
    "sim_out_of_range.csv": "过滤 lat∈[-90,90] 且 lon∈[73,135]（中国陆域大致范围）外的点。",
    "sim_constant_sensor.csv": "对行驶行检查 IMU 列的方差；方差=0 即常量占位，整列丢弃。",
    "sim_zero_speed.csv": "统计 speed=0 占比；过高则速度分析不可信，只做停泊分析。",
    "sim_sparse.csv": "相邻点时间间隔的中位数/最大值；间隔过大处轨迹会失真。",
    "sim_mixed_delim.csv": "按行 split(',') 后看首字段是否仍含 '\\t'；解析前先 strip。",
    "sim_timestamp_chaos.csv": "尝试多种格式解析，解析失败即异常；统一为 datetime。",
    "sim_dup_points.csv": "按 (id, 时间, 经纬度) 去重；统计重复行占比。",
    "sim_passenger_missing.csv": "passenger 为空/非 0/1 即异常；载客率按有效行计算。",
    "sim_cross_midnight.csv": "切分行程前先按时间连续性判断，避免被自然日截断。",
}

def read_rows(path, n=6, mixed=False):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        if mixed:
            header = f.readline().replace("\t", " ").strip().split(",")
            for line in f:
                cells = line.rstrip("\n").split(",")
                cells[0] = cells[0].replace("\t", "")
                rows.append(cells)
                if len(rows) >= n: break
        else:
            r = csv.reader(f)
            header = next(r)
            for row in r:
                rows.append(row)
                if len(rows) >= n: break
    return header, rows

# ---- 生成 3 张图表 ----
plt.rcParams["font.size"] = 11

# 1. 越界散点
p = os.path.join(SIM, "sim_out_of_range.csv")
xs, ys, bad = [], [], []
with open(p, encoding="utf-8") as f:
    r = csv.reader(f); next(r)
    for row in r:
        try:
            lon, lat = float(row[2]), float(row[3])
        except: continue
        xs.append(lon); ys.append(lat)
        bad.append(not (-90 <= lat <= 90 and 73 <= lon <= 135))
fig, ax = plt.subplots(figsize=(6.4, 4.2))
ax.scatter([x for x,b in zip(xs,bad) if not b],[y for y,b in zip(ys,bad) if not b], c="#2563eb", s=28, label="Normal")
ax.scatter([x for x,b in zip(xs,bad) if b],[y for y,b in zip(ys,bad) if b], c="#ef4444", s=48, marker="x", label="Out-of-range")
ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude"); ax.set_title("Out-of-range points (red X outside valid bounds)")
ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(IMG,"sim_outofrange.png"), dpi=110); plt.close(fig)

# 2. 常量传感器
p = os.path.join(SIM, "sim_constant_sensor.csv")
axv = []
with open(p, encoding="utf-8") as f:
    r = csv.reader(f); next(r)
    for row in r:
        try: axv.append(float(row[6]))
        except: pass
fig, ax = plt.subplots(figsize=(6.4, 3.6))
ax.plot(range(len(axv)), axv, c="#7c3aed", lw=2)
ax.set_title("Constant sensor: accel_x fixed at 1202 (placeholder, no info)")
ax.set_xlabel("Record #"); ax.set_ylabel("accel_x")
fig.tight_layout(); fig.savefig(os.path.join(IMG,"sim_constantsensor.png"), dpi=110); plt.close(fig)

# 3. 零速分布
p = os.path.join(SIM, "sim_zero_speed.csv")
sp = []
with open(p, encoding="utf-8") as f:
    r = csv.reader(f); next(r)
    for row in r:
        try: sp.append(float(row[5]))
        except: pass
fig, ax = plt.subplots(figsize=(6.4, 3.6))
ax.bar(range(len(sp)), sp, color=["#ef4444" if v==0 else "#16a085" for v in sp])
ax.set_title("Zero-speed dominant: red = speed 0 (parked)")
ax.set_xlabel("Record #"); ax.set_ylabel("speed (km/h)")
fig.tight_layout(); fig.savefig(os.path.join(IMG,"sim_zerospeed.png"), dpi=110); plt.close(fig)

# ---- 构建 HTML ----
cards = []
for m in manifest:
    fname = m["file"]
    header, rows = read_rows(os.path.join(SIM, fname), 6, mixed=(fname=="sim_mixed_delim.csv"))
    th = "".join(f"<th>{h}</th>" for h in header)
    trs = ""
    for row in rows:
        tds = "".join(f"<td>{c if c!='' else '<span class=miss>∅</span>'}</td>" for c in row)
        trs += f"<tr>{tds}</tr>"
    is_ref = fname == "sim_comprehensive.csv"
    tag = '<span class="sim-flag ref">真实参照</span>' if is_ref else '<span class="sim-flag">模拟演示</span>'
    detect = DETECT.get(fname, "")
    cards.append(f"""
    <article class="sim-card{' ref' if is_ref else ''}">
      <div class="sim-head">
        <h3>{m['title']} {tag}</h3>
        <a class="dl" href="../data/sim/{fname}" download>下载 CSV</a>
      </div>
      <p class="desc">{m['desc']}</p>
      <p class="impact"><b>对分析的影响：</b>{m['impact']}</p>
      <p class="detect"><b>怎么检测：</b>{detect}</p>
      <div class="table-wrap"><table class="sample"><thead><tr>{th}</tr></thead>
        <tbody>{trs}</tbody></table></div>
      <div class="cap">样本前 6 行（完整文件见上方下载）。</div>
    </article>""")

cards_html = "\n".join(cards)

# 图表卡片
charts = """
    <div class="chart-row">
      <figure><img src="../assets/img/sim_outofrange.png" alt="越界坐标散点"/><figcaption>越界坐标：红叉点跑出合理范围</figcaption></figure>
      <figure><img src="../assets/img/sim_constantsensor.png" alt="常量传感器"/><figcaption>常量传感器：IMU 恒为定值</figcaption></figure>
      <figure><img src="../assets/img/sim_zerospeed.png" alt="零速分布"/><figcaption>零速主导：大量速度为 0</figcaption></figure>
    </div>"""

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>模拟数据集图鉴 · 轨迹数据可能出现的全部情况</title>
<meta name="description" content="用 12 个模拟数据集，逐一演示 GPS/出租车轨迹数据中可能出现的各种情况：缺失、越界、常量传感器、稀疏、混合分隔符等。" />
<link rel="stylesheet" href="../assets/css/style.css" />
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%237c3aed'/%3E%3Ctext x='16' y='22' font-size='18' text-anchor='middle' fill='white' font-family='Arial' font-weight='bold'%3E%E2%9A%99%3C/text%3E%3C/svg%3E" />
</head>
<body>
<header class="site-header"><div class="container">
  <nav class="nav" aria-label="主导航">
    <a class="brand" href="../index.html"><span class="brand-mark" aria-hidden="true"></span><span>轨迹数据分析</span></a>
    <div class="nav-links">
      <a href="../index.html">主页</a>
      <a href="../guide/gps.html">基础概念</a>
      <a href="../index.html#datasets">数据集</a>
      <a href="../analysis/overview.html">分析</a>
      <a href="../methodology/pipeline.html">方法</a>
    </div>
    <button class="theme-toggle" aria-label="切换主题">☾</button>
  </nav>
</div></header>

<main><div class="container-narrow">
  <div class="crumbs">
    <a href="../index.html">主页</a><span class="sep">/</span>
    <a href="../index.html#datasets">数据集</a><span class="sep">/</span>
    <span>模拟数据集图鉴</span>
  </div>

  <span class="section-eyebrow" style="color:var(--datasets);">数据集 · 模拟图鉴</span>
  <h1>模拟数据集图鉴：这类数据可能出哪些问题</h1>
  <p>
    出租车/GPS 轨迹数据不是一种数据，而是一<strong>类</strong>数据——它们的字段、采样、质量千差万别。
    你手里的北京、深圳、无锡，只是现实中三种"比较全面、质量尚可"的样本。
    但当你去接新的数据源时，可能会遇到各种各样的情况：字段不全、坐标越界、传感器是占位常量、时间戳乱七八糟……
  </p>
  <p>
    这一页用 <strong>12 个小型模拟数据集</strong>，把这类数据<strong>所有可能出问题的情况都造了一份样本</strong>，
    逐一告诉你：它长什么样、为什么会出现、对分析有什么影响、怎么检测。把它当成一份"接数据前的体检清单"。
  </p>

  <div class="callout note">
    <span class="icon">📍</span>
    <div>
      <strong>北京 / 深圳 / 无锡 = 真实且较全面的参照。</strong>
      它们字段多、覆盖广，所以本项目拿它们当"正例"。图鉴里 <span class="sim-flag ref">真实参照</span> 那张卡
      就是"理想状态"的样子；其余 <span class="sim-flag">模拟演示</span> 的卡片，则是把各种"毛病"单独拆出来给你看。
      读懂这些毛病，再看真实数据时你就知道该先查哪里。
    </div>
  </div>

  <hr/>
  <h2>先看三张典型"毛病"的图</h2>
  __CHARTS__

  <hr/>
  <h2>12 张卡片：逐一过一遍</h2>
  <p class="muted">每张卡：这是什么情况 → 对分析的影响 → 怎么检测 → 样本前 6 行 → 完整 CSV 下载。</p>
  <div class="sim-grid">
  __CARDS__
  </div>

  <hr/>
  <h2>怎么用这份图鉴</h2>
  <ul>
    <li><strong>接新数据前</strong>：对照这 12 种情况，先问"它会不会有越界/缺失/常量/时间戳问题"，再动手。</li>
    <li><strong>清洗时</strong>：每张卡的"怎么检测"就是对应的清洗规则，可直接写成代码。</li>
    <li><strong>教学时</strong>：把模拟 CSV 当成练习数据，比直接用几个 G 的真实数据更轻、更快。</li>
  </ul>
  <div class="why">
    <span class="icon">🧭</span>
    <div>这些方法不是凭空想的，而是从本项目真实数据里提炼的：无锡的常量 IMU、跨省份越界、混合分隔符，
    北京的重复点，深圳的零速占比——都已在各数据集详情页和数据质量分析里实锤。模拟数据只是把它们单独放大给你看。</div>
  </div>

  <div style="display:flex;gap:12px;flex-wrap:wrap;margin:30px 0;">
    <a class="btn ghost" href="../index.html">← 返回主页</a>
    <a class="btn" href="../guide/trajectory.html">基础：数据质量四维度 →</a>
  </div>
</div></main>

<footer class="site-footer"><div class="container"><div class="row">
  <div>出租车轨迹数据分析 · 从 GPS 到分析</div>
  <div>数据归各自来源所有 · 代码 MIT</div>
</div></div></footer>
<button class="to-top" aria-label="返回顶部">↑</button>
<script src="../assets/js/main.js"></script>
</body>
</html>"""

html = html.replace("__CHARTS__", charts).replace("__CARDS__", cards_html)

# 注入一些样式（追加到 style.css 之外，这里用内联 <style> 不影响现有文件）
extra_css = """
<style>
.sim-grid{display:grid;grid-template-columns:1fr;gap:18px;margin-top:10px}
.sim-card{border:1px solid var(--border);border-radius:14px;padding:18px 20px;background:var(--card)}
.sim-card.ref{border-color:var(--guide);box-shadow:0 0 0 2px color-mix(in srgb,var(--guide) 25%,transparent)}
.sim-head{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
.sim-head h3{margin:0;font-size:1.05rem}
.sim-card .desc{margin:10px 0 6px;color:var(--text)}
.sim-card .impact{margin:6px 0;font-size:.92rem}
.sim-card .detect{margin:6px 0 12px;font-size:.9rem;color:var(--text-soft)}
.dl{font-size:.8rem;padding:4px 10px;border:1px solid var(--border);border-radius:8px;color:var(--accent);text-decoration:none}
.sample{font-size:.78rem}
.sample td,.sample th{white-space:nowrap;padding:3px 8px}
.cap{font-size:.75rem;color:var(--text-soft);margin-top:6px}
.miss{color:#ef4444;font-weight:bold}
.chart-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;margin:14px 0}
.chart-row figure{margin:0}
.chart-row img{width:100%;border:1px solid var(--border);border-radius:10px}
.chart-row figcaption{font-size:.78rem;color:var(--text-soft);text-align:center;margin-top:4px}
.muted{color:var(--text-soft)}
</style>"""
html = html.replace("</head>", extra_css + "\n</head>")

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"已生成 {OUT}")
print(f"卡片数: {len(manifest)}  图表: 3 张")
