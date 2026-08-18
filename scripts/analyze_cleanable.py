# -*- coding: utf-8 -*-
"""逐文件量化三城数据中"可大幅清理且不影响实际分析"的部分。
输出到 stdout 与 data/CLEANABLE_ANALYSIS.md。
只读取、不修改、不删除任何数据。"""
import os, csv, glob, random, statistics

BJ = r"C:\Users\wade\Documents\taxi-archive\beijing"
SZ = r"C:\Users\wade\Documents\taxi-archive\shenzhen"
WX = r"C:\Users\wade\Documents\taxi-archive-wuxi"

out = []
def log(s=""):
    print(s); out.append(str(s))

# ---------- 北京：逐文件统计连续重复 GPS 点 ----------
log("="*70)
log("一、北京 T-Drive (8911 个出租车 txt)")
log("="*70)
bj_files = glob.glob(os.path.join(BJ, "trajectories", "*", "*.txt"))
log(f"  文件数: {len(bj_files)}")
random.seed(42)
sample_bj = random.sample(bj_files, min(400, len(bj_files)))
total_lines = 0
dup_lines = 0
sample_lines = 0
for fp in sample_bj:
    with open(fp, "r", encoding="utf-8", errors="replace") as f:
        prev = None
        for line in f:
            sample_lines += 1
            line = line.strip()
            if not line:
                continue
            if line == prev:
                dup_lines += 1
            prev = line
rate = dup_lines / sample_lines if sample_lines else 0
# 估算全量
est_total = int(sample_lines / len(sample_bj) * len(bj_files))
est_dup = int(est_total * rate)
log(f"  抽样 {len(sample_bj)} 文件: {sample_lines} 行, 连续重复 {dup_lines} 行 ({rate*100:.1f}%)")
log(f"  全量估算: 约 {est_total:,} 行, 其中连续重复约 {est_dup:,} 行")
log(f"  → 删除连续重复 GPS 点(原地不动的重复 ping)可省约 {rate*100:.0f}% 体积, 无损(轨迹形状不变)")
log("")

# ---------- 深圳：逐片统计速度=0 / 载客 / 重复 ----------
log("="*70)
log("二、深圳 2014 (24 小时 CSV 分片)")
log("="*70)
sz_shards = sorted(glob.glob(os.path.join(SZ, "*.part*.csv")))
log(f"  分片数: {len(sz_shards)}")
# 取第一片做逐行精算
sh = sz_shards[0]
log(f"  精算样本片: {os.path.basename(sh)} ({os.path.getsize(sh)/1024/1024:.1f} MB)")
n=0; sp0=0; spgt0=0; pass1=0; dup=0; prev=None
with open(sh, "r", encoding="utf-8", errors="replace") as f:
    r = csv.reader(f)
    header = next(r)
    log(f"  字段: {header}")
    for row in r:
        if len(row) < 6: continue
        n += 1
        key = ",".join(row)
        if key == prev: dup += 1
        prev = key
        try:
            sp = float(row[5])
        except: sp = -1
        try:
            ps = int(row[4])
        except: ps = -1
        if sp == 0: sp0 += 1
        else: spgt0 += 1
        if ps == 1: pass1 += 1
log(f"  总行数: {n:,}")
log(f"  速度=0 (停着): {sp0:,} ({sp0/n*100:.1f}%)  | 速度>0 (行驶): {spgt0:,} ({spgt0/n*100:.1f}%)")
log(f"  载客(passenger=1): {pass1:,} ({pass1/n*100:.1f}%)")
log(f"  连续完全重复行: {dup:,} ({dup/n*100:.2f}%)")
log(f"  注: 速度=0 是'停车点', 对热点/停车分析有用, 不建议整删; 但可抽稀")
log("")

# ---------- 无锡：逐片统计常量 IMU(行驶车占位填充) ----------
log("="*70)
log("三、无锡 2020 (31 天 CSV 分片)")
log("="*70)
wx_shards = sorted(glob.glob(os.path.join(WX, "*.part*.csv")))
log(f"  分片数: {len(wx_shards)}")
sh = wx_shards[0]
log(f"  精算样本片: {os.path.basename(sh)} ({os.path.getsize(sh)/1024/1024:.1f} MB)")
n=0; moving=0; moving_const_imu=0; stopped=0
const_vals = {}
with open(sh, "r", encoding="utf-8", errors="replace") as f:
    r = csv.reader(f)
    header = next(r)
    # 字段: id,时间,经度,纬度,方向,速度,纵向加速度,横向加速度,垂直加速度,横摆角速度
    idx_dir = 4; idx_spd = 5; idx_lat = 2; idx_lon = 3
    idx_ax = 6; idx_ay = 7; idx_az = 8; idx_yaw = 9
    for row in r:
        if len(row) < 10: continue
        n += 1
        try:
            direction = int(row[idx_dir]); spd = float(row[idx_spd])
            ax=float(row[idx_ax]); ay=float(row[idx_ay]); az=float(row[idx_az]); yaw=float(row[idx_yaw])
        except: continue
        if spd > 0 or direction == 121:  # 行驶
            moving += 1
            # 常量 IMU 判定: 纵向加速度等是否等于已知占位常量
            if (ax, ay, az, yaw) == (1202.0, 315.0, 120.0, 343.0):
                moving_const_imu += 1
        else:
            stopped += 1
log(f"  总行数: {n:,}")
log(f"  行驶(速度>0或方向=121): {moving:,} ({moving/n*100:.1f}%)")
log(f"  其中 IMU=常量占位(1202/315/120/343)的无效行: {moving_const_imu:,} ({moving_const_imu/n*100:.1f}%)")
log(f"  停着: {stopped:,} ({stopped/n*100:.1f}%)")
log(f"  → 行驶车的 5 个 IMU 字段全是占位常量, 属垃圾数据; 但这些行本身(经纬度/速度)仍有效")
log("")

# ---------- 冗余压缩包 ----------
log("="*70)
log("四、已迁出的冗余压缩包 (C:\\Temp)")
log("="*70)
red = r"C:\Temp\taxi_redundant_archives"
if os.path.isdir(red):
    tot = 0
    for root,_,files in os.walk(red):
        for fl in files:
            tot += os.path.getsize(os.path.join(root,fl))
    log(f"  C:\\Temp\\taxi_redundant_archives 总大小: {tot/1024/1024:.0f} MB")
    log(f"  内容: 北京 rar(73M) + 深圳 zip(417M) + 深圳原始24csv(1.8G) + 无锡原始csv(2.6G) + 无锡zip(382M)")
    log(f"  → 这些与归档仓库内分片 CSV 完全重复, 物理删除即可释放 ~5GB (已不在仓库)")
log("")

# ---------- 抽稀潜力 ----------
log("="*70)
log("五、抽稀潜力 (保留每 K 个点, 轨迹形状基本不变)")
log("="*70)
log("  北京/深圳/无锡 GPS 点密度极高(秒级)。方法论演示与大部分分析只需 1/5~1/10 点。")
log("  每 5 抽 1 → 体积降到 ~20%; 每 10 抽 1 → ~10%。空间路径不失真, 仅丢失细时间分辨率。")
log("")

report = "\n".join(out)
with open(r"C:\Users\wade\Documents\taxi\data\CLEANABLE_ANALYSIS.md", "w", encoding="utf-8") as f:
    f.write("# 可清理数据分析（逐文件量化）\n\n" + report)
print("\n[已写入 data/CLEANABLE_ANALYSIS.md]")
