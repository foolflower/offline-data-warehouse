"""
Phase5/6: 用户行为日志生成引擎
对应 plan.md Phase 6:
  user_login_log, page_view_log, expose_log, action_log,
  start_log, search_log, error_log, session_info
"""
import math
import random
from datetime import datetime, timedelta, date

import config
from utils.csv_writer import CsvWriter
from utils.jsonl_writer import JsonlWriter
from utils.time_utils import random_time_on_day, fmt_datetime, fmt_date
from utils.distribution import weighted_choice, PrecomputedWeightedChooser


# ── 页面列表 ──
_PAGES = [
    "home", "category", "product_detail", "cart", "order_confirm",
    "payment", "order_list", "user_center", "search_result",
    "coupon_center", "activity_page", "brand_page",
]
_PAGE_WEIGHTS = [0.20, 0.15, 0.25, 0.10, 0.05,
                 0.03, 0.05, 0.05, 0.07, 0.02, 0.02, 0.01]

# 页面转移矩阵: 当前页 → 下一页概率分布 (漏斗逻辑)
# 行为真实性: home→category/search, category→product_detail, detail→cart, cart→order_confirm
_PAGE_TRANSITION = {
    "home":          [0.02, 0.30, 0.15, 0.02, 0.00, 0.00, 0.03, 0.05, 0.25, 0.08, 0.08, 0.02],
    "category":      [0.10, 0.05, 0.55, 0.02, 0.00, 0.00, 0.02, 0.03, 0.15, 0.03, 0.03, 0.02],
    "product_detail":[0.08, 0.10, 0.15, 0.35, 0.00, 0.00, 0.02, 0.02, 0.10, 0.05, 0.10, 0.03],
    "cart":          [0.10, 0.05, 0.20, 0.05, 0.40, 0.00, 0.05, 0.05, 0.05, 0.02, 0.02, 0.01],
    "order_confirm": [0.05, 0.02, 0.05, 0.10, 0.03, 0.60, 0.05, 0.05, 0.02, 0.01, 0.01, 0.01],
    "payment":       [0.05, 0.03, 0.05, 0.02, 0.00, 0.00, 0.50, 0.20, 0.05, 0.02, 0.05, 0.03],
    "order_list":    [0.25, 0.05, 0.15, 0.05, 0.00, 0.00, 0.05, 0.15, 0.10, 0.05, 0.10, 0.05],
    "user_center":   [0.30, 0.10, 0.05, 0.05, 0.00, 0.00, 0.15, 0.05, 0.10, 0.10, 0.05, 0.05],
    "search_result": [0.05, 0.10, 0.55, 0.05, 0.00, 0.00, 0.02, 0.03, 0.10, 0.03, 0.05, 0.02],
    "coupon_center": [0.15, 0.15, 0.25, 0.05, 0.00, 0.00, 0.02, 0.05, 0.10, 0.05, 0.15, 0.03],
    "activity_page": [0.10, 0.15, 0.35, 0.05, 0.00, 0.00, 0.02, 0.03, 0.10, 0.05, 0.05, 0.10],
    "brand_page":    [0.10, 0.10, 0.40, 0.05, 0.00, 0.00, 0.02, 0.03, 0.15, 0.05, 0.05, 0.05],
}

_ACTIONS = ["click", "collect", "add_cart", "share"]
_ACTION_W = [0.50, 0.15, 0.25, 0.10]

_SEARCH_KEYWORDS = [
    # 电子数码
    "手机", "耳机", "笔记本", "键盘", "显示器", "平板", "智能手表",
    "充电宝", "蓝牙音箱", "游戏鼠标", "机械键盘", "路由器", "投影仪",
    "无线充电器", "手机壳", "数据线", "摄像头", "打印机", "硬盘",
    # 服饰
    "T恤", "运动鞋", "书包", "羽绒服", "牛仔裤", "连衣裙", "卫衣",
    "短裤", "袜子", "内衣", "帽子", "腰带", "皮鞋", "凉鞋",
    # 美妆护肤
    "面膜", "防晒霜", "口红", "粉底液", "洗面奶", "精华液", "眼霜",
    "卸妆水", "护手霜", "香水", "睫毛膏", "遮瑕液",
    # 食品零食
    "零食", "瓜子", "坚果", "饼干", "巧克力", "蜂蜜", "燕麦",
    "泡面", "辣条", "薯片", "果冻", "棒棒糖", "牛肉干",
    # 家居日用
    "吸尘器", "洗衣液", "沙发", "枕头", "保温杯", "台灯", "拖把",
    "垃圾桶", "收纳盒", "空气净化器", "电饭锅", "热水壶",
    # 母婴运动医药
    "奶粉", "纸尿裤", "婴儿车", "维生素", "钙片", "牙膏", "猫粮",
    "瑜伽垫", "哑铃", "跑步鞋", "红豆薏米粉", "蛋白粉",
]


class BehaviorEngine:
    """行为日志生成引擎, 每天调用 process_day()"""

    def __init__(self, out_dir: str, sku_ids: list,
                 sku_weights: list, devices: list):
        self.out_dir = out_dir
        self.sku_ids = sku_ids
        self.sku_weights = sku_weights
        self.devices = devices
        # 自增ID
        self.login_id = 0
        self.pv_id = 0
        self.expose_id = 0
        self.action_id = 0
        self.start_id = 0
        self.search_id = 0
        self.error_id = 0
        self.session_id_seq = 0

        # 用户→设备绑定映射: 每个用户固定1-2个设备
        self._user_devices = {}  # 在process_day时惰性初始化

        # 用户→当天session映射, 供order_engine引用
        self.user_session_map = {}  # {uid: [session_id_str, ...]}

        # P0: 预计算SKU权重chooser, 避免每次weighted_choice重新累积
        self._sku_chooser = PrecomputedWeightedChooser(sku_ids, sku_weights)
        # 预计算页面权重chooser
        self._page_chooser = PrecomputedWeightedChooser(_PAGES, _PAGE_WEIGHTS)
        # 预计算页面转移chooser (每个页面一个)
        self._page_trans_choosers = {
            page: PrecomputedWeightedChooser(_PAGES, weights)
            for page, weights in _PAGE_TRANSITION.items()
        }
        # 预计算action权重chooser
        self._action_chooser = PrecomputedWeightedChooser(_ACTIONS, _ACTION_W)

    def open_writers(self):
        d = self.out_dir
        batch = config.CSV_BEHAVIOR_BATCH
        self.w_login = JsonlWriter(d, "user_login_log.jsonl", [
            "log_id", "user_id", "device_id", "login_time",
            "ip_address", "os", "app_version",
        ], batch_size=batch)
        self.w_pv = JsonlWriter(d, "page_view_log.jsonl", [
            "log_id", "user_id", "mid_id", "device_id",
            "page_id", "page_name", "sku_id",
            "session_id", "refer_page", "stay_seconds",
            "utm_source", "utm_medium", "utm_campaign",
            "create_time",
        ], batch_size=batch)
        self.w_expose = JsonlWriter(d, "expose_log.jsonl", [
            "log_id", "user_id", "mid_id", "device_id",
            "page_id", "sku_id", "position",
            "session_id", "trace_id", "create_time",
        ], batch_size=batch)
        self.w_action = JsonlWriter(d, "action_log.jsonl", [
            "log_id", "user_id", "mid_id", "device_id",
            "sku_id", "action_type",
            "session_id", "trace_id", "create_time",
        ], batch_size=batch)
        self.w_start = JsonlWriter(d, "start_log.jsonl", [
            "log_id", "user_id", "device_id",
            "app_version", "channel", "create_time",
        ], batch_size=batch)
        self.w_search = JsonlWriter(d, "search_log.jsonl", [
            "log_id", "user_id", "device_id",
            "keyword", "result_count", "click_sku_id",
            "session_id", "create_time",
        ], batch_size=batch)
        self.w_error = JsonlWriter(d, "error_log.jsonl", [
            "log_id", "user_id", "device_id",
            "error_code", "error_msg", "page_id",
            "create_time",
        ], batch_size=batch)
        self.w_session = CsvWriter(d, "session_info.csv", [
            "session_id", "user_id", "session_date",
            "start_time", "end_time", "event_count",
            "channel", "device_type", "device_id",
            "session_duration_minutes", "page_count",
            "search_count", "cart_count", "is_bounced",
        ], batch_size=batch)

    def close_writers(self):
        for attr in dir(self):
            if attr.startswith('w_'):
                getattr(self, attr).close()

    def flush_remaining_traces(self, traced_orders: dict):
        """B3: 为最后一天的traced订单补写expose→click→add_cart事件"""
        if not traced_orders:
            return
        for uid, orders in traced_orders.items():
            # 确保设备已初始化
            if uid not in self._user_devices:
                n_dev = random.choices([1, 2], weights=[0.7, 0.3], k=1)[0]
                self._user_devices[uid] = random.sample(
                    self.devices, k=min(n_dev, len(self.devices)))
            dev_id = random.choice(self._user_devices[uid])
            mid_id = f"M{dev_id:06d}"
            for torder in orders:
                tid = torder["trace_id"]
                t_time = torder["create_time"] - timedelta(
                    minutes=random.randint(5, 30))
                self.session_id_seq += 1
                trace_sess = f"SS{self.session_id_seq:010d}"
                trace_sess_start = t_time
                trace_event_cnt = 0
                trace_cart_cnt = 0
                for det in torder.get("details", []):
                    t_sku = det["sku_id"]
                    self.expose_id += 1
                    self.w_expose.write_row([
                        self.expose_id, uid, mid_id, dev_id,
                        "product_detail", t_sku, 1,
                        trace_sess, tid, fmt_datetime(t_time),
                    ])
                    trace_event_cnt += 1
                    t_time += timedelta(seconds=random.randint(10, 60))
                    self.action_id += 1
                    self.w_action.write_row([
                        self.action_id, uid, mid_id, dev_id,
                        t_sku, "click", trace_sess, tid,
                        fmt_datetime(t_time),
                    ])
                    trace_event_cnt += 1
                    t_time += timedelta(seconds=random.randint(5, 30))
                    self.action_id += 1
                    self.w_action.write_row([
                        self.action_id, uid, mid_id, dev_id,
                        t_sku, "add_cart", trace_sess, tid,
                        fmt_datetime(t_time),
                    ])
                    trace_event_cnt += 1
                    trace_cart_cnt += 1
                    t_time += timedelta(seconds=random.randint(5, 20))
                trace_sess_end = t_time
                trace_dur = (trace_sess_end - trace_sess_start).total_seconds() / 60.0
                self.w_session.write_row([
                    trace_sess, uid,
                    fmt_date(torder["create_time"].date()),
                    fmt_datetime(trace_sess_start),
                    fmt_datetime(trace_sess_end),
                    trace_event_cnt, "direct", "phone", dev_id,
                    round(trace_dur, 1), trace_event_cnt // 3,
                    0, trace_cart_cnt, 0,
                ])

    def process_day(self, day: date, dau_users: list, traced_orders: dict = None):
        """为每个DAU用户生成当日行为序列"""
        self.user_session_map = {}  # B1: 每天重置, 避免跨天session累积
        self._traced_orders = traced_orders or {}
        for uid in dau_users:
            self._gen_user_day(day, uid)

    def _gen_user_day(self, day: date, uid: int):
        """单个用户一天的完整行为链"""
        # 用户绑定设备: 每人固定1-2个, 惰性初始化
        if uid not in self._user_devices:
            n_dev = random.choices([1, 2], weights=[0.7, 0.3], k=1)[0]
            self._user_devices[uid] = random.sample(
                self.devices, k=min(n_dev, len(self.devices)))
        dev_id = random.choice(self._user_devices[uid])
        mid_id = f"M{dev_id:06d}"

        # Feature #12: 15% 匿名用户
        is_anon = random.random() < config.ANONYMOUS_LOG_RATE
        eff_uid = "" if is_anon else uid

        # session: 每次启动一个独立session
        n_starts = random.randint(*config.START_PER_USER)
        # 为每次启动创建独立session_id
        sess_ids = []
        for _ in range(n_starts):
            self.session_id_seq += 1
            sess_ids.append(f"SS{self.session_id_seq:010d}")
        # 记录用户所有session供OrderEngine引用
        if not is_anon:
            self.user_session_map.setdefault(uid, []).extend(sess_ids)

        # 1) start_log: 每次启动一条
        start_time = random_time_on_day(day)
        start_times = []
        for si in range(n_starts):
            self.start_id += 1
            start_times.append(start_time)
            self.w_start.write_row([
                self.start_id, eff_uid, dev_id,
                random.choice(["4.0.1", "4.2.0", "5.0.0"]),
                random.choice(["organic", "push", "ad", "share"]),
                fmt_datetime(start_time),
            ])
            start_time = start_time + timedelta(
                minutes=random.randint(30, 300))

        # 2) login_log (匿名用户跳过)
        login_time = random_time_on_day(day)
        if not is_anon:
            self.login_id += 1
            self.w_login.write_row([
                self.login_id, uid, dev_id, fmt_datetime(login_time),
                f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                random.choice(["Android", "iOS"]),
                random.choice(["4.0.1", "4.2.0", "5.0.0"]),
            ])

        # 3) page_view + expose + action — 按session分配PV
        n_pv = random.randint(*config.PAGE_VIEW_PER_USER)
        pv_per_sess = max(1, n_pv // n_starts)
        # 每个session的计数器
        sess_counters = [{
            "pv": 0, "search": 0, "cart": 0, "event": 0,
            "start_time": start_times[i],
            "end_time": start_times[i],
        } for i in range(n_starts)]
        cur_sess_idx = 0
        sess_id = sess_ids[0]
        cur_time = login_time + timedelta(seconds=random.randint(1, 60))
        last_page = ""

        for pv_i in range(n_pv):
            # 按PV分段切换session
            new_idx = min(pv_i // pv_per_sess, n_starts - 1)
            if new_idx != cur_sess_idx:
                cur_sess_idx = new_idx
                sess_id = sess_ids[cur_sess_idx]
                cur_time = start_times[cur_sess_idx] + timedelta(
                    seconds=random.randint(1, 60))
                last_page = ""
            # 漏斗逻辑: 第一页用全局权重, 后续页面基于当前页转移概率
            if pv_i == 0 or last_page not in self._page_trans_choosers:
                page = self._page_chooser.choose()
            else:
                page = self._page_trans_choosers[last_page].choose()
            sku_id = self._sku_chooser.choose() \
                if page in ("product_detail", "cart") else ""
            # 不同页面类型停留时间分化 (P2: 对数正态分布, 模拟真实长尾)
            _stay_range = {
                "home": (3, 30), "product_detail": (10, 180),
                "cart": (5, 60), "order_confirm": (10, 90),
                "payment": (5, 40), "category": (3, 25),
                "search_result": (5, 45), "my_account": (3, 20),
            }
            lo, hi = _stay_range.get(page, (2, 60))
            mid = (lo + hi) / 2
            mu = math.log(max(mid, 1))
            stay = int(random.lognormvariate(mu, 0.8))
            stay = max(lo, min(hi, stay))

            # Feature #4: UTM 60% null
            utm_src = "" if random.random() < config.NULL_UTM_RATE \
                else random.choice(["baidu", "wechat", "douyin", "direct"])
            utm_med = "" if not utm_src else random.choice(["cpc", "organic", "social"])
            utm_cmp = "" if not utm_src else f"camp{random.randint(1,30):03d}"

            self.pv_id += 1
            self.w_pv.write_row([
                self.pv_id, eff_uid, mid_id, dev_id,
                f"PG{self.pv_id}", page, sku_id,
                sess_id, last_page, stay,
                utm_src, utm_med, utm_cmp,
                fmt_datetime(cur_time),
            ])

            # Feature #5: 0.5% page_view 重复
            if random.random() < config.DUP_PAGE_VIEW_RATE:
                self.w_pv.write_row([
                    self.pv_id, eff_uid, mid_id, dev_id,
                    f"PG{self.pv_id}", page, sku_id,
                    sess_id, last_page, stay,
                    utm_src, utm_med, utm_cmp,
                    fmt_datetime(cur_time),
                ])

            sc = sess_counters[cur_sess_idx]
            sc["pv"] += 1
            sc["event"] += 1
            sc["end_time"] = cur_time

            # expose: 每页3-10次
            n_exp = random.randint(*config.EXPOSE_PER_PAGE)
            for pos in range(1, n_exp + 1):
                exp_sku = self._sku_chooser.choose()
                self.expose_id += 1
                self.w_expose.write_row([
                    self.expose_id, eff_uid, mid_id, dev_id,
                    f"PG{self.pv_id}", exp_sku, pos,
                    sess_id, "", fmt_datetime(cur_time),
                ])
                sess_counters[cur_sess_idx]["event"] += 1

            # action: 约30%的PV触发action
            if random.random() < 0.30:
                act = self._action_chooser.choose()
                act_sku = sku_id if sku_id else \
                    self._sku_chooser.choose()
                self.action_id += 1
                self.w_action.write_row([
                    self.action_id, eff_uid, mid_id, dev_id,
                    act_sku, act, sess_id, "",
                    fmt_datetime(cur_time),
                ])
                sess_counters[cur_sess_idx]["event"] += 1
                if act == "add_cart":
                    sess_counters[cur_sess_idx]["cart"] += 1

            last_page = page
            cur_time = cur_time + timedelta(seconds=stay)

        # 4) search_log: 0-5次 (归入最后一个session, 时间在session范围内)
        sess_id = sess_ids[-1]
        last_sc = sess_counters[-1]
        n_search = random.randint(*config.SEARCH_PER_USER)
        for _ in range(n_search):
            kw = random.choice(_SEARCH_KEYWORDS)
            # 幂律分布: 多数搜索返回少量结果, 少数热词返回大量结果
            rc = int(random.paretovariate(1.5)) + random.randint(0, 5)
            rc = min(rc, 2000)
            click_sku = self._sku_chooser.choose() \
                if rc > 0 and random.random() < 0.6 else ""
            self.search_id += 1
            # 搜索时间在最后session的start~end范围内
            s_start = last_sc["start_time"]
            s_end = last_sc["end_time"]
            delta = max(1, int((s_end - s_start).total_seconds()))
            s_time = s_start + timedelta(
                seconds=random.randint(0, delta))
            # 更新session end_time
            if s_time > last_sc["end_time"]:
                last_sc["end_time"] = s_time
            self.w_search.write_row([
                self.search_id, eff_uid, dev_id,
                kw, rc, click_sku, sess_id,
                fmt_datetime(s_time),
            ])
            sess_counters[-1]["search"] += 1
            sess_counters[-1]["event"] += 1

        # 5) error_log: 0.5%
        if random.random() < config.ERROR_RATE:
            self.error_id += 1
            err_codes = ["E001", "E002", "E003", "E004", "E005"]
            err_msgs = ["网络超时", "数据解析异常", "服务不可用",
                        "参数错误", "未知错误"]
            idx = random.randint(0, 4)
            self.w_error.write_row([
                self.error_id, eff_uid, dev_id,
                err_codes[idx], err_msgs[idx],
                random.choice(_PAGES),
                fmt_datetime(random_time_on_day(day)),
            ])

        # Feature #16: 全链路追踪 — 为该用户的traced订单注入 expose→click→add_cart
        if uid in self._traced_orders:
            for torder in self._traced_orders[uid]:
                tid = torder["trace_id"]
                t_time = torder["create_time"] - timedelta(
                    minutes=random.randint(5, 30))
                # B2: 为trace事件创建独立session, 时间范围对齐订单创建日
                self.session_id_seq += 1
                trace_sess = f"SS{self.session_id_seq:010d}"
                trace_sess_start = t_time
                trace_event_cnt = 0
                trace_cart_cnt = 0
                for det in torder.get("details", []):
                    t_sku = det["sku_id"]
                    # expose
                    self.expose_id += 1
                    self.w_expose.write_row([
                        self.expose_id, uid, mid_id, dev_id,
                        "product_detail", t_sku, 1,
                        trace_sess, tid, fmt_datetime(t_time),
                    ])
                    trace_event_cnt += 1
                    t_time = t_time + timedelta(seconds=random.randint(10, 60))
                    # click
                    self.action_id += 1
                    self.w_action.write_row([
                        self.action_id, uid, mid_id, dev_id,
                        t_sku, "click", trace_sess, tid,
                        fmt_datetime(t_time),
                    ])
                    trace_event_cnt += 1
                    t_time = t_time + timedelta(seconds=random.randint(5, 30))
                    # add_cart
                    self.action_id += 1
                    self.w_action.write_row([
                        self.action_id, uid, mid_id, dev_id,
                        t_sku, "add_cart", trace_sess, tid,
                        fmt_datetime(t_time),
                    ])
                    trace_event_cnt += 1
                    trace_cart_cnt += 1
                    t_time = t_time + timedelta(seconds=random.randint(5, 20))
                # B2: 写出trace专属session_info
                trace_sess_end = t_time
                trace_dur = (trace_sess_end - trace_sess_start).total_seconds() / 60.0
                self.w_session.write_row([
                    trace_sess, eff_uid,
                    fmt_date(torder["create_time"].date()),
                    fmt_datetime(trace_sess_start),
                    fmt_datetime(trace_sess_end),
                    trace_event_cnt, "direct", "phone", dev_id,
                    round(trace_dur, 1), trace_event_cnt // 3,
                    0, trace_cart_cnt, 0,
                ])

        # 6) session_info — 每个session各一条
        channel = random.choice(["organic", "push", "ad", "share", "direct"])
        dev_type = random.choice(["phone", "tablet", "pc"])
        for si in range(n_starts):
            sc = sess_counters[si]
            s_start = sc["start_time"]
            s_end = sc["end_time"]
            duration = (s_end - s_start).total_seconds() / 60.0
            is_bounced = 1 if sc["pv"] <= 1 else 0
            self.w_session.write_row([
                sess_ids[si], eff_uid, fmt_date(day),
                fmt_datetime(s_start), fmt_datetime(s_end),
                sc["event"], channel, dev_type, dev_id,
                round(duration, 1), sc["pv"],
                sc["search"], sc["cart"], is_bounced,
            ])
