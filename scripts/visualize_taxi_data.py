import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from datetime import datetime
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 数据路径
data_dir = r"c:\Users\wade\Documents\taxi\2.北京市出租车数据\Beijing(one-week trajectories of 10,357 taxis)\T-Drive trajectory data sample"

def parse_trajectory_file(filepath):
    """解析轨迹文件"""
    try:
        df = pd.read_csv(filepath, header=None, names=['taxi_id', 'timestamp', 'longitude', 'latitude'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        return None

def load_sample_data(sample_size=10):
    """加载样本数据"""
    files = list(Path(data_dir).glob('*.txt'))[:sample_size]
    all_data = []
    for f in files:
        df = parse_trajectory_file(f)
        if df is not None and len(df) > 0:
            all_data.append(df)
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

def calculate_statistics(df):
    """计算统计信息"""
    if df.empty:
        return {}
    
    # 计算时间范围
    time_range = df.groupby('taxi_id').agg({
        'timestamp': ['min', 'max', 'count'],
        'longitude': ['mean', 'min', 'max'],
        'latitude': ['mean', 'min', 'max']
    }).reset_index()
    
    time_range.columns = ['taxi_id', 'start_time', 'end_time', 'point_count',
                          'lng_mean', 'lng_min', 'lng_max',
                          'lat_mean', 'lat_min', 'lat_max']
    
    # 计算时长（分钟）
    time_range['duration_minutes'] = (time_range['end_time'] - time_range['start_time']).dt.total_seconds() / 60
    
    return time_range

def create_visualization(df, stats):
    """创建系列可视化图表"""
    # 设置图表大小和子图布局
    fig = plt.figure(figsize=(20, 15))
    gs = gridspec.GridSpec(3, 4, hspace=0.4, wspace=0.4)

    # 1. 轨迹点分布散点图
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.scatter(df['longitude'], df['latitude'], c=df['taxi_id'], cmap='tab20', s=0.1, alpha=0.5)
    ax1.set_xlabel('经度')
    ax1.set_ylabel('纬度')
    ax1.set_title('出租车轨迹点分布', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # 2. 单辆出租车详细轨迹
    ax2 = fig.add_subplot(gs[0, 1])
    taxi_sample = df[df['taxi_id'] == df['taxi_id'].iloc[0]].copy()
    taxi_sample = taxi_sample.sort_values('timestamp')
    ax2.plot(taxi_sample['longitude'], taxi_sample['latitude'], 'b-', linewidth=0.5, alpha=0.7)
    ax2.scatter(taxi_sample['longitude'], taxi_sample['latitude'], c=taxi_sample.index,
                cmap='viridis', s=10, alpha=0.8)
    ax2.set_xlabel('经度')
    ax2.set_ylabel('纬度')
    ax2.set_title(f'出租车 {taxi_sample["taxi_id"].iloc[0]} 轨迹详情', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # 3. 时间分布热力图（小时 x 天）
    ax3 = fig.add_subplot(gs[0, 2])
    df['hour'] = df['timestamp'].dt.hour
    df['day'] = df['timestamp'].dt.dayofweek
    df_day_hour = df.groupby(['day', 'hour']).size().unstack(fill_value=0)
    im = ax3.imshow(df_day_hour.values, cmap='YlOrRd', aspect='auto')
    ax3.set_xlabel('小时')
    ax3.set_ylabel('星期 (0=周一, 6=周日)')
    ax3.set_title('时间分布热力图', fontsize=12, fontweight='bold')
    ax3.set_yticks(range(7))
    ax3.set_yticklabels(['周一', '周二', '周三', '周四', '周五', '周六', '周日'])
    plt.colorbar(im, ax=ax3, label='记录数')

    # 4. 每辆出租车记录点数统计
    ax4 = fig.add_subplot(gs[0, 3])
    stats_sorted = stats.sort_values('point_count')
    ax4.bar(range(len(stats_sorted)), stats_sorted['point_count'], color='steelblue', alpha=0.7)
    ax4.set_xlabel('出租车排序')
    ax4.set_ylabel('记录点数')
    ax4.set_title('各出租车记录点数统计', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')

    # 5. 活动时长分布
    ax5 = fig.add_subplot(gs[1, 0])
    ax5.hist(stats['duration_minutes'], bins=20, color='orange', alpha=0.7, edgecolor='black')
    ax5.set_xlabel('活动时长 (分钟)')
    ax5.set_ylabel('出租车数量')
    ax5.set_title('活动时长分布', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3, axis='y')

    # 6. 经度分布
    ax6 = fig.add_subplot(gs[1, 1])
    ax6.hist(df['longitude'], bins=50, color='green', alpha=0.7, edgecolor='black')
    ax6.set_xlabel('经度')
    ax6.set_ylabel('频数')
    ax6.set_title('经度分布', fontsize=12, fontweight='bold')
    ax6.grid(True, alpha=0.3, axis='y')

    # 7. 纬度分布
    ax7 = fig.add_subplot(gs[1, 2])
    ax7.hist(df['latitude'], bins=50, color='purple', alpha=0.7, edgecolor='black')
    ax7.set_xlabel('纬度')
    ax7.set_ylabel('频数')
    ax7.set_title('纬度分布', fontsize=12, fontweight='bold')
    ax7.grid(True, alpha=0.3, axis='y')

    # 8. 每小时活动统计
    ax8 = fig.add_subplot(gs[1, 3])
    hourly_counts = df.groupby('hour').size()
    ax8.plot(hourly_counts.index, hourly_counts.values, marker='o', linewidth=2, markersize=6, color='red')
    ax8.fill_between(hourly_counts.index, hourly_counts.values, alpha=0.3, color='red')
    ax8.set_xlabel('小时')
    ax8.set_ylabel('记录数')
    ax8.set_title('每小时活动统计', fontsize=12, fontweight='bold')
    ax8.set_xticks(range(0, 24, 3))
    ax8.grid(True, alpha=0.3)

    # 9. 经纬度分布密度（2D直方图）
    ax9 = fig.add_subplot(gs[2, 0])
    h = ax9.hist2d(df['longitude'], df['latitude'], bins=40, cmap='Blues')
    ax9.set_xlabel('经度')
    ax9.set_ylabel('纬度')
    ax9.set_title('经纬度分布密度', fontsize=12, fontweight='bold')
    plt.colorbar(h[3], ax=ax9, label='密度')

    # 10. 多辆出租车轨迹对比
    ax10 = fig.add_subplot(gs[2, 1])
    for i, taxi_id in enumerate(df['taxi_id'].unique()[:5]):
        taxi_data = df[df['taxi_id'] == taxi_id].sort_values('timestamp')
        ax10.plot(taxi_data['longitude'], taxi_data['latitude'],
                 label=f'出租车 {taxi_id}', linewidth=0.8, alpha=0.7)
    ax10.set_xlabel('经度')
    ax10.set_ylabel('纬度')
    ax10.set_title('多辆出租车轨迹对比', fontsize=12, fontweight='bold')
    ax10.legend(fontsize=8, loc='best')
    ax10.grid(True, alpha=0.3)

    # 11. 每天活动统计
    ax11 = fig.add_subplot(gs[2, 2])
    daily_counts = df.groupby(df['timestamp'].dt.date).size()
    ax11.plot(range(len(daily_counts)), daily_counts.values, marker='s', linewidth=2, markersize=8, color='darkblue')
    ax11.set_xlabel('天数')
    ax11.set_ylabel('记录数')
    ax11.set_title('每天活动统计', fontsize=12, fontweight='bold')
    ax11.grid(True, alpha=0.3)

    # 12. 出租车活动范围统计
    ax12 = fig.add_subplot(gs[2, 3])
    stats['lng_range'] = stats['lng_max'] - stats['lng_min']
    stats['lat_range'] = stats['lat_max'] - stats['lat_min']
    stats['area'] = stats['lng_range'] * stats['lat_range']
    ax12.scatter(stats['lng_range'], stats['lat_range'], alpha=0.6, s=50, c='brown')
    ax12.set_xlabel('经度范围')
    ax12.set_ylabel('纬度范围')
    ax12.set_title('出租车活动范围统计', fontsize=12, fontweight='bold')
    ax12.grid(True, alpha=0.3)

    # 添加总标题
    fig.suptitle('北京出租车轨迹数据分析 - 12个子图综合展示', fontsize=16, fontweight='bold', y=0.995)

    return fig

def main():
    print("正在加载数据...")
    df = load_sample_data(sample_size=20)

    if df.empty:
        print("没有找到数据！")
        return

    print(f"加载了 {len(df)} 条记录，涉及 {df['taxi_id'].nunique()} 辆出租车")

    print("正在计算统计信息...")
    stats = calculate_statistics(df)

    print("正在创建可视化图表...")
    fig = create_visualization(df, stats)

    # 保存图片
    output_path = r"c:\Users\wade\Documents\taxi\taxi_visualization_4x3.png"
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n图表已保存到: {output_path}")

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
