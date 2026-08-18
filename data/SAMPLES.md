# 样本数据说明（data/）

本目录存放**小体积样本**，用于「基础数据处理 / 教学演示」直接在样本上跑，
无需加载全量原始数据。全量数据体积过大（北京 ~523MB / 深圳 ~2.2GB / 无锡 ~382MB），
已通过 `.gitignore` 屏蔽在 `raw/` 中，**不进仓库、不推送**。

## 样本文件

| 文件 | 行数 | 体积 | 字段 |
|------|------|------|------|
| `beijing_sample.csv`   | 50 | ~2 KB | `taxi_id,timestamp,lon,lat` |
| `shenzhen_sample.csv`  | 50 | ~2 KB | `trajectory_id,date,lon,lat,passenger,speed(km/h)` |
| `wuxi_sample.csv`      | 50 | ~5 KB | `id,经度,纬度,采集时间,方向,速度,纵向加速度,横向加速度,垂直加速度,横摆角速度` |

> 样本行数少（仅 50 行）是为了前端页面内联展示与轻量演示；
> 想做更充分的本地分析，见下方「重新生成更大的样本」。

## 全量数据在哪里

全量原始数据在仓库根目录的 `raw/`（已被 `.gitignore` 忽略）：

```
raw/
├── beijing/                      北京 T-Drive：8911 个 txt（每车一个轨迹文件）
├── shenzhen/                     深圳：24 个每小时 CSV（单日切片）
└── wuxi/                         无锡：31 个 zip（含 20200718.csv 已解包）+ 20200718.csv
```

这些文件**只存在于本地**，用于离线复算、抽更大样本、或重新生成图表；
推送到 GitHub 时会被 `.gitignore` 整体排除，因此仓库始终保持小巧、不触发
GitHub 的单文件 100MB / 仓库 ~1GB 限制。

## 重新生成样本（可复现）

脚本 `scripts/make_samples.py` 从 `raw/` 全量数据抽取代表性样本写入 `data/`：

```bash
# 直接用全量数据重新生成（覆盖 data/ 下样本）
python scripts/make_samples.py

# 先试跑到别的目录，确认无误再覆盖
SAMPLE_OUT=/tmp/preview python scripts/make_samples.py
```

生成逻辑：
- **北京**：取前 3 辆车（`1.txt`~`3.txt`），每车前 50 个点。
- **深圳**：取出租车 `22223` 的记录（跨每小时 CSV 抽取，前 50 条）。
- **无锡**：取 `20200718.csv` 前 50 行（保留首列 `id` 后的制表符混合分隔符）。

## 关于「仓库内提交的精选样本」

`data/*_sample.csv` 当前是**手工精选、且与对应数据集页（datasets/*.html）
内联表格严格对应**的版本——前端运行时验证（`verify_taxi_site.js`）会做
「CSV 前 5 行须出现在页面表格中」的交叉校验。

若用本脚本重新生成并覆盖，样本内容会按「文件顺序」抽取，可能与页面表格不一致，
导致验证未通过。此时有两种处理：
1. 保持仓库内已提交的精选样本不变（推荐，页面与验证均稳定）；
2. 重新生成后，同步更新 `datasets/*.html` 中的样本表格，再重跑验证脚本。

## 基础处理示例（无需全量）

```python
import pandas as pd

# 北京：看一辆车的轨迹点
bj = pd.read_csv("data/beijing_sample.csv")
print(bj["taxi_id"].value_counts())

# 深圳：载客率
sz = pd.read_csv("data/shenzhen_sample.csv")
print("载客比例:", (sz["passenger"] == 1).mean())

# 无锡：注意首列 id 后带制表符，按 [\t,] 切分
wx = pd.read_csv("data/wuxi_sample.csv")
print(wx.head())
```
