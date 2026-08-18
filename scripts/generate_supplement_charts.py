# -*- coding: utf-8 -*-
"""生成补充图表：真实数据图 + 模拟分析图（用于填充分析链空缺）"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = r"C:\Users\wade\Documents\taxi\assets\img"
RAW = r"C:\Users\wade\Documents\taxi\raw"
os.makedirs(OUT, exist_ok=True)

# ============ 1. 北京单车完整轨迹（真实数据） ============
def beijing_track():
    p = os.path.join(RAW, "beijing", "Beijing(one-week trajectories of 10,357 taxis)", "T-Drive trajectory data sample", "1.txt")
    df = pd.read_csv(p, header=None, names=['taxi_id', 'ts', 'lon', 'lat'])
    df = df[df['lon'].between(116.3, 116.8) & df['lat'].between(39.7, 40.1)]
    # 去掉重复点（GPS 漂移）
    df = df.drop_duplicates(subset=['lon', 'lat']).reset_index(drop=True)
    ts = pd.to_datetime(df['ts'])
    t0 = ts.min()
    secs = (ts - t0).dt.total_seconds().values  # 距 0 点秒数，避免 datetime 溢出

    fig, ax = plt.subplots(1, 1, figsize=(10, 9))
    pts = ax.scatter(df['lon'], df['lat'], c=secs, cmap='viridis', s=18, alpha=0.85, zorder=3)
    ax.plot(df['lon'], df['lat'], '-', color='#999999', lw=0.6, alpha=0.4, zorder=2)
    ax.set_title('北京 T-Drive · 出租车 1 号的一天轨迹\n（颜色 = 当天时间，从早到晚）', fontsize=14, fontweight='bold')
    ax.set_xlabel('经度 (°E)'); ax.set_ylabel('纬度 (°N)')
    ax.grid(True, alpha=0.25)
    cb = plt.colorbar(pts, ax=ax, shrink=0.8, label='2月2日时刻')
    # 用秒数 → HH:MM 格式化
    def fmt_hm(x, pos):
        h = int(x // 3600); m = int((x % 3600) // 60)
        return f'{h:02d}:{m:02d}'
    cb.ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(fmt_hm))
    # 标注两个典型位置
    ax.annotate('市中心区\n(短时停留)', xy=(116.511, 39.921), xytext=(116.49, 39.93),
                arrowprops=dict(arrowstyle='->', color='red'), fontsize=10, color='red')
    ax.annotate('远端驻车区\n(长时间不动)', xy=(116.6916, 39.8516), xytext=(116.66, 39.84),
                arrowprops=dict(arrowstyle='->', color='blue'), fontsize=10, color='blue')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'beijing-track-day.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('beijing-track-day.png:', len(df), 'points')

# ============ 2. 北京多车轨迹对比（真实数据） ============
def beijing_multi():
    base = os.path.join(RAW, "beijing", "Beijing(one-week trajectories of 10,357 taxis)", "T-Drive trajectory data sample")
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), sharex=True, sharey=True)
    ids = ['1.txt', '50.txt', '500.txt']
    colors = ['#c0392b', '#2563eb', '#16a085']
    for ax, fn, c in zip(axes, ids, colors):
        p = os.path.join(base, fn)
        df = pd.read_csv(p, header=None, names=['taxi_id', 'ts', 'lon', 'lat'])
        df = df[df['lon'].between(116.3, 116.8) & df['lat'].between(39.7, 40.1)]
        df = df.drop_duplicates(subset=['lon', 'lat'])
        ax.plot(df['lon'], df['lat'], '-', color=c, lw=0.8, alpha=0.8)
        ax.scatter(df['lon'].iloc[0], df['lat'].iloc[0], marker='o', s=40, color=c, zorder=5, edgecolors='k')
        ax.scatter(df['lon'].iloc[-1], df['lat'].iloc[-1], marker='x', s=50, color='k', zorder=5)
        ax.set_title(f'出租车 {fn[:-4]} 号', fontsize=12)
        ax.grid(True, alpha=0.25)
        ax.set_xlabel('经度 (°E)')
        if ax is axes[0]: ax.set_ylabel('纬度 (°N)')
    fig.suptitle('不同出租车的运营轨迹差异（真实数据：圈=起点，×=终点）', fontsize=14, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(os.path.join(OUT, 'beijing-multi-track.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('beijing-multi-track.png done')

# ============ 3. 深圳空车 vs 载客空间分布（真实数据，采样） ============
def shenzhen_load():
    p = os.path.join(RAW, "shenzhen", "12_时.csv")
    df = pd.read_csv(p, nrows=400000)  # 采样 40 万行加速
    df = df[(df['lon'].between(113.7, 114.7)) & (df['lat'].between(22.3, 23.0))]
    empty = df[df['passenger'] == 0]
    loaded = df[df['passenger'] == 1]
    print('  载客:', len(loaded), '空车:', len(empty))

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    for ax, sub, title in [(axes[0], empty, '空车（巡游寻客）'), (axes[1], loaded, '载客（正在运营）')]:
        hb = ax.hexbin(sub['lon'], sub['lat'], gridsize=60, cmap='YlOrRd', mincnt=1)
        ax.set_title(f'{title} · 深圳 12:00 切片（真实 40 万条采样）', fontsize=12)
        ax.set_xlabel('经度 (°E)'); ax.set_ylabel('纬度 (°N)')
        cb = plt.colorbar(hb, ax=ax, shrink=0.8); cb.set_label('采样点密度')
    fig.suptitle('空车与载客的空间分布对比：空车更集中在城区核心', fontsize=14, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(os.path.join(OUT, 'shenzhen-load-compare.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('shenzhen-load-compare.png done')

# ============ 4. 深圳速度分布（真实数据） ============
def shenzhen_speed():
    p = os.path.join(RAW, "shenzhen", "12_时.csv")
    df = pd.read_csv(p, nrows=400000)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(df['speed(km/h)'], bins=60, color='#d35400', alpha=0.85, edgecolor='white', lw=0.3)
    ax.axvline(df['speed(km/h)'].median(), color='#2563eb', ls='--', lw=1.5, label=f"中位数 {df['speed(km/h)'].median():.0f} km/h")
    ax.axvline(df['speed(km/h)'].mean(), color='#16a085', ls='--', lw=1.5, label=f"均值 {df['speed(km/h)'].mean():.1f} km/h")
    ax.set_xlabel('瞬时速度 (km/h)'); ax.set_ylabel('记录数')
    ax.set_title('深圳出租车瞬时速度分布（12:00 切片，40 万条采样）\n左端"零速高峰"= 等红灯 / 堵车 / 上客', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.25, axis='y')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'shenzhen-speed-dist.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('shenzhen-speed-dist.png done')

# ============ 5. 无锡惯性信号时序（真实数据） ============
def wuxi_signal():
    p = os.path.join(RAW, "wuxi", "data", "20200718.csv")
    # 该文件表头用逗号分隔，但数据行是 "id<TAB>,lon,lat,..." 混合格式，需手动解析
    cols = None
    recs = []
    with open(p, 'r', encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f):
            line = line.rstrip('\r\n')
            if i == 0:
                cols = [c.strip() for c in line.split(',')]
                continue
            if i > 60001: break
            cells = line.split(',')
            if len(cells) < 10:
                continue
            cells[0] = cells[0].strip()
            recs.append(cells)
    df = pd.DataFrame(recs, columns=cols)
    for c in ['速度', '纵向加速度', '横向加速度', '垂直加速度', '横摆角速度']:
        df[c] = pd.to_numeric(df[c], errors='coerce')

    # 关键发现：行驶车辆(方向=121)的惯性值高度恒定(疑似默认填充)，
    # 因此挑一辆 静止(speed==0) 且 横向/垂直加速度有真实起伏 的车，展示低速传感器噪声。
    stat = df[df['速度'] == 0]
    if stat.empty:
        print('  无锡: 无 speed==0 记录, 跳过'); return
    g = stat.groupby('id')
    best, best_var = None, -1
    for vid, sub in g:
        v = sub['横向加速度'].nunique() + sub['垂直加速度'].nunique()
        if v > best_var:
            best_var, best = v, vid
    d = stat[stat['id'] == best].head(400).reset_index(drop=True)
    ts = pd.to_datetime(d['采集时间'])
    t = (ts - ts.iloc[0]).dt.total_seconds().values

    fig, axes = plt.subplots(4, 1, figsize=(11, 9), sharex=True)
    axes[0].plot(t, d['速度'], color='#2563eb', lw=1.2); axes[0].set_ylabel('速度 (km/h)'); axes[0].set_title(f'无锡 · 静止车辆 {best} 的低速惯性信号（真实 400 条记录）\n低速段速度≈0，惯性通道呈低幅传感器噪声', fontsize=12, fontweight='bold')
    axes[1].plot(t, d['纵向加速度'], color='#d35400', lw=1.0); axes[1].set_ylabel('纵向加速度')
    axes[2].plot(t, d['横向加速度'], color='#16a085', lw=1.0); axes[2].set_ylabel('横向加速度')
    axes[3].plot(t, d['横摆角速度'], color='#8e44ad', lw=1.0); axes[3].set_ylabel('横摆角速度'); axes[3].set_xlabel('时间 (秒)')
    for ax in axes: ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'wuxi-signal-series.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('wuxi-signal-series.png done; 静止车', best, 'var=', best_var)

# ============ 6. 模拟 OD 矩阵（体系空缺 → 模拟填充） ============
def od_matrix():
    np.random.seed(42)
    zones = ['福田', '罗湖', '南山', '盐田', '宝安', '龙岗', '龙华', '光明', '坪山', '大鹏', '其他']
    n = len(zones)
    # 构造一个不对称的 OD 矩阵：对角线高（区内出行），少数强联系（福田→南山等）
    base = np.random.rand(n, n) * 50
    np.fill_diagonal(base, np.random.rand(n) * 400 + 300)
    base[0, 2] += 180  # 福田→南山
    base[2, 0] += 140  # 南山→福田
    base[0, 4] += 120; base[4, 0] += 90
    base[1, 2] += 80
    od = np.round(base).astype(int)

    fig, ax = plt.subplots(figsize=(9, 8))
    im = ax.imshow(od, cmap='YlOrRd')
    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels(zones, rotation=45, ha='right'); ax.set_yticklabels(zones)
    for i in range(n):
        for j in range(n):
            ax.text(j, i, str(od[i, j]), ha='center', va='center', fontsize=8,
                    color='white' if od[i, j] > 200 else '#333')
    ax.set_xlabel('目的地 (D)'); ax.set_ylabel('出发地 (O)')
    ax.set_title('模拟 OD 出行矩阵（示例）· 行 = 出发区，列 = 到达区\n说明：真实 OD 需从起讫点还原，本图用于演示分析方法', fontsize=12, fontweight='bold')
    cb = plt.colorbar(im, ax=ax, shrink=0.85); cb.set_label('出行量 (单位：千次/日)')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'od-matrix-demo.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('od-matrix-demo.png done')

# ============ 7. 模拟热点区（用真实坐标做 hexbin，标注假设热点） ============
def hotspot():
    np.random.seed(7)
    # 用深圳坐标生成 3 个高斯簇模拟热点（真实位置附近）
    centers = [(114.05, 22.53), (114.12, 22.55), (114.08, 22.52)]
    xs, ys = [], []
    for c in centers:
        n = 3000
        xs.append(np.random.normal(c[0], 0.012, n))
        ys.append(np.random.normal(c[1], 0.01, n))
    xs = np.concatenate(xs); ys = np.concatenate(ys)

    fig, ax = plt.subplots(figsize=(9, 7))
    hb = ax.hexbin(xs, ys, gridsize=40, cmap='hot', mincnt=1)
    ax.set_title('出租车热点区域识别（模拟演示）\n颜色越亮 = 越可能是热门上客点', fontsize=12, fontweight='bold')
    ax.set_xlabel('经度 (°E)'); ax.set_ylabel('纬度 (°N)')
    cb = plt.colorbar(hb, ax=ax, shrink=0.8); cb.set_label('密度')
    ax.annotate('疑似商圈热点', xy=(114.05, 22.53), xytext=(113.98, 22.56),
                arrowprops=dict(arrowstyle='->'), fontsize=10, color='#c0392b')
    ax.annotate('疑似交通枢纽', xy=(114.12, 22.55), xytext=(114.16, 22.58),
                arrowprops=dict(arrowstyle='->'), fontsize=10, color='#c0392b')
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'hotspot-demo.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('hotspot-demo.png done')

if __name__ == '__main__':
    beijing_track()
    beijing_multi()
    shenzhen_load()
    shenzhen_speed()
    wuxi_signal()
    od_matrix()
    hotspot()
    print('全部完成')
