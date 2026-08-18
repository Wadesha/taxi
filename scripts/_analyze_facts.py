# -*- coding: utf-8 -*-
"""提取深圳/无锡真实数据事实，用于写页面时引用真实数字回答真实问题。"""
import csv, statistics, collections, os

RAW = r"C:\Users\wade\Documents\taxi\raw"

def num(x):
    try: return float(x)
    except: return None

# ===================== 深圳 12_时.csv =====================
print("="*60)
print("深圳 12_时.csv (真实数据采样)")
print("="*60)
p = os.path.join(RAW, "shenzhen", "12_时.csv")
pass0 = pass1 = 0
speeds = []
ids = set()
lon_min=lon_max=lat_min=lat_max=None
N = 0
MAX = 400000
with open(p, 'r', encoding='utf-8', errors='replace') as f:
    r = csv.reader(f)
    header = next(r)
    for row in r:
        if len(row) < 6: 
            continue
        N += 1
        tid, dt, lon, lat, pas, spd = row[0], row[1], row[2], row[3], row[4], row[5]
        ids.add(tid)
        if pas == '0': pass0 += 1
        elif pas == '1': pass1 += 1
        s = num(spd)
        if s is not None: speeds.append(s)
        lo, la = num(lon), num(lat)
        if lo is not None and la is not None:
            lon_min = lo if lon_min is None else min(lon_min, lo)
            lon_max = lo if lon_max is None else max(lon_max, lo)
            lat_min = la if lat_min is None else min(lat_min, la)
            lat_max = la if lat_max is None else max(lat_max, la)
        if N >= MAX: break

total = pass0 + pass1
print(f"采样行数: {N:,}")
print(f"唯一 trajectory_id 数: {len(ids):,}")
print(f"载客(passenger=1): {pass1:,} ({pass1/total*100:.1f}%)  空车(passenger=0): {pass0:,} ({pass0/total*100:.1f}%)")
print(f"速度: 均值 {statistics.mean(speeds):.1f} km/h, 中位数 {statistics.median(speeds):.0f} km/h, 最大 {max(speeds):.0f}, 零速占比 {sum(1 for s in speeds if s==0)/len(speeds)*100:.1f}%")
print(f"经度范围: {lon_min:.4f} ~ {lon_max:.4f} E")
print(f"纬度范围: {lat_min:.4f} ~ {lat_max:.4f} N")
# 速度分布（分桶）
buckets = collections.Counter()
for s in speeds:
    b = int(s//10)*10
    buckets[b] += 1
top = sorted(buckets.items(), key=lambda x:-x[1])[:6]
print("速度分布（前6个10km/h桶）:", [(f"{k}-{k+10}", v) for k,v in top])

# ===================== 无锡 20200718.csv =====================
print("\n" + "="*60)
print("无锡 20200718.csv (真实数据采样)")
print("="*60)
p = os.path.join(RAW, "wuxi", "data", "20200718.csv")
ids_w = set()
dirs = collections.Counter()
speeds_w = []
lon_min=lon_max=lat_min=lat_max=None
N=0; MAX=60000
out_region = 0
with open(p, 'r', encoding='utf-8', errors='replace') as f:
    for i, line in enumerate(f):
        line = line.rstrip('\r\n')
        if i == 0:
            header = line.split(',')
            continue
        if not line: continue
        # 格式： id<TAB>,lon,lat,time,dir,speed,...  按逗号切，再 strip 首字段尾随 \t
        cells = line.split(',')
        if len(cells) < 10:
            continue
        cells[0] = cells[0].strip()
        N += 1
        vid, lon, lat, t, direction, spd = cells[0], cells[1], cells[2], cells[3], cells[4], cells[5]
        ids_w.add(vid)
        dirs[direction] += 1
        s = num(spd)
        if s is not None: speeds_w.append(s)
        lo, la = num(lon), num(lat)
        if lo is not None and la is not None:
            lon_min = lo if lon_min is None else min(lon_min, lo)
            lon_max = lo if lon_max is None else max(lon_max, lo)
            lat_min = la if lat_min is None else min(lat_min, la)
            lat_max = la if lat_max is None else max(lat_max, la)
            # 无锡合理范围约 119.8~120.6E, 31.2~31.9N；越界标记
            if not (119.5 <= lo <= 121.0 and 30.8 <= la <= 32.2):
                out_region += 1
        if N >= MAX: break

print(f"采样行数: {N:,}")
print(f"唯一车辆 id 数: {len(ids_w):,}")
print(f"方向(direction)取值计数(前8): {dirs.most_common(8)}")
print(f"速度: 均值 {statistics.mean(speeds_w):.1f}, 中位数 {statistics.median(speeds_w):.0f}, 零速占比 {sum(1 for s in speeds_w if s==0)/len(speeds_w)*100:.1f}%")
print(f"经度范围: {lon_min:.4f} ~ {lon_max:.4f} E")
print(f"纬度范围: {lat_min:.4f} ~ {lat_max:.4f} N")
print(f"采样中落在无锡合理范围外的点: {out_region} ({out_region/N*100:.1f}%)")
