# 出租车轨迹数据分析 · Static Site

[![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue?logo=github)](https://pages.github.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Static Site](https://img.shields.io/badge/Type-Static%20Site-brightgreen)](https://developer.mozilla.org/en-US/docs/Glossary/Static_site_generator)

> 面向 **北京 / 深圳 / 无锡** 三座城市的出租车 GPS 轨迹数据可视化与分析项目，
> 整理为一个可直接部署到 **GitHub Pages** 的体系化纯静态站点。

## ✨ 项目亮点

- 🏙️ **三城对照** — 北京 T-Drive 2008、深圳 2014、无锡（含 9 维惯性信号）三个公开数据集
- 📖 **从基础讲起** — GPS、经纬度、WGS-84、轨迹字段、采样间隔、数据质量通病
- 📊 **真实数据 + 模拟演示** — 能用真实数据的地方用真实数据；体系缺位处用模拟图填充并明确标注
- 🖼️ **图片灯箱 / 表格分页 / 主题切换** — 原生 JS 交互，零依赖
- 🌓 **深浅主题** — CSS 变量驱动，跟随系统偏好
- 📱 **响应式** — 桌面 / 平板 / 手机自适应
- 🚀 **GitHub Pages 友好** — 纯静态、无构建、相对路径

## 📂 目录结构

```
.
├── index.html                  # 主页：总览 + 4 步学习路径
├── guide/                      # 📖 基础概念
│   ├── gps.html                # GPS 与经纬度
│   ├── sensing.html            # 数据是怎么被采集的（GNSS 原理/误差/上报链路/隐私）
│   └── trajectory.html         # 轨迹数据与字段
├── datasets/                   # 🗂️ 数据集详情
│   ├── beijing.html            # 北京 T-Drive 2008
│   ├── shenzhen.html           # 深圳 2014
│   ├── wuxi.html               # 无锡（含惯性信号与数据质量观察）
│   ├── taxonomy.html           # 🧭 交通时空数据家族图鉴（六类框架 + 17 种典型数据集）
│   └── simulation.html         # 🧪 模拟数据集图鉴（12 种数据质量问题演示）
├── analysis/                   # 🔬 分析方法与结果
│   ├── overview.html           # 跨城综合对比
│   ├── trajectory.html         # 轨迹形态与空间分布
│   ├── od.html                 # OD 出行矩阵（模拟演示）
│   └── hotspot.html            # 热点识别（模拟演示）
├── methodology/                # 🛠️ 复现与部署
│   ├── pipeline.html           # 数据管线：解压 → 解析 → 清洗 → 分析 → 可视化
│   └── deploy.html             # GitHub Pages 部署指南
├── assets/
│   ├── css/style.css           # 体系化样式
│   ├── js/main.js              # 主题切换 / 灯箱 / 分页 / 返回顶部
│   └── img/                    # 分析图（真实数据 + 模拟演示）
├── data/
│   ├── summary.json            # 三城字段与规模概要
│   ├── 三城 50 行真实样本 CSV
│   ├── SAMPLES.md              # 样本说明与再生成方式
│   └── sim/                    # 🧪 12 个质量模拟 CSV + manifest.json
│       └── modes/              # 🧭 17 个家族模拟 CSV + manifest_modes.json（六类交通数据）
├── scripts/                    # Python 可复现脚本
│   ├── extract_rar.py          # 解压北京 RAR
│   ├── visualize_taxi_data.py  # 原始综合可视化
│   ├── generate_supplement_charts.py  # 补充真实数据图 + 模拟图
│   ├── make_samples.py         # 从全量数据生成样本
│   ├── make_sim_datasets.py    # 生成 12 个模拟数据集
│   ├── build_simulation_page.py# 构建模拟数据集图鉴页
│   ├── make_mode_datasets.py   # 生成 17 个跨模态交通数据集（A~F 六类）
│   ├── build_taxonomy_page.py  # 构建交通数据家族图鉴页
│   ├── restructure_archive.py  # 全量数据重组/分片
│   └── analyze_cleanable.py    # 可清理数据量化分析
├── raw/                        # ⚠️ 原始大数据（已迁归档仓库 taxi-archive*，.gitignore 排除）
├── docs/                       # 原始数据说明文档
└── README.md
```

## 🧭 交通数据家族图鉴（重要）

`datasets/taxonomy.html` 把「出租车 GPS」放回它的大家庭：交通时空数据可分成 **六类（A~F）**——
A 连续点轨迹 / B 行程起止 / C 刷卡事件 / D 断面检测 / E 聚合衍生 / F 其他模态与粗定位。
页面用 **17 个模拟数据集**（`data/sim/modes/*.csv`）覆盖六类典型情况（出租车、网约车、公交、货车、共享单车、
有桩单车、计价器、地铁 AFC、公交刷卡、线圈、卡口、ETC、速度指数、网格 OD、船舶 AIS、手机信令……），
每张卡给出：载体 / 结构 / 粒度 → 能回答 → 不能回答 → 典型陷阱 → 字段 → 真实参照 → 样本 → CSV 下载。
另附六维分类框架图、「同一次出行六类痕迹」对比图、采样间隔谱与空间精度谱，以及 17 行大对照表。
配套 `guide/sensing.html` 讲清底层采集原理：GNSS 定位、四类误差源、车载上报链路、采样间隔决定分析能力、五种定位技术、坐标偏移、隐私脱敏四层级。

## 🧪 模拟数据集图鉴

`datasets/simulation.html` 用 **12 个小型模拟数据集**（`data/sim/*.csv`）逐一演示 GPS/出租车轨迹数据
**所有可能出问题的情况**：仅位置、缺失坐标、越界坐标、常量传感器（IMU 占位）、零速主导、稀疏采样、
混合分隔符、时间戳混乱、重复点、载客缺失、跨日轨迹，并以「北京式全面数据」作为真实参照。
每张卡给出：现象 → 对分析的影响 → 检测规则 → 样本 → CSV 下载。适合作为**接新数据前的体检清单**和教学练习数据。

## 🗂️ 数据集

| 城市 | 数据集 | 时间 | 规模 | 字段数 | 典型用途 | 数据质量注意 |
|------|--------|------|------|--------|----------|--------------|
| 北京 | T-Drive 2008 | 2008-02-02 ~ 02-08 | 10,357 辆 / 8,911 文件 | 4 (id, ts, lon, lat) | 轨迹挖掘、OD 估算、聚类基线 | 无载客/速度字段；有重复点、时间缺失 |
| 深圳 | 深圳 2014 | 2014-10-22 (单日) | 24 CSV / 约 4700 万行 | 6 (+ passenger, speed) | 空驶/载客行为、速度画像、拥堵 | 时间字段无日期；少量越界坐标 |
| 无锡 | 无锡 2020 | 2020-07-18 起（README 写 2022） | 32 文件 / 约 250 MB | 10 (+ 方向/速度/三轴加速度/横摆角速度) | 低速/驻车行为、数据画像教学 | 范围覆盖全国；行驶段 IMU 为常量填充，驾驶行为分析需谨慎 |

数据归各自来源所有，使用前请遵守对应许可证条款。

## 🚀 本地预览

```bash
# Python 3
python -m http.server 8767

# 或 Node.js
npx serve .
```

打开 <http://localhost:8767> 即可访问。
**注意**：不要直接双击 `index.html`（`file://` 协议下部分资源会被浏览器拦截）。

## 📦 部署到 GitHub Pages

```bash
# 1. 在项目根目录初始化并提交
git init
git add .
git commit -m "init: taxi trajectory analysis site"

# 2. 关联并推送到你的仓库
git branch -M main
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git push -u origin main

# 3. 在 GitHub 仓库 Settings → Pages 选择 main / root
# 4. 等待约 1 分钟，访问 https://YOUR_USER.github.io/YOUR_REPO/
```

原始大数据已写入 `.gitignore`，不会进入仓库。
详细步骤见站点内 [方法页 · 部署到 GitHub Pages](./methodology/deploy.html)。

## 🛠️ 技术栈

- **数据处理**：Python 3.10+ · pandas · matplotlib · numpy · 7-Zip
- **前端**：原生 HTML5 + CSS3 + JavaScript（无 npm、无构建）
- **托管**：GitHub Pages
- **字体**：系统默认（PingFang SC / Microsoft YaHei / Segoe UI）

## 📜 许可证

本项目代码以 [MIT](./LICENSE) 许可证发布。
数据归各自原始来源所有，使用前请阅读对应的数据使用条款。

## 🙏 致谢

- 微软亚洲研究院 T-Drive 项目组 — 提供北京轨迹数据
- 各公开数据集发布者
- 全部图表由 Python (pandas + matplotlib) 生成
