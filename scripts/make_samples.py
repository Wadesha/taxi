#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_samples.py — 从「全量原始数据」生成「小体积样本」

为什么需要它
------------
全量数据体积很大，不适合放进 Git 仓库，也不适合在演示/教学时加载：
    raw/beijing   8911 个 txt  ≈ 523 MB
    raw/shenzhen  24 个每小时 CSV ≈ 2.2 GB
    raw/wuxi      31 个 zip（含 20200718.csv）≈ 382 MB

本脚本从 `raw/`（已被 .gitignore 屏蔽、不进仓库）抽取有代表性的小样本，
写入 `data/`，供「基础数据处理」直接在样本上跑，无需加载全量。

生成的样本（默认各 50 行，单文件仅数 KB）：
    data/beijing_sample.csv   列: taxi_id,timestamp,lon,lat
    data/shenzhen_sample.csv  列: trajectory_id,date,lon,lat,passenger,speed(km/h)
    data/wuxi_sample.csv      列: id,经度,纬度,采集时间,方向,速度,纵向加速度,横向加速度,垂直加速度,横摆角速度

注意
----
- 仓库里提交的 `data/*_sample.csv` 是手工精选、与对应数据集页表格严格对应的版本
  （用于前端运行时验证的样本交叉校验）。本脚本默认也会生成同样结构的样本；
  若重新生成后页面表格未同步，请运行前端验证脚本（verify_taxi_site.js）确认，
  或保持仓库内已提交的精选样本不变。
- 可用环境变量 SAMPLE_OUT 指定输出目录，方便先试跑再决定覆盖：
      SAMPLE_OUT=/tmp/taxi_sample_test python make_samples.py
"""

import os
import glob
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
OUT = os.environ.get("SAMPLE_OUT", os.path.join(ROOT, "data"))
os.makedirs(OUT, exist_ok=True)


def write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(header + "\n")
        for r in rows:
            f.write(r + "\n")
    return len(rows)


def beijing_sample(n_taxis=3, per_taxi=50):
    """北京 T-Drive：每辆车一个 txt，格式 id,timestamp,lon,lat。"""
    files = sorted(glob.glob(os.path.join(RAW, "beijing", "**", "*.txt"), recursive=True))
    if not files:
        print("  ! 未找到北京原始 txt（应在 raw/beijing 下）", file=sys.stderr)
        return 0
    rows = []
    for fp in files[:n_taxis]:
        with open(fp, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= per_taxi:
                    break
                line = line.strip()
                if line:
                    rows.append(line)
    write_csv(
        os.path.join(OUT, "beijing_sample.csv"),
        "taxi_id,timestamp,lon,lat",
        rows,
    )
    return len(rows)


def shenzhen_sample(tid="22223", max_rows=50):
    """深圳：每小时一个 csv，格式 trajectory_id,date,lon,lat,passenger,speed(km/h)。"""
    files = sorted(glob.glob(os.path.join(RAW, "shenzhen", "*.csv")))
    if not files:
        print("  ! 未找到深圳原始 CSV（应在 raw/shenzhen 下）", file=sys.stderr)
        return 0
    rows = []
    for fp in files:
        with open(fp, encoding="utf-8", errors="replace") as f:
            f.readline()  # 跳过表头
            for line in f:
                if line.strip().startswith(tid + ","):
                    rows.append(line.strip())
                    if len(rows) >= max_rows:
                        break
        if rows:
            break
    write_csv(
        os.path.join(OUT, "shenzhen_sample.csv"),
        "trajectory_id,date,lon,lat,passenger,speed(km/h)",
        rows,
    )
    return len(rows)


def wuxi_sample(max_rows=50):
    """无锡：单 csv，10 字段，首列 id 后带制表符（混合分隔符）。"""
    fp = os.path.join(RAW, "wuxi", "data", "20200718.csv")
    if not os.path.exists(fp):
        print("  ! 未找到无锡原始 CSV：", fp, file=sys.stderr)
        return 0
    rows = []
    with open(fp, encoding="utf-8", errors="replace") as f:
        header = f.readline().strip()
        for i, line in enumerate(f):
            if i >= max_rows:
                break
            line = line.strip()
            if line:
                rows.append(line)
    write_csv(os.path.join(OUT, "wuxi_sample.csv"), header, rows)
    return len(rows)


if __name__ == "__main__":
    print("生成样本 ->", OUT)
    print("  beijing :", beijing_sample(), "行")
    print("  shenzhen:", shenzhen_sample(), "行")
    print("  wuxi    :", wuxi_sample(), "行")
    print("完成。样本已写入 data/（或用 SAMPLE_OUT 指定的目录）。")
