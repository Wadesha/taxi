# -*- coding: utf-8 -*-
"""生成一组"模拟出租车轨迹数据集"，逐一演示这类 GPS/轨迹数据中
可能出现的各种情况。每个数据集 30-60 行，带明确缺陷标记。
输出: data/sim/*.csv  +  data/sim/manifest.json（供页面展示用）
只生成文件，不改动任何现有数据。"""
import os, json, random, math

random.seed(20260819)
OUT = r"C:\Users\wade\Documents\taxi\data\sim"
os.makedirs(OUT, exist_ok=True)

def fmt(v, nd=6):
    if v is None: return ""
    return f"{v:.{nd}f}"

def write_csv(name, header, rows, mixed=False):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8", newline="") as f:
        if mixed:
            # 混合分隔符: 第一列后跟 \t，其余用 ,
            f.write("\t, ".join(header) + "\n")
            for r in rows:
                cells = [str(c) for c in r]
                f.write("\t, ".join(cells) + "\n")
        else:
            f.write(",".join(header) + "\n")
            for r in rows:
                f.write(",".join(str(c) for c in r) + "\n")
    return path

# 基础轨迹生成：在中心点附近游走
def walk(n, lon0, lat0, step=0.0008, dt=10):
    pts = []
    lon, lat = lon0, lat0
    t = 0
    for i in range(n):
        lon += random.uniform(-step, step)
        lat += random.uniform(-step, step)
        pts.append((lon, lat, t))
        t += dt
    return pts

manifest = []

# 1. 北京式全面数据（真实参照）
def d_comprehensive():
    rows = []
    base = walk(40, 116.40, 39.90)
    for i, (lon, lat, t) in enumerate(base):
        sp = round(random.uniform(0, 60), 1)
        ps = 1 if sp > 5 and i % 3 == 0 else 0
        rows.append([f"京A{i%5:03d}", f"2008-02-02 12:{i:02d}:00", fmt(lon), fmt(lat), ps, sp, round(random.uniform(0,359),1)])
    write_csv("sim_comprehensive.csv",
              ["taxi_id","timestamp","lon","lat","passenger","speed_kmh","heading"], rows)
    return ("sim_comprehensive","全面(真实参照)","字段完整：id/时间/经纬度/载客/速度/航向，无明显缺陷。北京 T-Drive + 深圳 2014 属此类。","正常数据几乎零缺陷；用它对照下面各种'毛病'。")

# 2. 仅位置（T-Drive 式最小字段）
def d_minimal():
    rows = []
    base = walk(40, 116.40, 39.90)
    for i, (lon, lat, t) in enumerate(base):
        rows.append([f"T{i%8:04d}", f"2008-02-02 12:{i:02d}:00", fmt(lon), fmt(lat)])
    write_csv("sim_minimal.csv", ["taxi_id","timestamp","lon","lat"], rows)
    return ("sim_minimal","仅位置(最小字段)","只有 id/时间/经纬度，没有载客/速度/航向。北京 T-Drive 原始释放即如此。","能做的分析受限：只能看轨迹形状，无法算 OD/速度/载客率。")

# 3. 缺失坐标
def d_missing():
    rows = []
    base = walk(40, 114.06, 22.54)
    for i, (lon, lat, t) in enumerate(base):
        if i in (5, 12, 23, 31):  # 注入缺失
            rows.append([f"S{i%6:03d}", f"2014-10-22 12:{i:02d}:00", "", "", 0, 0.0])
        else:
            rows.append([f"S{i%6:03d}", f"2014-10-22 12:{i:02d}:00", fmt(lon), fmt(lat), 0, round(random.uniform(0,40),1)])
    write_csv("sim_missing.csv", ["taxi_id","timestamp","lon","lat","passenger","speed_kmh"], rows)
    return ("sim_missing","缺失坐标","部分行经纬度为空（GPS 信号丢失/解析失败）。","缺失点会让轨迹'断线'，需插值或丢弃该段。占比越高越难修复。")

# 4. 越界坐标
def d_out_of_range():
    rows = []
    base = walk(40, 114.06, 22.54)
    for i, (lon, lat, t) in enumerate(base):
        if i in (10, 11, 28):
            # 漂移：纬度 > 90 或 经度跑到境外
            lon2 = 999.99 if i == 10 else lon
            lat2 = 199.99 if i == 11 else (lat + 60 if i == 28 else lat)
            rows.append([f"W{i%4:03d}", f"2020-07-18 12:{i:02d}:00", fmt(lon2), fmt(lat2), 121, 12.0])
        else:
            rows.append([f"W{i%4:03d}", f"2020-07-18 12:{i:02d}:00", fmt(lon), fmt(lat), 121, round(random.uniform(0,40),1)])
    write_csv("sim_out_of_range.csv", ["taxi_id","timestamp","lon","lat","direction","speed_kmh"], rows)
    return ("sim_out_of_range","越界坐标","经纬度超出合理范围（lat>90、lon 跑到上千、或跨省漂移）。无锡数据实测约 11.7% 跨省份越界。","越界点多为坐标系统错误或漂移，应直接剔除，否则会把轨迹画到非洲/海里。")

# 5. 常量传感器（IMU 占位）
def d_constant_sensor():
    rows = []
    base = walk(40, 114.06, 22.54)
    for i, (lon, lat, t) in enumerate(base):
        # 行驶车 IMU 全为常量占位（模拟无锡）
        rows.append([f"W{i%4:03d}", f"2020-07-18 12:{i:02d}:00", fmt(lon), fmt(lat), 121,
                     round(random.uniform(10,40),1), 1202, 315, 120, 343])
    write_csv("sim_constant_sensor.csv",
              ["taxi_id","timestamp","lon","lat","direction","speed_kmh","accel_x","accel_y","accel_z","yaw"], rows)
    return ("sim_constant_sensor","常量传感器(占位)","行驶状态下 5 个 IMU 字段恒为同一常数（如 1202/315/120/343）。无锡实测 78% 行驶行如此。","IMU 列实际是无用垃圾；经纬度/速度仍有效，但别拿 IMU 做加速度分析。")

# 6. 零速主导
def d_zero_speed():
    rows = []
    base = walk(40, 114.06, 22.54)
    for i, (lon, lat, t) in enumerate(base):
        sp = 0.0 if i % 5 != 0 else round(random.uniform(20,50),1)
        rows.append([f"S{i%6:03d}", f"2014-10-22 12:{i:02d}:00", fmt(lon), fmt(lat), 0, sp])
    write_csv("sim_zero_speed.csv", ["taxi_id","timestamp","lon","lat","passenger","speed_kmh"], rows)
    return ("sim_zero_speed","零速主导","绝大多数点 speed=0（长时间停靠/熄火），行驶点稀疏。","行驶样本太少，速度/载客分析不可靠；适合只研究'停泊点'。")

# 7. 稀疏采样
def d_sparse():
    rows = []
    base = walk(20, 116.40, 39.90, step=0.02)
    t = 0
    for i, (lon, lat, _) in enumerate(base):
        rows.append([f"T{i%8:04d}", f"2008-02-02 12:{t:02d}:00", fmt(lon), fmt(lat)])
        t += random.choice([120, 300, 600])  # 2-10 分钟一个大间隙
    write_csv("sim_sparse.csv", ["taxi_id","timestamp","lon","lat"], rows)
    return ("sim_sparse","稀疏采样","采样间隔极大（分钟级），点间直线连接会严重偏离真实道路。","轨迹形状失真，只能看大致方向，不能做精细路径/速度分析。")

# 8. 混合分隔符
def d_mixed_delim():
    rows = []
    base = walk(40, 120.30, 31.55)
    for i, (lon, lat, t) in enumerate(base):
        rows.append([f"W{i%4:03d}", f"2020-07-18 12:{i:02d}:00", fmt(lon), fmt(lat), 121, round(random.uniform(0,40),1)])
    write_csv("sim_mixed_delim.csv",
              ["taxi_id","timestamp","lon","lat","direction","speed_kmh"], rows, mixed=True)
    return ("sim_mixed_delim","混合分隔符","首列 id 后跟制表符 \\t，其余字段用逗号。无锡原始 CSV 即如此，普通 csv.reader 会解析失败。","解析时须先 split(',') 再 strip 首字段尾随 tab，否则整行错列。")

# 9. 时间戳混乱
def d_timestamp_chaos():
    rows = []
    base = walk(36, 114.06, 22.54)
    for i, (lon, lat, t) in enumerate(base):
        mode = i % 4
        if mode == 0:
            ts = f"2020-07-18 12:{i%60:02d}:00"      # ISO
        elif mode == 1:
            ts = f"07/18/2020 12:{i%60:02d}"          # 美式
        elif mode == 2:
            ts = str(1595049600 + i * 10)             # Unix 秒
        else:
            ts = f"2020/7/18 12:{i%60:02d}"           # 斜杠式
        rows.append([f"S{i%6:03d}", ts, fmt(lon), fmt(lat), 0, round(random.uniform(0,40),1)])
    write_csv("sim_timestamp_chaos.csv", ["taxi_id","timestamp","lon","lat","passenger","speed_kmh"], rows)
    return ("sim_timestamp_chaos","时间戳混乱","时间格式不统一：ISO、美式、Unix 秒、斜杠式混用。","必须统一解析为 datetime 才能算时长/速度；格式识别错误会导致时间倒流。")

# 10. 重复点
def d_dup_points():
    rows = []
    base = walk(40, 116.40, 39.90)
    prev = None
    for i, (lon, lat, t) in enumerate(base):
        if i in (8, 9, 10, 20, 21):  # 原地不动 → 连续重复
            row = prev if prev else [f"T{i%8:04d}", f"2008-02-02 12:{i:02d}:00", fmt(lon), fmt(lat)]
        else:
            row = [f"T{i%8:04d}", f"2008-02-02 12:{i:02d}:00", fmt(lon), fmt(lat)]
            prev = row
        rows.append(row)
    write_csv("sim_dup_points.csv", ["taxi_id","timestamp","lon","lat"], rows)
    return ("sim_dup_points","重复点","同一位置连续多条完全相同记录（GPS 静止时高频 ping）。北京实测约 8% 是此类。","无损可删：去重后轨迹不变，体积还能小一点。")

# 11. 载客状态缺失
def d_passenger_missing():
    rows = []
    base = walk(40, 114.06, 22.54)
    for i, (lon, lat, t) in enumerate(base):
        ps = "" if i in (6, 17, 29) else (1 if i % 4 == 0 else 0)
        rows.append([f"S{i%6:03d}", f"2014-10-22 12:{i:02d}:00", fmt(lon), fmt(lat), ps, round(random.uniform(0,40),1)])
    write_csv("sim_passenger_missing.csv", ["taxi_id","timestamp","lon","lat","passenger","speed_kmh"], rows)
    return ("sim_passenger_missing","载客状态缺失","passenger 字段空白或异常，无法区分空车/载客。","载客率算不出；OD/热点分析可信度下降。")

# 12. 跨日轨迹
def d_cross_midnight():
    rows = []
    base = walk(40, 116.40, 39.90, step=0.001)
    for i, (lon, lat, t) in enumerate(base):
        # 23:50 -> 00:30
        if i < 20:
            hh, mm = 23, 50 + i
            if mm >= 60: hh, mm = 0, mm-60
        else:
            hh, mm = 0, 10 + (i-20)
        ts = f"2008-02-02 {hh:02d}:{mm:02d}:00" if i < 20 else f"2008-02-03 {hh:02d}:{mm:02d}:00"
        rows.append([f"T{i%8:04d}", ts, fmt(lon), fmt(lat)])
    write_csv("sim_cross_midnight.csv", ["taxi_id","timestamp","lon","lat"], rows)
    return ("sim_cross_midnight","跨日轨迹","轨迹跨越午夜，按「日」切分时会把一条连续行程拦腰截断。","按自然日聚合前要先做「行程连续性」判断，否则跨日行程被拆碎。")

builders = [d_comprehensive, d_minimal, d_missing, d_out_of_range, d_constant_sensor,
            d_zero_speed, d_sparse, d_mixed_delim, d_timestamp_chaos, d_dup_points,
            d_passenger_missing, d_cross_midnight]
for b in builders:
    name, title, desc, impact = b()
    manifest.append({"file": name + ".csv", "title": title, "desc": desc, "impact": impact})

with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f"生成 {len(manifest)} 个模拟数据集 -> {OUT}")
for m in manifest:
    print(f"  {m['file']:28s} {m['title']}")
