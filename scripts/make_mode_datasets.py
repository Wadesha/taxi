# -*- coding: utf-8 -*-
"""生成「交通时空数据分类图鉴」所需的一系列模拟数据集。

出发点：出租车 GPS 只是交通时空数据家族里的一格。
这份脚本把整张图的典型形态都造一份小样本，按 6 大结构分类：

  A 连续点轨迹      —— 车载终端逐点上报（出租车/网约车/公交/货车/共享电单车）
  B 行程起止记录    —— 只有起点终点，无中间轨迹（共享单车/有桩自行车/计价器行程）
  C 刷卡与事件      —— 离散交易观测（地铁 AFC / 公交 IC）
  D 断面固定检测    —— 设备守在一个断面上数车（线圈 / 卡口 ANPR / ETC 门架）
  E 聚合衍生        —— 已脱敏的统计产品（路段速度 / 网格 OD）
  F 其他模态与粗定位 —— 非道路或低精度（船舶 AIS / 手机信令）

输出：data/sim/modes/*.csv + manifest_modes.json
所有数据均为程序生成的模拟数据，不含任何真实个人或运营信息。
"""
import os, csv, json, random
from datetime import datetime, timedelta

random.seed(20260819)

ROOT = r"C:\Users\wade\Documents\taxi"
OUT = os.path.join(ROOT, "data", "sim", "modes")
os.makedirs(OUT, exist_ok=True)

# 统一的模拟城市中心（长三角某地量级，纯模拟）
CLON, CLAT = 120.3010, 31.5700
DAY = datetime(2026, 5, 18, 7, 0, 0)

META = []


def reg(file, cat, cat_name, title, carrier, structure, granularity,
        can, cannot, pitfall, realref, fields):
    META.append(dict(file=file, cat=cat, cat_name=cat_name, title=title,
                     carrier=carrier, structure=structure, granularity=granularity,
                     can=can, cannot=cannot, pitfall=pitfall,
                     realref=realref, fields=fields))


def f6(v):
    return f"{v:.6f}"


def jit(v, amp):
    return v + random.uniform(-amp, amp)


def T(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def write(fname, header, rows):
    with open(os.path.join(OUT, fname), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return len(rows)


def street_walk(n, lon0, lat0, step=0.0011, turn_p=0.16):
    """沿栅格街道行走，模拟受路网约束的轨迹（不是直线，也不是随机游走）。"""
    pts = []
    lon, lat = lon0, lat0
    dirs = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    d = random.randrange(4)
    for _ in range(n):
        if random.random() < turn_p:
            d = (d + random.choice([1, -1])) % 4
        dx, dy = dirs[d]
        lon += dx * step
        lat += dy * step * 0.78
        pts.append((jit(lon, 0.00007), jit(lat, 0.00007)))
    return pts


# ══════════════════════════════════════════════════════════════
# A 连续点轨迹
# ══════════════════════════════════════════════════════════════

def a1_taxi_gps():
    """出租车车载 GPS：本项目北京/深圳数据的形态。"""
    header = ["veh_id", "ts", "lon", "lat", "speed_kmh", "heading_deg", "occupied"]
    rows = []
    for v in range(3):
        vid = f"SIM-T{v + 1:03d}"
        pts = street_walk(16, jit(CLON, 0.01), jit(CLAT, 0.01))
        t = DAY + timedelta(minutes=v * 7)
        occ = random.choice([0, 1])
        for i, (lon, lat) in enumerate(pts):
            if i in (5, 11):
                occ = 1 - occ                      # 载客状态翻转 = 上/下客
            sp = 0 if random.random() < 0.18 else round(random.uniform(8, 52), 1)
            rows.append([vid, T(t), f6(lon), f6(lat), sp,
                         random.randrange(0, 360, 15), occ])
            t += timedelta(seconds=30)
    n = write("a1_taxi_gps.csv", header, rows)
    reg("a1_taxi_gps.csv", "A", "连续点轨迹", "出租车车载 GPS",
        "巡游出租车", "连续点序列（30 秒一点）", "秒级时间 / 米级空间",
        "完整行驶路径、速度画像、空车 vs 载客对比、OD 推断、热点识别、路径选择偏好。",
        "乘客是谁、车费多少、乘客下车后去了哪（换乘链断在下客点）。",
        "载客字段翻转点才是真正的上下客时刻；若只按「速度=0」找停靠，会把红灯误判成载客交易。",
        "本项目北京 T-Drive 2008、深圳 2014",
        "veh_id 车辆编号｜ts 时间戳｜lon/lat WGS-84 坐标｜speed_kmh 瞬时速度｜heading_deg 航向角｜occupied 0 空车 1 载客")
    return n


def a2_ridehail_order():
    """网约车：轨迹按订单状态分段，这是它与巡游出租车的本质差别。"""
    header = ["order_id", "driver_id", "ts", "lon", "lat", "speed_kmh", "order_status"]
    rows = []
    # 0 空驶待单 / 1 接驾中 / 2 送驾中 / 3 完成后空驶
    for o in range(2):
        oid = f"ORD{20260518000 + o}"
        did = f"DRV{o + 41:04d}"
        t = DAY + timedelta(minutes=o * 12)
        lon, lat = jit(CLON, 0.012), jit(CLAT, 0.012)
        seq = [(0, 5), (1, 7), (2, 12), (3, 4)]
        for status, cnt in seq:
            pts = street_walk(cnt, lon, lat)
            for lon, lat in pts:
                rows.append([oid if status in (1, 2) else "",
                             did, T(t), f6(lon), f6(lat),
                             round(random.uniform(0, 48), 1), status])
                t += timedelta(seconds=20)
    n = write("a2_ridehail_order.csv", header, rows)
    reg("a2_ridehail_order.csv", "A", "连续点轨迹", "网约车订单轨迹",
        "网约车（平台派单）", "连续点序列 + 订单状态机", "20 秒级 / 米级",
        "接驾距离与时长、平台派单效率、空驶结构（待单 vs 接驾）、订单级完整链路。",
        "巡游揽客行为（本来就不存在）、未上平台的黑车、平台之外的出行。",
        "空驶期 order_id 为空，直接按 order_id 分组会丢掉一半里程；接驾里程常被误算进「载客里程」。",
        "滴滴 GAIA 开放数据集（成都/西安订单与轨迹）",
        "order_id 订单号（空=无订单）｜driver_id 司机｜ts 时间｜lon/lat 坐标｜speed_kmh 速度｜order_status 0待单/1接驾/2送驾/3完成后空驶")
    return n


def a3_bus_gps():
    """公交车 GPS：轨迹被固定线路死死约束，天天重复同一条路。"""
    header = ["line_id", "bus_id", "ts", "lon", "lat", "speed_kmh",
              "next_stop_seq", "sched_dev_s"]
    rows = []
    route = street_walk(20, CLON - 0.012, CLAT - 0.008, step=0.0013, turn_p=0.08)
    for b in range(3):
        t = DAY + timedelta(minutes=b * 9)
        dev = random.randint(-60, 40)
        for i, (lon, lat) in enumerate(route):
            dev += random.randint(-12, 25)         # 延误逐站累积
            at_stop = i % 4 == 0
            rows.append([f"L{random.choice([12, 12, 12])}", f"BUS{b + 1:03d}", T(t),
                         f6(jit(lon, 0.00004)), f6(jit(lat, 0.00004)),
                         0 if at_stop else round(random.uniform(12, 38), 1),
                         i // 4 + 1, dev])
            t += timedelta(seconds=45 if at_stop else 35)
    n = write("a3_bus_gps.csv", header, rows)
    reg("a3_bus_gps.csv", "A", "连续点轨迹", "公交车 GPS 与到站偏差",
        "常规公交", "连续点序列 + 线路/站序标签", "30~45 秒级 / 站点级语义",
        "线路运行时间、站间车速、到站准点率、串车（bunching）识别、专用道效果评估。",
        "车上有几个人、乘客从哪上到哪下（要配合刷卡数据）、乘客等待时间。",
        "同一线路多辆车轨迹几乎重叠，做空间聚类会把线路当成「热点」；sched_dev_s 是累积量不是瞬时量。",
        "各地公交集团 AVL 数据、GTFS-Realtime",
        "line_id 线路｜bus_id 车辆｜ts 时间｜lon/lat 坐标｜speed_kmh 速度｜next_stop_seq 下一站序号｜sched_dev_s 相对时刻表偏差秒（正=晚点）")
    return n


def a4_truck_freight():
    """货车：城际长距离 + 长时间装卸停车 + 报警码。"""
    header = ["plate_hash", "ts", "lon", "lat", "speed_kmh", "load_state", "alarm_code"]
    rows = []
    for v in range(2):
        ph = f"HASH{random.getrandbits(20):05X}"
        t = DAY + timedelta(hours=v)
        lon, lat = jit(CLON, 0.03), jit(CLAT, 0.03)
        # 阶段：装货长停 → 长途行驶 → 卸货长停
        for _ in range(6):                          # 装货停车（速度 0，位置不动）
            rows.append([ph, T(t), f6(lon), f6(lat), 0, "empty", ""])
            t += timedelta(minutes=5)
        for i in range(14):                         # 高速行驶，采样间隔大
            lon += 0.019
            lat += 0.006
            sp = round(random.uniform(62, 95), 1)
            rows.append([ph, T(t), f6(lon), f6(lat), sp, "loaded",
                         "OVERSPEED" if sp > 90 else ""])
            t += timedelta(minutes=3)
        for _ in range(5):                           # 卸货停车
            rows.append([ph, T(t), f6(lon), f6(lat), 0, "loaded", "LONG_PARK"])
            t += timedelta(minutes=6)
    n = write("a4_truck_freight.csv", header, rows)
    reg("a4_truck_freight.csv", "A", "连续点轨迹", "货运车辆北斗监控",
        "营运货车（部标北斗终端）", "连续点序列 + 状态与报警", "1~5 分钟级 / 城际尺度",
        "干线物流通道识别、装卸点（物流枢纽）挖掘、超速与疲劳驾驶合规、空重载里程比。",
        "货物是什么、运费多少、城市内最后一公里配送细节（采样太稀）。",
        "采样间隔按分钟计，直线插值会「穿墙」跨越河流山体；长时间零速是装卸不是故障，别当异常删掉。",
        "全国道路货运车辆公共监管平台、部标 JT/T 808 终端数据",
        "plate_hash 车牌哈希（脱敏）｜ts 时间｜lon/lat 坐标｜speed_kmh 速度｜load_state empty空载/loaded重载｜alarm_code 报警类型")
    return n


def a5_ebike_share():
    """共享电单车：低速、走小巷、电子围栏。"""
    header = ["bike_id", "ts", "lon", "lat", "speed_kmh", "battery_pct", "in_fence"]
    rows = []
    for b in range(3):
        bid = f"EB{random.randrange(10000, 99999)}"
        t = DAY + timedelta(minutes=b * 6)
        pts = street_walk(14, jit(CLON, 0.006), jit(CLAT, 0.006), step=0.0004, turn_p=0.35)
        bat = random.randint(35, 95)
        for i, (lon, lat) in enumerate(pts):
            bat -= random.randint(0, 2)
            rows.append([bid, T(t), f6(lon), f6(lat),
                         round(random.uniform(4, 22), 1), bat,
                         0 if i in (9, 10) else 1])
            t += timedelta(seconds=15)
    n = write("a5_ebike_share.csv", header, rows)
    reg("a5_ebike_share.csv", "A", "连续点轨迹", "共享电单车骑行轨迹",
        "共享电单车 / 助力车", "连续点序列 + 围栏与电量", "15 秒级 / 亚米级抖动明显",
        "非机动车道使用、违规驶出电子围栏、短距接驳（地铁最后一公里）、电量与调度需求。",
        "骑车人是谁、有没有戴头盔、是否载人（数据里看不出来）。",
        "轨迹经常落在机动车路网之外（人行道、小巷、绿道），用汽车路网做地图匹配会大面积匹配失败。",
        "各城市共享单车/电单车监管平台接口",
        "bike_id 车辆｜ts 时间｜lon/lat 坐标｜speed_kmh 速度｜battery_pct 电量百分比｜in_fence 1在运营围栏内/0越界")
    return n


# ══════════════════════════════════════════════════════════════
# B 行程起止记录（无中间轨迹）
# ══════════════════════════════════════════════════════════════

def b1_dockless_bike_trip():
    header = ["order_id", "bike_id", "start_time", "start_lon", "start_lat",
              "end_time", "end_lon", "end_lat", "duration_s", "distance_m"]
    rows = []
    for i in range(28):
        t0 = DAY + timedelta(minutes=random.randint(0, 180))
        dur = random.randint(180, 1900)
        slon, slat = jit(CLON, 0.02), jit(CLAT, 0.02)
        elon, elat = slon + random.uniform(-0.012, 0.012), slat + random.uniform(-0.01, 0.01)
        # 直线距离 × 迂回系数（真实骑行路径总比直线长）
        straight = ((elon - slon) * 95000) ** 2 + ((elat - slat) * 111000) ** 2
        dist = int(straight ** 0.5 * random.uniform(1.15, 1.45))
        rows.append([f"BK{20260518000 + i}", f"MB{random.randrange(100000, 999999)}",
                     T(t0), f6(slon), f6(slat), T(t0 + timedelta(seconds=dur)),
                     f6(elon), f6(elat), dur, dist])
    n = write("b1_dockless_bike_trip.csv", header, rows)
    reg("b1_dockless_bike_trip.csv", "B", "行程起止记录", "共享单车骑行订单",
        "无桩共享单车", "只有起点与终点（两个坐标）", "行程级 / 米级起止点",
        "OD 分布、骑行时长与距离分布、地铁站接驳量、早晚高峰潮汐、投放调度需求。",
        "走了哪条路（中间轨迹根本不存在）、路径选择偏好、途中是否停顿。",
        "distance_m 通常是「计费距离」而非直线距离，拿它算平均速度会偏大；不能做地图匹配和路径分析。",
        "摩拜/哈啰开放数据、Divvy / Citi Bike 公开 trip 数据",
        "order_id 订单｜bike_id 车辆｜start/end_time 起止时间｜start/end_lon,lat 起止坐标｜duration_s 时长秒｜distance_m 骑行距离米")
    return n


def b2_docked_bike_trip():
    """有桩公共自行车：位置是站点 ID，不是坐标——必须 join 站点表。"""
    header = ["trip_id", "start_station_id", "start_station_name", "start_time",
              "end_station_id", "end_station_name", "end_time", "member_type"]
    stations = [(f"ST{i:03d}", n) for i, n in enumerate(
        ["体育中心西门", "文化广场", "地铁二号线A口", "滨湖公园北", "大学城南门",
         "人民路口", "科技园东", "医院正门"], start=1)]
    rows = []
    for i in range(26):
        (sid, sname), (eid, ename) = random.sample(stations, 2)
        t0 = DAY + timedelta(minutes=random.randint(0, 200))
        dur = random.randint(240, 1500)
        rows.append([f"DT{9000 + i}", sid, sname, T(t0), eid, ename,
                     T(t0 + timedelta(seconds=dur)),
                     random.choice(["annual", "annual", "casual"])])
    n = write("b2_docked_bike_trip.csv", header, rows)
    reg("b2_docked_bike_trip.csv", "B", "行程起止记录", "有桩公共自行车行程",
        "有桩公共自行车", "站点到站点（离散节点，无坐标）", "行程级 / 站点级空间",
        "站点间流量矩阵、站点满溢与空桩、会员 vs 散客行为差异、调度车调运计划。",
        "任何比站点更细的空间分析——你连起点坐标都没有，只有一个站名。",
        "位置精度被站点锁死（一个站覆盖数百米）；必须外接站点坐标表才能上地图，站点还会新增/迁移导致 ID 变化。",
        "Capital Bikeshare、杭州公共自行车、巴黎 Vélib'",
        "trip_id 行程｜start/end_station_id 起止站点编号｜station_name 站名｜start/end_time 起止时间｜member_type annual年卡/casual散客")
    return n


def b3_taxi_meter_trip():
    """出租车计价器行程记录：有钱、有里程，但没有轨迹。"""
    header = ["trip_id", "pickup_time", "dropoff_time", "pu_lon", "pu_lat",
              "do_lon", "do_lat", "trip_dist_km", "fare_cny", "passenger_cnt",
              "payment_type"]
    rows = []
    for i in range(26):
        t0 = DAY + timedelta(minutes=random.randint(0, 240))
        dur = random.randint(300, 2400)
        slon, slat = jit(CLON, 0.025), jit(CLAT, 0.025)
        dlon, dlat = slon + random.uniform(-0.03, 0.03), slat + random.uniform(-0.025, 0.025)
        dist = round(random.uniform(1.2, 18.5), 2)
        fare = round(11 + dist * 2.4 + random.uniform(0, 6), 1)
        rows.append([f"MT{7000 + i}", T(t0), T(t0 + timedelta(seconds=dur)),
                     f6(slon), f6(slat), f6(dlon), f6(dlat), dist, fare,
                     random.choice([1, 1, 1, 2, 2, 3]),
                     random.choice(["cash", "qr", "qr", "card"])])
    n = write("b3_taxi_meter_trip.csv", header, rows)
    reg("b3_taxi_meter_trip.csv", "B", "行程起止记录", "出租车计价器行程记录",
        "巡游出租车（计价器/发票系统）", "起止点 + 里程金额（无轨迹）", "行程级 / 米级起止点",
        "出行需求 OD、票价与里程关系、时段需求曲线、机场火车站集散量、支付方式演变。",
        "行驶路径与绕路判定（没有轨迹）、空驶行为（只记录载客段）、拥堵成因。",
        "只记录成功交易，空驶完全不可见——用它估算车辆利用率会严重偏高；里程是计价里程含空驶爬行。",
        "NYC TLC Trip Record Data（全球最常用的出行数据集之一）",
        "trip_id 行程｜pickup/dropoff_time 上下车时间｜pu/do_lon,lat 上下车坐标｜trip_dist_km 计价里程｜fare_cny 车费｜passenger_cnt 乘客数｜payment_type 支付方式")
    return n


# ══════════════════════════════════════════════════════════════
# C 刷卡与事件
# ══════════════════════════════════════════════════════════════

def c1_metro_afc():
    header = ["card_hash", "in_station", "in_time", "out_station", "out_time",
              "fare_cny", "card_type"]
    sts = ["火车站", "中山路", "三阳广场", "南禅寺", "太湖广场", "体育中心",
           "大学城", "机场", "会展中心"]
    rows = []
    for i in range(30):
        a, b = random.sample(sts, 2)
        t0 = DAY + timedelta(minutes=random.randint(0, 200))
        dur = random.randint(6, 48)
        rows.append([f"C{random.getrandbits(24):06X}", a, T(t0), b,
                     T(t0 + timedelta(minutes=dur)),
                     round(2 + dur * 0.09, 1),
                     random.choice(["normal", "normal", "student", "senior"])])
    n = write("c1_metro_afc.csv", header, rows)
    reg("c1_metro_afc.csv", "C", "刷卡与事件", "地铁进出站刷卡（AFC）",
        "轨道交通乘客", "两次事件配对（进站 + 出站）", "秒级时间 / 车站级空间",
        "全网 OD 客流矩阵、断面客流、换乘量估算、票价清分、通勤人群识别（跨天配对同一卡号）。",
        "乘客走了哪条换乘路径（同一 OD 常有 2~3 条可行路径，只能靠模型分配）、车厢内拥挤度、站外接驳方式。",
        "换乘路径不可观测，是这类数据的先天盲区；同卡号跨天配对涉及个体追踪，属敏感操作需脱敏与合规审查。",
        "各城市轨道 AFC 清分数据、上海/北京公交卡研究数据集",
        "card_hash 卡号哈希｜in_station/out_station 进出站｜in_time/out_time 进出时间｜fare_cny 票价｜card_type 卡类型")
    return n


def c2_bus_ic_onboard():
    """公交刷卡的经典残缺：只有上车，没有下车。"""
    header = ["card_hash", "line_id", "bus_id", "board_time", "board_stop_id",
              "board_stop_name", "transfer_flag"]
    stops = [(f"S{i:03d}", n) for i, n in enumerate(
        ["建筑路", "青石桥", "梁溪大桥", "工人文化宫", "崇安寺", "县前东街"], start=1)]
    rows = []
    for i in range(28):
        sid, sname = random.choice(stops)
        rows.append([f"C{random.getrandbits(24):06X}", f"L{random.choice([12, 25, 88])}",
                     f"BUS{random.randint(1, 40):03d}",
                     T(DAY + timedelta(minutes=random.randint(0, 190))),
                     sid, sname, random.choice([0, 0, 0, 1])])
    n = write("c2_bus_ic_onboard.csv", header, rows)
    reg("c2_bus_ic_onboard.csv", "C", "刷卡与事件", "公交刷卡（仅上车，无下车）",
        "常规公交乘客", "单次事件（只有一端）", "秒级时间 / 站点级空间",
        "线路上车客流、站点上客排名、换乘识别（同卡短时间内二次刷卡）、通勤 OD 的「起点」一半。",
        "下车站在哪——数据里根本没有。必须用出行链推断（下一次上车站≈本次下车站；当天最后一程≈当天第一程起点）。",
        "一票制城市普遍只刷上车，直接统计 OD 会得到一半为空的矩阵；推断出的下车站是估计值，必须标注不确定性。",
        "国内多数一票制城市公交 IC 卡数据",
        "card_hash 卡号哈希｜line_id 线路｜bus_id 车辆｜board_time 上车刷卡时间｜board_stop_id/name 上车站｜transfer_flag 1=判定为换乘")
    return n


# ══════════════════════════════════════════════════════════════
# D 断面固定检测
# ══════════════════════════════════════════════════════════════

def d1_loop_detector():
    header = ["detector_id", "link_id", "ts_5min", "volume_veh",
              "occupancy_pct", "avg_speed_kmh", "quality_flag"]
    rows = []
    for d in range(3):
        did = f"DET{d + 1:03d}"
        t = DAY
        for k in range(16):
            peak = 1.0 if 8 <= t.hour < 9 else 0.55
            vol = int(random.uniform(40, 120) * peak)
            occ = round(min(95, vol * random.uniform(0.35, 0.7)), 1)
            spd = round(max(6, 62 - occ * 0.55 + random.uniform(-4, 4)), 1)
            bad = k == 9 and d == 1
            rows.append([did, f"LK{2000 + d}", T(t),
                         "" if bad else vol, "" if bad else occ,
                         "" if bad else spd, "MISSING" if bad else "OK"])
            t += timedelta(minutes=5)
    n = write("d1_loop_detector.csv", header, rows)
    reg("d1_loop_detector.csv", "D", "断面固定检测", "线圈 / 地磁检测器",
        "断面上通过的所有车辆（不区分个体）", "固定位置的时间序列聚合", "5 分钟聚合 / 单一断面",
        "断面流量与占有率、拥堵演化曲线、基本图（流量-密度-速度关系）、信号配时评估、长期趋势（设备常年在岗）。",
        "任何个体行为——它不知道是谁经过，也不知道车从哪来到哪去；无法做 OD 与路径。",
        "设备故障导致成段缺失是常态（quality_flag），直接求均值会被 0 或空值污染；单点代表不了整条路。",
        "加州 PeMS、各城市交通信号系统检测器数据",
        "detector_id 检测器｜link_id 所在路段｜ts_5min 5分钟时间片｜volume_veh 通过车辆数｜occupancy_pct 时间占有率｜avg_speed_kmh 断面平均速度｜quality_flag 数据质量")
    return n


def d2_anpr_camera():
    """卡口车牌识别：离散断面观测，可以拼路径，但有漏检。"""
    header = ["plate_hash", "gantry_id", "pass_time", "lane", "speed_kmh",
              "confidence", "vehicle_type"]
    rows = []
    gantries = ["G01", "G02", "G03", "G04", "G05"]
    for v in range(8):
        ph = f"P{random.getrandbits(20):05X}"
        t = DAY + timedelta(minutes=random.randint(0, 60))
        route = gantries[:random.randint(3, 5)]
        for g in route:
            if random.random() < 0.15:           # 15% 漏检：这一段路径就断了
                t += timedelta(minutes=random.randint(3, 8))
                continue
            rows.append([ph, g, T(t), random.randint(1, 3),
                         round(random.uniform(35, 88), 1),
                         round(random.uniform(0.72, 0.99), 2),
                         random.choice(["car", "car", "car", "truck", "bus"])])
            t += timedelta(minutes=random.randint(3, 9))
    n = write("d2_anpr_camera.csv", header, rows)
    reg("d2_anpr_camera.csv", "D", "断面固定检测", "卡口车牌识别（ANPR）",
        "经过卡口的车辆（可识别到车）", "多个断面的离散观测点", "秒级时间 / 卡口点位空间",
        "卡口间行程时间、部分路径还原（把同一车牌串起来）、区域进出量、异常车辆追踪。",
        "两个卡口之间走的具体路线（中间是黑箱）、没装卡口的路网、车内情况。",
        "识别率不是 100%（confidence 低、遮挡、夜间），漏检会把一条路径拦腰截断；车牌本身是强个体标识，必须哈希脱敏。",
        "各城市公安交管卡口数据、高速门架流水",
        "plate_hash 车牌哈希｜gantry_id 卡口编号｜pass_time 通过时间｜lane 车道｜speed_kmh 通过速度｜confidence 识别置信度｜vehicle_type 车型")
    return n


def d3_etc_gantry():
    header = ["obu_hash", "gantry_id", "pass_time", "vehicle_class",
              "toll_cny", "province"]
    rows = []
    for v in range(9):
        oh = f"OBU{random.getrandbits(20):05X}"
        t = DAY + timedelta(minutes=random.randint(0, 120))
        for k in range(random.randint(2, 5)):
            rows.append([oh, f"GT{3100 + k}", T(t),
                         random.choice(["k1", "k1", "k2", "h2"]),
                         round(random.uniform(3.5, 42.0), 2),
                         random.choice(["苏", "苏", "浙", "皖"])])
            t += timedelta(minutes=random.randint(10, 40))
    n = write("d3_etc_gantry.csv", header, rows)
    reg("d3_etc_gantry.csv", "D", "断面固定检测", "高速 ETC 门架流水",
        "高速公路车辆（装 ETC 的）", "门架序列（按里程分段计费）", "秒级时间 / 门架里程点",
        "城际出行 OD、高速路网流量分配、分车型货运量、跨省通道分析、收费稽核。",
        "普通国省道与城市道路（门架只在高速上）、未装 ETC 车辆（走人工车道的那部分被系统性遗漏）。",
        "只覆盖高速，用它推断「城际总出行量」会系统性偏低；vehicle_class 是收费类别不是真实车型。",
        "全国高速 ETC 门架系统（2020 年后全网联网）",
        "obu_hash 车载单元哈希｜gantry_id 门架｜pass_time 通过时间｜vehicle_class 收费车型｜toll_cny 计费金额｜province 归属省份")
    return n


# ══════════════════════════════════════════════════════════════
# E 聚合衍生
# ══════════════════════════════════════════════════════════════

def e1_link_speed():
    header = ["link_id", "ts_5min", "speed_kmh", "free_flow_kmh",
              "congestion_idx", "sample_cnt"]
    rows = []
    for l in range(4):
        lid = f"LK{5000 + l}"
        ff = random.choice([40, 50, 60, 80])
        t = DAY
        for k in range(14):
            peak = 0.45 if 8 <= t.hour < 9 else 0.85
            sp = round(ff * peak * random.uniform(0.85, 1.1), 1)
            rows.append([lid, T(t), sp, ff, round(ff / max(sp, 1), 2),
                         random.randint(3, 180)])
            t += timedelta(minutes=5)
    n = write("e1_link_speed.csv", header, rows)
    reg("e1_link_speed.csv", "E", "聚合衍生", "路段速度指数",
        "路段（不是车辆）", "路段 × 时间片的聚合指标", "5 分钟 / 路段级",
        "全城拥堵指数、路段级速度热力图、拥堵时空传播、长期改善效果评估、无隐私顾虑地公开发布。",
        "任何个体轨迹（已被聚合抹去）、具体是哪些车造成拥堵、路径选择。",
        "sample_cnt 很小时速度极不稳定（3 辆车的均值不代表路段）；很多商业产品的算法不公开，跨城市/跨年份不可直接比较。",
        "高德/百度拥堵指数、TomTom Traffic Index、Uber Movement",
        "link_id 路段｜ts_5min 时间片｜speed_kmh 平均速度｜free_flow_kmh 自由流速度｜congestion_idx 拥堵指数（自由流/实际）｜sample_cnt 参与计算的样本车数")
    return n


def e2_grid_od_flow():
    header = ["hour", "grid_from", "grid_to", "trips", "mode", "grid_size_m"]
    rows = []
    grids = [f"G{r}{c}" for r in range(3) for c in range(3)]
    for h in [7, 8, 12, 18]:
        for _ in range(9):
            a, b = random.sample(grids, 2)
            rows.append([h, a, b, random.randint(5, 480),
                         random.choice(["taxi", "bike", "metro", "bus"]), 500])
    n = write("e2_grid_od_flow.csv", header, rows)
    reg("e2_grid_od_flow.csv", "E", "聚合衍生", "网格 OD 流量（脱敏发布态）",
        "人群流量（个体已抹除）", "网格 × 网格 × 时段的计数矩阵", "小时级 / 500 米网格",
        "宏观通勤流向、职住平衡、片区吸引与产生量、多方式对比、可公开发表与共享。",
        "个体出行链、具体路径、精确起终点（已被网格模糊化）、小样本人群（常被抑制为 0 或空）。",
        "网格边界会切开真实活动中心（模块化谬误）；小于阈值的流量常被隐去，直接求和会少算总量。",
        "联通/移动智慧足迹产品、Google/Apple 移动趋势报告、LEHD LODES",
        "hour 时段｜grid_from/grid_to 起止网格编号｜trips 出行次数｜mode 出行方式｜grid_size_m 网格边长米")
    return n


# ══════════════════════════════════════════════════════════════
# F 其他模态与粗定位
# ══════════════════════════════════════════════════════════════

def f1_ship_ais():
    header = ["mmsi", "ts", "lon", "lat", "sog_kn", "cog_deg", "nav_status", "draught_m"]
    rows = []
    for v in range(3):
        mm = f"41{random.randrange(1000000, 9999999)}"
        t = DAY + timedelta(minutes=v * 20)
        lon, lat = 121.8 + random.uniform(-0.3, 0.3), 31.0 + random.uniform(-0.3, 0.3)
        for k in range(14):
            moored = k >= 11
            lon += 0 if moored else random.uniform(0.02, 0.05)
            lat += 0 if moored else random.uniform(-0.02, 0.02)
            rows.append([mm, T(t), f6(lon), f6(lat),
                         0.0 if moored else round(random.uniform(6, 15), 1),
                         random.randrange(0, 360, 5),
                         "moored" if moored else "under_way",
                         round(random.uniform(4.5, 12.8), 1)])
            t += timedelta(minutes=random.choice([2, 3, 6, 10]))
    n = write("f1_ship_ais.csv", header, rows)
    reg("f1_ship_ais.csv", "F", "其他模态与粗定位", "船舶 AIS 报文",
        "船舶（海运/内河）", "连续点序列（但无路网约束）", "分钟级不等间隔 / 公里级尺度",
        "航线识别、港口停泊与等泊时间、贸易流量代理指标、碳排放估算、渔船作业区识别。",
        "船上货物明细、关闭 AIS 期间的行为（暗船）、内陆运输衔接。",
        "海面没有路网，所有基于「地图匹配」的方法直接失效；采样间隔随航速与设备变化极大；AIS 可被人为关闭。",
        "全球 AIS 公开数据（如 Danish AIS、Marine Cadastre）",
        "mmsi 船舶识别码｜ts 时间｜lon/lat 坐标｜sog_kn 对地航速（节）｜cog_deg 对地航向｜nav_status 航行状态｜draught_m 吃水深度")
    return n


def f2_pedestrian_signal():
    """手机信令：定位精度几百米，位置会在基站之间来回跳。"""
    header = ["user_hash", "ts", "cell_lon", "cell_lat", "accuracy_m",
              "cell_id", "event_type"]
    rows = []
    cells = [(jit(CLON, 0.02), jit(CLAT, 0.02), f"CELL{i:04d}") for i in range(5)]
    for u in range(4):
        uh = f"U{random.getrandbits(24):06X}"
        t = DAY + timedelta(minutes=u * 11)
        for k in range(12):
            # 关键现象：同一人静止不动，位置也会在相邻基站间来回跳
            clon, clat, cid = random.choice(cells[:2] if k < 6 else cells[2:])
            rows.append([uh, T(t), f6(clon), f6(clat),
                         random.choice([180, 250, 350, 500, 800]), cid,
                         random.choice(["handover", "periodic", "periodic", "call"])])
            t += timedelta(minutes=random.choice([2, 4, 7, 15]))
    n = write("f2_pedestrian_signal.csv", header, rows)
    reg("f2_pedestrian_signal.csv", "F", "其他模态与粗定位", "手机信令 / 基站定位",
        "持手机的人（全模式，不限交通工具）", "事件触发的粗定位点序列", "不等间隔（分钟~小时）/ 数百米精度",
        "全人群全方式出行（唯一能覆盖步行的数据）、职住识别、跨城迁徙、大范围人口热力、疫情/活动人流管控。",
        "具体交通方式（走路还是坐车分不清）、精确路径、小尺度空间行为（精度本身就有几百米）。",
        "「乒乓切换」——人不动位置也会在基站间反复跳，会被误判为高速移动；精度字段必须参与分析而不是忽略；隐私敏感度最高。",
        "运营商智慧足迹类产品、学术界手机信令 CDR 研究数据",
        "user_hash 用户哈希｜ts 时间｜cell_lon/cell_lat 基站或定位中心坐标｜accuracy_m 定位精度（米，越大越粗）｜cell_id 小区编号｜event_type handover切换/periodic周期上报/call通话")
    return n


# ══════════════════════════════════════════════════════════════

BUILDERS = [
    a1_taxi_gps, a2_ridehail_order, a3_bus_gps, a4_truck_freight, a5_ebike_share,
    b1_dockless_bike_trip, b2_docked_bike_trip, b3_taxi_meter_trip,
    c1_metro_afc, c2_bus_ic_onboard,
    d1_loop_detector, d2_anpr_camera, d3_etc_gantry,
    e1_link_speed, e2_grid_od_flow,
    f1_ship_ais, f2_pedestrian_signal,
]

if __name__ == "__main__":
    total = 0
    for fn in BUILDERS:
        n = fn()
        total += n
        print(f"  {fn.__name__:26s} -> {n:4d} 行")
    for m in META:
        m["rows"] = None
    with open(os.path.join(OUT, "manifest_modes.json"), "w", encoding="utf-8") as f:
        json.dump(META, f, ensure_ascii=False, indent=2)
    print(f"\n共 {len(META)} 个模拟数据集, {total} 行, 输出到 {OUT}")
