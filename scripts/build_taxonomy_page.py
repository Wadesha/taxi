# -*- coding: utf-8 -*-
"""构建 datasets/taxonomy.html —— 交通时空数据「家族」全景图鉴。

消费 data/sim/modes/manifest_modes.json + 17 个 CSV，生成自包含页面：
- 六维分类框架（A 连续点轨迹 / B 行程起止 / C 刷卡事件 / D 断面检测 / E 聚合衍生 / F 其他模态）
- 一图看懂：同一次出行，六类数据各留下什么「痕迹」
- 3 张 matplotlib 图表：分类覆盖 / 采样间隔谱 / 空间精度谱
- 17 张卡片（按类别分组）：能回答 / 不能回答 / 典型陷阱 / 字段 / 真实参照 / 样本 / 下载
- 一张 17 行大对照表
所有图表标签用英文，规避 CJK 字体缺失。
"""
import os, json, csv, math, random
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# 中文字体配置（Win 自带 SimHei/微软雅黑；不设则中文乱码为方块）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

ROOT = r"C:\Users\wade\Documents\taxi"
SIM = os.path.join(ROOT, "data", "sim", "modes")
IMG = os.path.join(ROOT, "assets", "img")
OUT = os.path.join(ROOT, "datasets", "taxonomy.html")

manifest = json.load(open(os.path.join(SIM, "manifest_modes.json"), encoding="utf-8"))

# ---------- 类别元信息 ----------
CATS = {
    "A": ("连续点轨迹", "Continuous point trajectories",
          "车载/手持终端<b>逐点上报</b>：每个时刻一个坐标点，串起来就是轨迹。", "#2563eb"),
    "B": ("行程起止记录", "OD / trip records",
          "只有<b>起点和终点</b>（OD），中间轨迹根本不存在。", "#16a085"),
    "C": ("刷卡与事件", "Tap-in / events",
          "离散的<b>刷卡或交易事件</b>，按个体卡号配对还原出行。", "#d35400"),
    "D": ("断面固定检测", "Fixed sensors",
          "设备<b>守在固定断面</b>，数经过的车或人，不区分个体。", "#7c3aed"),
    "E": ("聚合衍生", "Aggregated products",
          "已经<b>脱敏统计好的成品</b>：速度指数、网格 OD 等。", "#db2777"),
    "F": ("其他模态与粗定位", "Other modalities",
          "船舶 AIS、手机信令等<b>非陆路 / 粗定位</b>数据。", "#0284c7"),
}
CAT_ORDER = ["A", "B", "C", "D", "E", "F"]

# 采样间隔（秒，名义值）与空间精度（米，名义值）用于图表
SAMPLING_S = {
    "a1_taxi_gps": 30, "a2_ridehail_order": 20, "a3_bus_gps": 35, "a4_truck_freight": 180, "a5_ebike_share": 15,
    "b1_dockless_bike_trip": 600, "b2_docked_bike_trip": 600, "b3_taxi_meter_trip": 600,
    "c1_metro_afc": 5, "c2_bus_ic_onboard": 5,
    "d1_loop_detector": 300, "d2_anpr_camera": 1, "d3_etc_gantry": 1,
    "e1_link_speed": 300, "e2_grid_od_flow": 3600,
    "f1_ship_ais": 120, "f2_pedestrian_signal": 600,
}
SPATIAL_M = {
    "a1_taxi_gps": 5, "a2_ridehail_order": 5, "a3_bus_gps": 8, "a4_truck_freight": 12, "a5_ebike_share": 5,
    "b1_dockless_bike_trip": 5, "b2_docked_bike_trip": 300, "b3_taxi_meter_trip": 5,
    "c1_metro_afc": 300, "c2_bus_ic_onboard": 300,
    "d1_loop_detector": 1, "d2_anpr_camera": 1, "d3_etc_gantry": 1,
    "e1_link_speed": 30, "e2_grid_od_flow": 500,
    "f1_ship_ais": 500, "f2_pedestrian_signal": 300,
}

def read_rows(path, n=6):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        r = csv.reader(f); header = next(r)
        for row in r:
            rows.append(row)
            if len(rows) >= n: break
    return header, rows

# ---------- 1. 图表：分类覆盖 ----------
counts = {c: sum(1 for m in manifest if m["cat"] == c) for c in CAT_ORDER}
fig, ax = plt.subplots(figsize=(6.4, 3.2))
xs = [f"{c} {CATS[c][0]}" for c in CAT_ORDER]
ys = [counts[c] for c in CAT_ORDER]
cols = ["#2563eb", "#16a085", "#d35400", "#7c3aed", "#db2777", "#0284c7"]
bars = ax.bar(xs, ys, color=cols, edgecolor="white", linewidth=0.4)
for b, v in zip(bars, ys):
    ax.text(b.get_x()+b.get_width()/2, v+0.05, str(v), ha="center", va="bottom", fontsize=11, fontweight="bold")
ax.set_ylabel("样本数据集数")
ax.set_title("六类交通数据各覆盖多少种样本（共 17 个）")
ax.set_ylim(0, max(ys)+1)
plt.xticks(rotation=20, ha="right", fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(IMG, "tax_cat_coverage.png"), dpi=110); plt.close(fig)

# ---------- 2. 图表：采样间隔谱（线性；log+barh 在 matplotlib 会塌缩） ----------
def k(file):  # manifest 的 file 带 .csv 后缀，去掉再查表
    return file[:-4] if file.endswith(".csv") else file
items = sorted(manifest, key=lambda m: SAMPLING_S.get(k(m["file"]), 1))
fig, ax = plt.subplots(figsize=(7.6, 6.0))
labels = [m["title"] for m in items]
vals = [SAMPLING_S.get(k(m["file"]), 1) for m in items]
colors = [CATS[m["cat"]][3] for m in items]
bars = ax.barh(range(len(items)), vals, color=colors, edgecolor="white", linewidth=0.4)
ax.set_yticks(range(len(items))); ax.set_yticklabels(labels, fontsize=9)
ax.set_xlabel("名义采样间隔（秒，线性）")
ax.set_title("时间采样间隔谱：采样越粗，能做的分析越受限")
ax.invert_yaxis()
# 数值标签：放在条形右端外侧
xmax = max(vals)
ax.set_xlim(0, xmax * 1.18)
for bar, v in zip(bars, vals):
    label = f"{v}s" if v < 60 else (f"{v//60}min" if v < 3600 else f"{v//3600}h")
    ax.text(bar.get_width() + xmax * 0.012, bar.get_y() + bar.get_height() / 2,
            label, va="center", fontsize=8.5, color="#444")
legend = [Patch(facecolor=CATS[c][3], label=f"{c} {CATS[c][0]}") for c in CAT_ORDER]
ax.legend(handles=legend, fontsize=8, loc="lower right")
ax.grid(axis="x", alpha=0.25)
fig.tight_layout(); fig.savefig(os.path.join(IMG, "tax_sampling.png"), dpi=110); plt.close(fig)

# ---------- 3. 图表：空间精度谱（线性） ----------
items2 = sorted(manifest, key=lambda m: SPATIAL_M.get(k(m["file"]), 1))
fig, ax = plt.subplots(figsize=(7.6, 6.0))
labels2 = [m["title"] for m in items2]
vals2 = [max(SPATIAL_M.get(k(m["file"]), 1), 1) for m in items2]
colors2 = [CATS[m["cat"]][3] for m in items2]
bars2 = ax.barh(range(len(items2)), vals2, color=colors2, edgecolor="white", linewidth=0.4)
ax.set_yticks(range(len(items2))); ax.set_yticklabels(labels2, fontsize=9)
ax.set_xlabel("名义空间精度（米，线性；D 类固定检测≈1m 即点位）")
ax.set_title("空间精度谱：精度越粗，越看不到个体路径")
ax.invert_yaxis()
xmax2 = max(vals2)
ax.set_xlim(0, xmax2 * 1.20)
for bar, v in zip(bars2, vals2):
    label = f"{v}m（点位）" if v <= 1 else (f"{v}m（站点）" if v == 300 else f"{v}m")
    ax.text(bar.get_width() + xmax2 * 0.012, bar.get_y() + bar.get_height() / 2,
            label, va="center", fontsize=8.5, color="#444")
ax.legend(handles=legend, fontsize=8, loc="lower right")
ax.grid(axis="x", alpha=0.25)
fig.tight_layout(); fig.savefig(os.path.join(IMG, "tax_spatial.png"), dpi=110); plt.close(fig)

# ---------- SVG：一图看懂「同一次出行，六类数据各留下什么痕迹」 ----------
def road_curve(t):
    x = 28 + 206 * t
    y = 78 + 26 * math.sin(t * 3.1) + 10 * math.sin(t * 6.7 + 0.6)
    return x, y

def road_points(n=26):
    return [road_curve(i / (n - 1)) for i in range(n)]

def panel_svg(cat, title, ox, oy):
    """生成单个面板的内层 SVG 内容（不含外框）。"""
    pts = road_points()
    inner = []
    # 背景路（浅灰虚线，所有面板一致，代表「真实发生过的那条路」）
    d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    inner.append(f'<path d="{d}" fill="none" stroke="#cbd2d9" stroke-width="2" '
                 f'stroke-dasharray="4 4" opacity="0.6"/>')
    if cat == "A":
        for (x, y) in pts[::2]:
            inner.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="#2563eb"/>')
        inner.append(f'<text x="150" y="150" text-anchor="middle" font-size="11" fill="#2563eb">'
                     f'密密麻麻的坐标点串成轨迹</text>')
    elif cat == "B":
        sx, sy = pts[1]; ex, ey = pts[-2]
        inner.append(f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" '
                     f'stroke="#16a085" stroke-width="2" stroke-dasharray="5 4"/>')
        inner.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="5" fill="#16a085"/>')
        inner.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="5" fill="#16a085"/>')
        inner.append(f'<text x="{sx:.1f}" y="{sy-9:.1f}" text-anchor="middle" font-size="10" fill="#16a085">起点</text>')
        inner.append(f'<text x="{ex:.1f}" y="{ey-9:.1f}" text-anchor="middle" font-size="10" fill="#16a085">终点</text>')
        inner.append(f'<text x="150" y="150" text-anchor="middle" font-size="11" fill="#16a085">只有 OD，中间是黑箱</text>')
    elif cat == "C":
        sx, sy = pts[1]; ex, ey = pts[-2]
        inner.append(f'<rect x="{sx-7:.1f}" y="{sy-7:.1f}" width="14" height="14" rx="2" fill="#d35400"/>')
        inner.append(f'<rect x="{ex-7:.1f}" y="{ey-7:.1f}" width="14" height="14" rx="2" fill="#d35400"/>')
        inner.append(f'<text x="{sx:.1f}" y="{sy+20:.1f}" text-anchor="middle" font-size="9" fill="#d35400">进</text>')
        inner.append(f'<text x="{ex:.1f}" y="{ey+20:.1f}" text-anchor="middle" font-size="9" fill="#d35400">出</text>')
        inner.append(f'<text x="150" y="150" text-anchor="middle" font-size="11" fill="#d35400">两次刷卡事件，路径靠推断</text>')
    elif cat == "D":
        for t in (0.2, 0.5, 0.8):
            x, y = road_curve(t)
            inner.append(f'<line x1="{x:.1f}" y1="{y-12:.1f}" x2="{x:.1f}" y2="{y+12:.1f}" stroke="#7c3aed" stroke-width="2.5"/>')
            inner.append(f'<circle cx="{x:.1f}" cy="{y-12:.1f}" r="3" fill="#7c3aed"/>')
        inner.append(f'<text x="150" y="150" text-anchor="middle" font-size="11" fill="#7c3aed">断面上数车，不知道是谁</text>')
    elif cat == "E":
        seg = 8
        for i in range(seg):
            x0, y0 = road_curve(i / seg)
            x1, y1 = road_curve((i + 1) / seg)
            # 用红(慢)->绿(快)模拟拥堵梯度
            r = int(220 - 160 * (i / seg)); g = int(60 + 160 * (i / seg)); b = 60
            col = f"rgb({r},{g},{b})"
            inner.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
                         f'stroke="{col}" stroke-width="4"/>')
        inner.append(f'<text x="150" y="150" text-anchor="middle" font-size="11" fill="#db2777">路段被染成红/绿，个体已抹去</text>')
    elif cat == "F":
        # 粗网格 + 经过的格子高亮 + 模糊团
        cell = 46
        for gx in range(0, 240, cell):
            for gy in range(0, 132, cell):
                inner.append(f'<rect x="{gx}" y="{gy}" width="{cell}" height="{cell}" fill="none" stroke="#e3e8ee" stroke-width="1"/>')
        cx = sum(x for x, y in pts) / len(pts)
        cy = sum(y for x, y in pts) / len(pts)
        inner.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="34" fill="#0284c7" opacity="0.18"/>')
        inner.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="18" fill="#0284c7" opacity="0.28"/>')
        inner.append(f'<text x="150" y="150" text-anchor="middle" font-size="11" fill="#0284c7">几百米精度的模糊团</text>')
    # 外框与标题
    frame = (f'<g transform="translate({ox},{oy})">'
             f'<rect x="0" y="0" width="280" height="170" rx="12" fill="#fff" stroke="{CATS[cat][3]}" stroke-width="1.5"/>'
             f'<rect x="0" y="0" width="280" height="26" rx="12" fill="{CATS[cat][3]}"/>'
             f'<rect x="0" y="13" width="280" height="13" fill="{CATS[cat][3]}"/>'
             f'<text x="14" y="18" font-size="12" font-weight="bold" fill="#fff">{cat} · {title}</text>'
             f'<g transform="translate(14,32)">' + "".join(inner) + '</g>'
             f'</g>')
    return frame

traces_panels = []
grid_pos = [(20, 30), (320, 30), (620, 30), (20, 220), (320, 220), (620, 220)]
for i, c in enumerate(CAT_ORDER):
    # 每个类别取第一个数据集作为代表
    rep = next(m for m in manifest if m["cat"] == c)
    traces_panels.append(panel_svg(c, rep["title"], grid_pos[i][0], grid_pos[i][1]))
traces_svg = (
    '<svg viewBox="0 0 920 420" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="同一次出行六类数据痕迹对比">'
    + "".join(traces_panels) +
    '</svg>'
)

# ---------- SVG：六维分类框架 ----------
fw_blocks = []
for i, c in enumerate(CAT_ORDER):
    name, en, desc, col = CATS[c]
    x = 20 + (i % 3) * 300
    y = 20 + (i // 3) * 110
    examples = "、".join(m["carrier"] for m in manifest if m["cat"] == c)[:40]
    fw_blocks.append(
        f'<g transform="translate({x},{y})">'
        f'<rect x="0" y="0" width="280" height="92" rx="12" fill="#fff" stroke="{col}" stroke-width="1.5"/>'
        f'<rect x="0" y="0" width="8" height="92" rx="4" fill="{col}"/>'
        f'<text x="20" y="24" font-size="13" font-weight="bold" fill="{col}">{c} · {name}</text>'
        f'<text x="20" y="40" font-size="9.5" fill="#8794a6">{en}</text>'
        f'<text x="20" y="58" font-size="10" fill="#4a5568">{desc}</text>'
        f'<text x="20" y="80" font-size="9.5" fill="#7b8794">例：{examples}</text>'
        f'</g>'
    )
fw_svg = (
    '<svg viewBox="0 0 920 235" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="六维分类框架">'
    + "".join(fw_blocks) +
    '</svg>'
)

# ---------- 卡片 HTML ----------
def cat_section(cat):
    name, en, desc, col = CATS[cat]
    members = [m for m in manifest if m["cat"] == cat]
    cards = []
    for m in members:
        header, rows = read_rows(os.path.join(SIM, m["file"]), 6)
        th = "".join(f"<th>{h}</th>" for h in header)
        trs = ""
        for row in rows:
            tds = "".join(f"<td>{c if c != '' else '<span class=miss>∅</span>'}</td>" for c in row)
            trs += f"<tr>{tds}</tr>"
        cards.append(f"""
        <article class="tax-card" style="border-left:4px solid {col}">
          <div class="tax-head">
            <h4>{m['title']}</h4>
            <a class="dl" href="../data/sim/modes/{m['file']}" download>下载 CSV</a>
          </div>
          <div class="tax-meta">
            <span><b>载体</b> {m['carrier']}</span>
            <span><b>结构</b> {m['structure']}</span>
            <span><b>粒度</b> {m['granularity']}</span>
          </div>
          <div class="tax-grid">
            <div class="can"><b>✅ 能回答</b><p>{m['can']}</p></div>
            <div class="cannot"><b>⛔ 不能回答</b><p>{m['cannot']}</p></div>
          </div>
          <p class="pit"><b>⚠️ 典型陷阱</b> {m['pitfall']}</p>
          <p class="fields"><b>字段</b> {m['fields']}</p>
          <p class="ref"><b>真实参照</b> {m['realref']}</p>
          <div class="table-wrap"><table class="sample"><thead><tr>{th}</tr></thead>
            <tbody>{trs}</tbody></table></div>
          <div class="cap">样本前 6 行（完整文件见上方下载）。</div>
        </article>""")
    return f"""
    <section class="cat-block">
      <h3 id="cat-{cat}" style="color:{col}">{cat} · {name} <span class="en">{en}</span></h3>
      <p class="cat-desc">{desc}</p>
      <div class="tax-gridwrap">{''.join(cards)}</div>
    </section>"""

# ---------- 大对照表 ----------
def cell(text):
    return f"<td>{text}</td>"

rows_tbl = ""
for m in manifest:
    col = CATS[m["cat"]][2]
    rows_tbl += (
        f"<tr><td><span class='dot' style='background:{col}'></span>{m['cat']}</td>"
        f"<td><b>{m['title']}</b><br/><span class='muted'>{m['carrier']}</span></td>"
        f"{cell(m['granularity'])}{cell(m['can'])}{cell(m['cannot'])}"
        f"{cell(m['pitfall'])}{cell(m['realref'])}</tr>")

# ---------- 组合 HTML ----------
charts_html = """
  <div class="chart-row">
    <figure><img src="../assets/img/tax_cat_coverage.png" alt="分类覆盖"/><figcaption>六类数据各覆盖多少种样本</figcaption></figure>
  </div>
  <div class="chart-row">
    <figure><img src="../assets/img/tax_sampling.png" alt="采样间隔谱"/><figcaption>时间采样越粗，能做的分析越受限（对数轴）</figcaption></figure>
    <figure><img src="../assets/img/tax_spatial.png" alt="空间精度谱"/><figcaption>空间精度越粗，越看不到个体路径（对数轴）</figcaption></figure>
  </div>"""

cat_sections_html = "\n".join(cat_section(c) for c in CAT_ORDER)

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>交通时空数据家族 · 六类与 17 种典型数据集</title>
<meta name="description" content="出租车 GPS 只是交通时空数据这一大类里较全面的一种。本页用六维分类框架 + 17 个模拟数据集，把出租车、网约车、公交、单车、地铁、卡口、AIS、手机信令等典型交通数据的结构、能回答/不能回答的问题、典型陷阱与真实参照一次讲清。" />
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
    <span>交通时空数据家族</span>
  </div>

  <span class="section-eyebrow" style="color:var(--guide);">数据集 · 家族图鉴</span>
  <h1>交通时空数据家族：不止出租车</h1>
  <p>
    你手里的北京、深圳、无锡出租车数据非常好，但它们只是<b>「交通时空数据」这一大类里<b>比较全面</b>的一种</b>——
    属于「A 连续点轨迹」里的「出租车」这一个分支。现实里还有网约车、公交、共享单车、地铁刷卡、卡口、ETC、
    船舶 AIS、手机信令……它们长得完全不一样，能回答的问题也天差地别。
  </p>
  <p>
    这一页做三件事：① 用<b>六维分类框架</b>把整个家族铺开；② 用<b>一张对比图</b>说明同一次出行在不同数据里留下什么痕迹；
    ③ 用 <b>17 个模拟数据集</b>（覆盖六类）逐一告诉你：它长什么样、<b>能回答什么、不能回答什么、有什么典型陷阱</b>、对标哪个真实数据集。
    把它当成你接任何一份新交通数据前的「选型和避坑手册」。
  </p>

  <div class="callout note">
    <span class="icon">🧭</span>
    <div><b>怎么读这页：</b>先记住六类（A~F）的<strong>结构差异</strong>，再看 17 张卡片里每类的「能回答 / 不能回答」——
    这两个字段决定了一份数据<strong>到底能做什么分析</strong>。同一座城市，换了数据源，能做的题目可能从「路径还原」直接掉到「只有断面流量」。</div>
  </div>

  <hr/>
  <h2>一、六维分类框架</h2>
  <p class="muted">按「数据是怎么产生的」分成六类。出租车 GPS 占 A 类一格；其余五类与出租车思路完全不同。</p>
  __FW__

  <hr/>
  <h2>二、同一次出行，六类数据各留下什么痕迹</h2>
  <p>下面六个面板是<strong>同一条路、同一次出行</strong>。注意：左边 A 能看到完整轨迹，越往右数据越「稀疏/聚合」，
    到 F 类只剩下一团几百米精度的模糊影子——这正是一份数据<b>能回答什么</b>的根本原因。</p>
  <div class="svg-wrap">__TRACES__</div>
  <div class="cap">图例：灰色虚线=真实发生过的路；彩色=该类数据实际记录到的内容。</div>

  <hr/>
  <h2>三、三张谱：覆盖 / 采样间隔 / 空间精度</h2>
  <p class="muted">出租车类数据往往「采样密、精度高」；越往聚合/粗定位走，分析自由度越低。</p>
  __CHARTS__

  <hr/>
  <h2>四、17 种典型数据集（按类别分组）</h2>
  <p class="muted">每张卡：载体 / 结构 / 粒度 → 能回答 → 不能回答 → 典型陷阱 → 字段 → 真实参照 → 样本 → 下载。</p>
  __SECTIONS__

  <hr/>
  <h2>五、一张大对照表（17 行速查）</h2>
  <div class="table-wrap" style="overflow-x:auto;">
  <table class="bigtable">
    <thead><tr>
      <th>类</th><th>数据集</th><th>粒度</th><th>能回答</th><th>不能回答</th><th>典型陷阱</th><th>真实参照</th>
    </tr></thead>
    <tbody>__ROWS__</tbody>
  </table></div>

  <hr/>
  <h2>六、怎么用这份家族图鉴</h2>
  <ul>
    <li><b>选型前</b>：拿到一份新数据，先问「它属于 A~F 哪一类？」——类别直接决定可分析性。</li>
    <li><b>写需求前</b>：对照每类的「不能回答」，提前砍掉做不到的分析题目，避免白做。</li>
    <li><b>接数据前</b>：读「典型陷阱」，把清洗和校验规则先列出来（如公交只刷上车的 OD 半空、ETC 只覆盖高速……）。</li>
    <li><b>教学/练手</b>：17 个 CSV 是轻量练习数据，比几个 G 真实数据更适合跑通管线。</li>
  </ul>
  <div class="why">
    <span class="icon">🧩</span>
    <div>本项目的北京/深圳/无锡出租车数据 = A 类的「富样本」参照；其余 16 种模拟数据集则把交通数据的<b>其他分支与典型坑</b>单独造出来给你看。读懂家族，再看真实数据就知道该先查哪里。</div>
  </div>

  <div style="display:flex;gap:12px;flex-wrap:wrap;margin:30px 0;">
    <a class="btn ghost" href="../index.html">← 返回主页</a>
    <a class="btn" href="../datasets/simulation.html">数据质量「毛病」图鉴 →</a>
    <a class="btn ghost" href="../guide/sensing.html">数据怎么被采集 →</a>
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

html = (html.replace("__FW__", fw_svg)
            .replace("__TRACES__", traces_svg)
            .replace("__CHARTS__", charts_html)
            .replace("__SECTIONS__", cat_sections_html)
            .replace("__ROWS__", rows_tbl))

extra_css = """
<style>
.tax-gridwrap{display:grid;grid-template-columns:1fr;gap:18px;margin-top:10px}
.cat-block h3 .en{font-weight:400;font-size:.8em;color:var(--text-muted)}
.cat-desc{color:var(--text-soft)}
.tax-card{border:1px solid var(--border);border-radius:14px;padding:16px 18px;background:var(--card);margin-bottom:4px}
.tax-head{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
.tax-head h4{margin:0;font-size:1.02rem}
.tax-meta{display:flex;flex-wrap:wrap;gap:6px 14px;margin:8px 0;font-size:.82rem;color:var(--text-soft)}
.tax-meta b{color:var(--text)}
.tax-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:8px 0}
.tax-grid .can,.tax-grid .cannot{padding:8px 10px;border-radius:10px;font-size:.85rem}
.tax-grid .can{background:color-mix(in srgb,var(--wuxi) 12%,transparent)}
.tax-grid .cannot{background:color-mix(in srgb,var(--beijing) 10%,transparent)}
.tax-grid p{margin:4px 0 0}
.pit{font-size:.86rem;margin:8px 0 4px}
.fields{font-size:.8rem;color:var(--text-soft);margin:4px 0}
.ref{font-size:.82rem;color:var(--text-soft);margin:4px 0 10px}
.dl{font-size:.78rem;padding:4px 10px;border:1px solid var(--border);border-radius:8px;color:var(--accent);text-decoration:none;white-space:nowrap}
.sample{font-size:.74rem}
.sample td,.sample th{white-space:nowrap;padding:3px 7px}
.cap{font-size:.74rem;color:var(--text-muted);margin-top:6px}
.svg-wrap{border:1px solid var(--border);border-radius:12px;background:var(--bg-elev);padding:10px}
.bigtable{font-size:.8rem}
.bigtable td,.bigtable th{vertical-align:top;padding:6px 9px}
.bigtable .dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px}
.muted{color:var(--text-muted)}
.miss{color:#ef4444;font-weight:bold}
.chart-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px;margin:14px 0}
.chart-row figure{margin:0}
.chart-row img{width:100%;border:1px solid var(--border);border-radius:10px}
.chart-row figcaption{font-size:.78rem;color:var(--text-soft);text-align:center;margin-top:4px}
.callout.note,.why{border-left:3px solid var(--guide);background:var(--bg-muted);padding:12px 14px;border-radius:8px;margin:14px 0}
.why{display:flex;gap:10px;align-items:flex-start}
.why .icon{font-size:1.2rem}
.btn{display:inline-block;padding:8px 16px;border-radius:10px;background:var(--accent);color:#fff;font-weight:600}
.btn.ghost{background:transparent;border:1px solid var(--border);color:var(--accent)}
</style>"""
html = html.replace("</head>", extra_css + "\n</head>")

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print(f"已生成 {OUT}")
print(f"类别段: {len(CAT_ORDER)}  卡片: {len(manifest)}  对照表行: {len(manifest)}")
