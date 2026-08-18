#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 raw/ 下的【已解包】全量数据重组到 archive/，结构清清楚楚：
  archive/beijing/trajectories/<bucket>/<id>.txt    北京 8911 个轨迹文件（按 id 每 1000 一组）
  archive/shenzhen/2014-10-22_<HH>.partNN.csv       深圳 24 小时 CSV（重命名 + <50MB 分片，每片含表头）
Wuxi 单独处理（见任务 #24）。本脚本只动 beijing + shenzhen。
移动（shutil.move）而非复制，避免双份占用磁盘。
"""
import os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_B = os.path.join(ROOT, "raw", "beijing")
SRC_S = os.path.join(ROOT, "raw", "shenzhen")
DST   = os.path.join(ROOT, "archive")
SHARD_MAX = 45 * 1024 * 1024  # 45MB，留余量确保单文件 <50MB（无 GitHub 警告）

def restructure_beijing():
    dst = os.path.join(DST, "beijing", "trajectories")
    os.makedirs(dst, exist_ok=True)
    txts = []
    for root, _, files in os.walk(SRC_B):
        for f in files:
            if f.endswith(".txt"):
                txts.append(os.path.join(root, f))
    print(f"[beijing] 找到 txt: {len(txts)}")
    moved = 0
    for p in txts:
        name = os.path.basename(p)
        try:
            idn = int(os.path.splitext(name)[0])
        except ValueError:
            idn = 0
        lo = (idn // 1000) * 1000 + 1
        hi = lo + 999
        sub = os.path.join(dst, f"{lo:05d}-{hi:05d}")
        os.makedirs(sub, exist_ok=True)
        shutil.move(p, os.path.join(sub, name))
        moved += 1
    print(f"[beijing] 已移动到 archive/beijing/trajectories/ : {moved} 个")

def shard_csv(src, dst_dir, base):
    os.makedirs(dst_dir, exist_ok=True)
    part = 0
    out = None
    written = 0
    with open(src, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline()
        def open_part():
            nonlocal part, out, written
            if out:
                out.close()
            part += 1
            written = 0
            fn = os.path.join(dst_dir, f"{base}.part{part:02d}.csv")
            out = open(fn, "w", encoding="utf-8")
            out.write(header)
        open_part()
        for line in f:
            if written > SHARD_MAX and line.rstrip("\n"):
                open_part()
            out.write(line)
            written += len(line.encode("utf-8"))
    if out:
        out.close()
    return part

def restructure_shenzhen():
    dst = os.path.join(DST, "shenzhen")
    os.makedirs(dst, exist_ok=True)
    csvs = sorted(
        f for f in os.listdir(SRC_S) if f.endswith(".csv")
    )
    print(f"[shenzhen] 找到 csv: {len(csvs)}")
    for fn in csvs:
        try:
            hh = int(fn[:2])
        except ValueError:
            hh = 0
        base = f"2014-10-22_{hh:02d}"
        n = shard_csv(os.path.join(SRC_S, fn), dst, base)
        print(f"[shenzhen] {fn} -> {base}.part01..{n:02d}.csv ({n} 片)")
    print(f"[shenzhen] 完成，输出目录: {dst}")

if __name__ == "__main__":
    restructure_beijing()
    restructure_shenzhen()
    print("DONE")
