"""
Phase5核心: 订单生命周期生成引擎 (order_engine.py)
对应 plan.md 三、事件驱动生成法
生成: order_info, order_detail, order_status_log,
      payment_info, payment_detail, payment_invoice,
      order_refund_info, cart_info, favor_info,
      comment_info, after_sales
"""
import random
from datetime import datetime, timedelta, date

import config
from utils.csv_writer import CsvWriter
from utils.time_utils import (
    random_time_on_day, midnight_drift_time, midnight_drift_next_day,
    should_midnight_drift, pay_delay_minutes, ship_delay_hours,
    receive_delay_days, complete_delay_days,
    add_minutes, add_hours, add_days,
    should_time_anomaly, should_late_callback, late_callback_delay_hours,
    fmt_datetime, fmt_date,
)
from utils.distribution import (
    weighted_choice, build_hot_sku_weights, build_hot_city_weights,
    choose_fate, normal_int,
)
from utils.fake_data import random_chinese_name


# ── 常量 ──
PAYMENT_TYPES = [1, 2, 3, 4]     # Feature #13: 1微信/2支付宝/3银行卡/4货到付款
PAYMENT_TYPE_W = [0.44, 0.37, 0.17, 0.02]
SOURCE_TYPES = [1, 2, 3, 4]       # 1APP/2小程序/3H5/4PC
SOURCE_TYPE_W = [0.50, 0.25, 0.15, 0.10]

# 订单状态: 0待支付 1已支付 2已发货 3已收货 4已完成 5退款 6取消
# H2: 性别/年龄偏好品类关键词 (匹配SKU名称)
_FEMALE_KEYWORDS = {"面膜", "口红", "精华液", "防晒", "洗面奶", "粉底", "眼霜",
                    "卸妆", "眉笔", "腮红", "连衣裙", "丝巾", "珍珠", "耳环",
                    "手镯", "项链", "戒指", "美妆", "护肤", "香水"}
_MALE_KEYWORDS = {"笔记本", "显示器", "键盘", "鼠标", "行车记录", "座垫",
                  "车载", "哑铃", "登山包", "帐篷", "遥控车", "电钻", "路由器"}
_CHILD_KEYWORDS = {"奶粉", "纸尿裤", "积木", "推车", "绘本", "学步", "儿童", "婴儿"}

STATUS_MAP = {
    'created': 0, 'paid': 1, 'shipped': 2,
    'received': 3, 'completed': 4, 'refunded': 5, 'cancelled': 6,
}


class OrderEngine:
    """事件驱动订单生成引擎, 每天调用 process_day()"""

    def __init__(self, out_dir: str, skus: dict, users: dict,
                 activities: dict, coupons: dict, merchants: dict,
                 cities: dict, receives: dict = None,
                 rules_by_activity: dict = None,
                 user_addresses: dict = None,
                 activity_sku_map: dict = None):
        self.out_dir = out_dir
        self.skus = skus
        self.users = users
        self.activities = activities
        self.coupons = coupons
        self.merchants = merchants
        self.cities = cities
        self.rules_by_activity = rules_by_activity or {}
        self.user_addresses = user_addresses or {}
        self.activity_sku_map = activity_sku_map or {}

        # SKU权重 (Feature #6 热点倾斜)
        self.sku_ids = sorted(skus.keys())
        self.sku_weights = build_hot_sku_weights(
            self.sku_ids, config.HOT_SKU_COUNT, config.HOT_SKU_ORDER_SHARE)

        # 城市权重 (Feature #6)
        self.city_ids = sorted(cities.keys())
        self.city_weights = build_hot_city_weights(
            self.city_ids, config.HOT_CITY_COUNT, config.HOT_CITY_ORDER_SHARE)

        # 活跃用户池 (排除lost)
        self.active_user_ids = [
            uid for uid, u in users.items() if u["status"] != "lost"
        ]

        # 自增ID计数器
        self.order_id_seq = 0
        self.detail_id_seq = 0
        self.status_log_id_seq = 0
        self.payment_id_seq = 0
        self.pay_detail_id_seq = 0
        self.invoice_id_seq = 0
        self.refund_id_seq = 0
        self.cart_id_seq = 0
        self.favor_id_seq = 0
        self.comment_id_seq = 0
        self.after_sales_id_seq = 0

        # 待推进的历史订单 {order_id: order_dict}
        self.pending_orders = {}

        # 用户首单追踪 (Feature #15)
        self.user_first_order = set()

        # 券使用池
        self.coupon_ids = list(coupons.keys()) if coupons else []

        # 按用户分组的可用领取记录 (status='used')
        self._user_receive_pool = {}  # {user_id: [receive_dict, ...]}
        if receives:
            for rec in receives.values():
                if rec["status"] == "used":
                    uid = rec["user_id"]
                    self._user_receive_pool.setdefault(uid, []).append(rec)

        # 已消费的券使用记录 [(use_id, coupon_id, user_id, order_id, use_time, discount, record_id)]
        self._coupon_use_seq = 0

        # 用户下单权重: 高level用户下单概率更高 (帕累托效应)
        self._user_order_weights = {}
        for uid, u in users.items():
            lv = u.get("user_level", 1)
            # level 1→1, 2→2, 3→4, 4→8, 5→16 指数递增
            self._user_order_weights[uid] = 2 ** (lv - 1)

        # 按品类索引SKU, 支持同品类聚合选品
        self._cat3_sku_map = {}  # {cat3_id: [sku_id, ...]}
        for sid, sku in skus.items():
            c3 = sku.get("cat3_id")
            if c3:
                self._cat3_sku_map.setdefault(c3, []).append(sid)

        # 用户实际行为统计 (供 user_tag_snapshot 使用)
        # {uid: {"order_count": int, "total_amount": float, "last_order_day": date, "active_days": set}}
        self.user_stats = {}

        # 每日新进入 shipped 状态的订单 (供 ship_eng 处理, 解决跨天孤儿问题)
        # H2: 按关键词构建性别/年龄偏好SKU池
        self._female_sku_ids = [
            sid for sid, sk in skus.items()
            if any(kw in sk.get("sku_name", "") for kw in _FEMALE_KEYWORDS)
        ]
        self._male_sku_ids = [
            sid for sid, sk in skus.items()
            if any(kw in sk.get("sku_name", "") for kw in _MALE_KEYWORDS)
        ]
        self._child_sku_ids = [
            sid for sid, sk in skus.items()
            if any(kw in sk.get("sku_name", "") for kw in _CHILD_KEYWORDS)
        ]

        # 每日新进入 shipped 状态的订单 (供 ship_eng 处理, 解决跨天孤儿问题)
        self.newly_shipped_today = []
        # 每日新进入 received 状态的订单 (供 ship_eng 更新 signed_flag)
        self.newly_received_today = []
        # 每日新进入 refunded 状态的订单 (供库存回补)
        self.newly_refunded_today = []

    def _update_user_stats(self, uid: int, day: date, amount: float):
        """更新用户的订单统计"""
        if uid not in self.user_stats:
            self.user_stats[uid] = {
                "order_count": 0, "total_amount": 0.0,
                "last_order_day": None, "active_days": set(),
            }
        s = self.user_stats[uid]
        s["order_count"] += 1
        s["total_amount"] += amount
        s["last_order_day"] = day
        s["active_days"].add(day)

    def open_writers(self):
        """打开所有CSV writer"""
        d = self.out_dir
        self.w_order = CsvWriter(d, "order_info.csv", [
            "order_id", "user_id", "merchant_id", "province_id",
            "city_id", "order_status", "total_amount",
            "original_total_amount", "activity_reduce_amount",
            "coupon_reduce_amount", "discount_reduce_amount",
            "freight_amount", "payment_type", "source_type",
            "is_first_order", "session_id", "trace_id",
            "create_time", "payment_time", "send_time",
            "receive_time", "complete_time", "operate_time",
        ])
        self.w_detail = CsvWriter(d, "order_detail.csv", [
            "detail_id", "order_id", "sku_id", "sku_name",
            "order_price", "sku_num", "sku_total_amount",
            "merchant_id", "create_time", "operate_time",
        ])
        self.w_status = CsvWriter(d, "order_status_log.csv", [
            "log_id", "order_id", "order_status",
            "operate_time",
        ])
        self.w_payment = CsvWriter(d, "payment_info.csv", [
            "payment_id", "order_id", "user_id", "payment_type",
            "payment_amount", "payment_status",
            "create_time", "pay_time", "callback_time",
        ])
        self.w_pay_detail = CsvWriter(d, "payment_detail.csv", [
            "id", "payment_id", "order_id", "sku_id",
            "amount", "create_time",
        ])
        self.w_invoice = CsvWriter(d, "payment_invoice.csv", [
            "invoice_id", "order_id", "user_id", "invoice_type",
            "invoice_title", "amount", "create_time",
        ])
        self.w_refund = CsvWriter(d, "order_refund_info.csv", [
            "refund_id", "order_id", "user_id", "sku_id",
            "refund_amount", "refund_status", "reason",
            "apply_time", "audit_time", "complete_time",
        ])
        self.w_cart = CsvWriter(d, "cart_info.csv", [
            "cart_id", "user_id", "sku_id", "sku_num",
            "is_ordered", "create_time", "operate_time",
        ])
        self.w_favor = CsvWriter(d, "favor_info.csv", [
            "favor_id", "user_id", "sku_id",
            "create_time", "cancel_time", "is_cancel",
        ])
        self.w_comment = CsvWriter(d, "comment_info.csv", [
            "comment_id", "order_id", "user_id", "sku_id",
            "appraise", "content", "create_time", "operate_time",
        ])
        self.w_after = CsvWriter(d, "after_sales.csv", [
            "after_sales_id", "order_id", "user_id", "sku_id",
            "type", "status", "reason",
            "apply_time", "complete_time",
        ])
        self.w_coupon_use = CsvWriter(d, "coupon_use.csv", [
            "use_id", "coupon_id", "user_id", "order_id",
            "use_time", "discount_amount", "receive_record_id",
        ], append=True)

    def close_writers(self):
        # 将仍未终态的 pending 订单以当前状态写出
        for oid, o in self.pending_orders.items():
            self._write_order_row(o)
        self.pending_orders.clear()
        for attr in dir(self):
            if attr.startswith('w_'):
                getattr(self, attr).close()

    # ── 状态日志写入 ──
    def _log_status(self, order_id, status_code, operate_time):
        """Feature #19: 每次状态变更写一条 status_log"""
        self.status_log_id_seq += 1
        self.w_status.write_row([
            self.status_log_id_seq, order_id,
            status_code, fmt_datetime(operate_time),
        ])

    # ── 创建新订单 ──
    def _create_new_order(self, day: date, uid: int, trace_id: str):
        self.order_id_seq += 1
        oid = self.order_id_seq
        fate = choose_fate(config.ORDER_FATE_WEIGHTS)
        user = self.users[uid]

        # 创建时间 (Feature #1 零点漂移)
        is_drift = should_midnight_drift()
        if is_drift:
            create_time = midnight_drift_time(day)
        else:
            create_time = random_time_on_day(day)

        # SKU选择 (Feature #6 热点 + 品类聚合: 70%同品类)
        n_items = random.randint(1, 5)
        gender = user.get("gender", 0)
        age_str = user.get("birthday", "")
        try:
            birth_year = int(age_str[:4]) if age_str else 1985
            age = 2026 - birth_year
        except (ValueError, TypeError):
            age = 30
        # 30% 概率按性别/年龄偏好选品
        bias_pools = []
        if gender == 2 and self._female_sku_ids:  # 女性
            bias_pools = self._female_sku_ids
        elif gender == 1 and self._male_sku_ids:  # 男性
            bias_pools = self._male_sku_ids
        if age < 12 and self._child_sku_ids:
            bias_pools = self._child_sku_ids
        if bias_pools and random.random() < 0.30:
            first_sid = random.choice(bias_pools)
        else:
            first_sid = weighted_choice(self.sku_ids, self.sku_weights)
        chosen_skus = [first_sid]
        anchor_cat3 = self.skus[first_sid].get("cat3_id")
        same_cat_skus = self._cat3_sku_map.get(anchor_cat3, [])
        for _ in range(n_items - 1):
            if same_cat_skus and random.random() < 0.70:
                sid = random.choice(same_cat_skus)
            else:
                sid = weighted_choice(self.sku_ids, self.sku_weights)
            chosen_skus.append(sid)

        # 生成 order_detail
        original_total = 0.0
        details = []
        for sid in chosen_skus:
            self.detail_id_seq += 1
            sku = self.skus[sid]
            price = round(sku["original_price"] * random.uniform(0.85, 1.0), 2)
            qty = random.randint(1, 3)
            line_total = round(price * qty, 2)
            original_total += line_total
            details.append({
                "detail_id": self.detail_id_seq,
                "sku_id": sid, "price": price,
                "qty": qty, "line_total": line_total,
            })
            det_sku_name = sku.get("sku_name", f"SKU{sid:05d}")
            det_merchant_id = sku.get("merchant_id", 1)
            self.w_detail.write_row([
                self.detail_id_seq, oid, sid, det_sku_name,
                price, qty, line_total, det_merchant_id,
                fmt_datetime(create_time), fmt_datetime(create_time),
            ])
        original_total = round(original_total, 2)

        # 优惠计算
        activity_reduce = 0.0
        coupon_reduce = 0.0
        used_receive = None
        if random.random() >= config.NULL_COUPON_RATE:
            # 尝试从该用户的券池中取一张满足门槛的券
            pool = self._user_receive_pool.get(uid)
            if pool:
                # 遍历找满足 condition_amount <= original_total 且已领取且未过期的券
                matched_idx = None
                for pi in range(len(pool) - 1, -1, -1):
                    rec = pool[pi]
                    cp = self.coupons.get(rec["coupon_id"], {})
                    cond = cp.get("condition_amount", 0)
                    # 校验: 领取时间 <= 下单时间
                    recv_t = rec.get("receive_time")
                    if recv_t and recv_t > create_time:
                        continue
                    # 校验: 券未过期 (expire_date >= 当天)
                    exp_d = rec.get("expire_date")
                    if exp_d and exp_d < day:
                        continue
                    if cond <= original_total:
                        matched_idx = pi
                        break
                if matched_idx is not None:
                    used_receive = pool.pop(matched_idx)
                    cp = self.coupons.get(used_receive["coupon_id"], {})
                    cp_type = cp.get("type", "")
                    if cp_type == "折扣券":
                        disc = float(cp.get("benefit_discount") or 1.0)
                        coupon_reduce = round(original_total * (1 - disc), 2)
                    else:
                        ba = cp.get("benefit_amount", 0)
                        coupon_reduce = round(float(ba), 2) if ba else round(random.uniform(5, 50), 2)
                    # 券抵扣不能超过订单金额
                    coupon_reduce = min(coupon_reduce, original_total)
            # 没有可用券则不使用(不凭空造优惠)
        # 活动满减: 查询真实活动规则, 按金额阶梯匹配
        activity_reduce = 0.0
        if random.random() < 0.3 and self.activities:
            # 筛选当天有效的活动
            valid_aids = [
                aid for aid, info in self.activities.items()
                if info.get("start_date") <= day <= info.get("end_date")
            ]
            if valid_aids:
                aid = random.choice(valid_aids)
                # 校验: 订单SKU是否在活动SKU中
                act_skus = self.activity_sku_map.get(aid, set())
                order_sku_set = set(chosen_skus)
                if order_sku_set & act_skus:  # 至少有一个SKU参与活动
                    # P2: 仅统计参与活动SKU的金额作为满减基准
                    activity_amount = sum(
                        d["line_total"] for d in details
                        if d["sku_id"] in act_skus
                    )
                    rules = self.rules_by_activity.get(aid, [])
                    # 筛选满足门槛的规则, 取最高档
                    best_rule = None
                    for rule in rules:
                        cond = rule.get("condition_amount", 0)
                        if activity_amount >= cond:
                            if best_rule is None or cond > best_rule["condition_amount"]:
                                best_rule = rule
                    if best_rule:
                        if best_rule.get("rule_type") == "满减":
                            activity_reduce = round(float(best_rule.get("benefit_amount", 0)), 2)
                        elif best_rule.get("rule_type") in ("折扣", "秒杀"):
                            disc = float(best_rule.get("benefit_discount") or 1.0)
                            activity_reduce = round(activity_amount * (1 - disc), 2)
        # 会员折扣: 高等级用户享额外折扣
        discount_reduce = 0.0
        u_level = self.users[uid].get("user_level", 1)
        if u_level >= 4 and random.random() < 0.3:
            discount_reduce = round(original_total * random.uniform(0.02, 0.05), 2)
        # 多重优惠互斥: 活动减>0时80%概率不用券; 总折扣不超原价70%
        if activity_reduce > 0 and coupon_reduce > 0 and random.random() < 0.8:
            coupon_reduce = 0.0
        total_reduce = activity_reduce + coupon_reduce + discount_reduce
        max_reduce = original_total * 0.70
        if total_reduce > max_reduce:
            scale = max_reduce / total_reduce
            activity_reduce = round(activity_reduce * scale, 2)
            coupon_reduce = round(coupon_reduce * scale, 2)
            # B4: 末项补差, 避免3路round累积精度丢失
            discount_reduce = round(max_reduce - activity_reduce - coupon_reduce, 2)
        # 运费: 原价满99包邮, 否则5~15元
        discounted_total = original_total - activity_reduce - coupon_reduce - discount_reduce
        if original_total >= 99:
            freight = 0.0
        else:
            freight = round(random.uniform(5, 15), 2)
        total = round(
            max(0.01, original_total - activity_reduce
                - coupon_reduce - discount_reduce + freight), 2)

        # 收货地址: 优先从用户已注册地址中选取 (默认地址优先)
        addrs = self.user_addresses.get(uid)
        if addrs:
            # 优先选默认地址, 否则随机
            default_addrs = [a for a in addrs if a.get("is_default")]
            addr = random.choice(default_addrs) if default_addrs \
                else random.choice(addrs)
            city_id = addr["city_id"]
            province_id = addr["province_id"]
        else:
            city_id = user.get("city_id") or weighted_choice(
                self.city_ids, self.city_weights)
            province_id = user.get("province_id", 1)

        # 首单
        is_first = 1 if uid not in self.user_first_order else 0
        self.user_first_order.add(uid)

        # merchant_id (按金额最大的商户, 多商户订单取主商户)
        merchant_amounts = {}
        for det in details:
            mid = self.skus[det["sku_id"]].get("merchant_id", 1)
            merchant_amounts[mid] = merchant_amounts.get(mid, 0) + det["line_total"]
        merchant_id = max(merchant_amounts, key=merchant_amounts.get)

        # 支付方式 / 来源
        pay_type = weighted_choice(PAYMENT_TYPES, PAYMENT_TYPE_W)
        src_type = weighted_choice(SOURCE_TYPES, SOURCE_TYPE_W)
        session_id = f"S{oid:08d}"
        sess_list = getattr(self, 'user_session_map', {}).get(uid)
        if sess_list:
            session_id = random.choice(sess_list)

        order = {
            "order_id": oid, "user_id": uid,
            "merchant_id": merchant_id,
            "province_id": province_id, "city_id": city_id,
            "fate": fate, "total_amount": total,
            "original_total_amount": original_total,
            "activity_reduce": activity_reduce,
            "coupon_reduce": coupon_reduce,
            "discount_reduce": discount_reduce,
            "freight": freight,
            "pay_type": pay_type, "src_type": src_type,
            "is_first": is_first,
            "session_id": session_id, "trace_id": trace_id,
            "create_time": create_time,
            "current_status": "created",
            "_is_drift": is_drift,
            "payment_time": None, "send_time": None,
            "receive_time": None, "complete_time": None,
            "details": details,
        }

        # order_info 仅在终态(completed/cancelled/refunded)或 close 时写入，
        # 避免同一 order_id 出现多行

        # 写 status_log: 创建
        self._log_status(oid, STATUS_MAP["created"], create_time)

        # 写 coupon_use (关联真实领取记录)
        if used_receive and coupon_reduce > 0:
            self._coupon_use_seq += 1
            use_time = create_time + timedelta(minutes=random.randint(0, 5))
            self.w_coupon_use.write_row([
                self._coupon_use_seq,
                used_receive["coupon_id"],
                uid, oid,
                fmt_datetime(use_time),
                coupon_reduce,
                used_receive["record_id"],
            ])

        # 加入 pending 队列
        self.pending_orders[oid] = order

        return order

    def _write_order_row(self, o):
        """写入/更新 order_info 一行"""
        self.w_order.write_row([
            o["order_id"], o["user_id"], o["merchant_id"],
            o["province_id"], o["city_id"],
            STATUS_MAP[o["current_status"]],
            o["total_amount"], o["original_total_amount"],
            o["activity_reduce"], o["coupon_reduce"],
            o["discount_reduce"], o["freight"],
            o["pay_type"], o["src_type"],
            o["is_first"], o["session_id"],
            o.get("trace_id", ""),
            fmt_datetime(o["create_time"]),
            fmt_datetime(o["payment_time"]),
            fmt_datetime(o["send_time"]),
            fmt_datetime(o["receive_time"]),
            fmt_datetime(o["complete_time"]),
            fmt_datetime(o.get("last_operate_time", o["create_time"])),
        ])

    # ── 历史订单状态推进 ──
    def _advance_orders(self, current_day: date):
        """推进 pending_orders 中需要变更的订单（同一天可多步推进）"""
        now = datetime(current_day.year, current_day.month,
                       current_day.day, 23, 59, 59)
        to_remove = []
        for oid, o in list(self.pending_orders.items()):
            fate = o["fate"]
            prev_status = None
            # 循环推进直到状态不再变化或到达终态
            while o["current_status"] != prev_status:
                prev_status = o["current_status"]
                if prev_status == "created":
                    self._advance_from_created(o, now, fate)
                elif prev_status == "paid":
                    self._advance_from_paid(o, now, fate)
                elif prev_status == "shipped":
                    self._advance_from_shipped(o, now, fate)
                elif prev_status == "received":
                    self._advance_from_received(o, now, fate)
                else:
                    break  # 终态

            # 终态订单移除 pending，写入最终快照
            if o["current_status"] in ("completed", "cancelled", "refunded"):
                self._write_order_row(o)
                to_remove.append(oid)

        for oid in to_remove:
            del self.pending_orders[oid]

    def _advance_from_created(self, o, now, fate):
        """created → paid / cancelled / 超时"""
        ct = o["create_time"]
        # 路径B: 主动取消(30分-3小时), 路径E: 超时未支付(24-48小时)
        if fate == 'B':
            cancel_delay = random.uniform(30, 180)
            cancel_time = add_minutes(ct, cancel_delay)
            if cancel_time <= now:
                o["current_status"] = "cancelled"
                o["last_operate_time"] = cancel_time
                self._log_status(o["order_id"], STATUS_MAP["cancelled"],
                                 cancel_time)
            return
        if fate == 'E':
            cancel_delay = random.uniform(1440, 2880)
            cancel_time = add_minutes(ct, cancel_delay)
            if cancel_time <= now:
                o["current_status"] = "cancelled"
                o["last_operate_time"] = cancel_time
                self._log_status(o["order_id"], STATUS_MAP["cancelled"],
                                 cancel_time)
            return

        # 路径 A/C/D: 需要支付
        pay_delay = pay_delay_minutes()
        pay_time = add_minutes(ct, pay_delay)

        # Feature #1 零点漂移: 跨天支付
        if o.get("_is_drift"):
            pay_time = midnight_drift_next_day(ct.date())

        if pay_time <= now:
            o["payment_time"] = pay_time
            o["current_status"] = "paid"
            o["last_operate_time"] = pay_time
            self._log_status(o["order_id"], STATUS_MAP["paid"], pay_time)
            # COD(货到付款)订单延迟到签收时才生成支付记录
            if o["pay_type"] != 4:
                self._write_payment(o)
            # 只统计已付款订单用于标签计算
            self._update_user_stats(
                o["user_id"], pay_time.date(), o["total_amount"])

    def _advance_from_paid(self, o, now, fate):
        """paid → shipped / refunded"""
        pt = o["payment_time"]
        # 路径D: 支付后退款
        if fate == 'D':
            refund_delay = random.uniform(60, 1440)
            refund_time = add_minutes(pt, refund_delay)
            if refund_time <= now:
                o["current_status"] = "refunded"
                o["last_operate_time"] = refund_time
                self._log_status(o["order_id"], STATUS_MAP["refunded"],
                                 refund_time)
                self._write_refund(o, refund_time)
                self.newly_refunded_today.append(o)
            return

        # 路径A/C: 发货
        ship_hours = ship_delay_hours()
        ship_time = add_hours(pt, ship_hours)
        if ship_time <= now:
            o["send_time"] = ship_time
            o["current_status"] = "shipped"
            o["last_operate_time"] = ship_time
            self._log_status(o["order_id"], STATUS_MAP["shipped"],
                             ship_time)
            self.newly_shipped_today.append(o)

    def _advance_from_shipped(self, o, now, fate):
        """shipped → received"""
        st = o["send_time"]
        recv_days = receive_delay_days()
        recv_time = add_days(st, recv_days)
        if recv_time <= now:
            o["receive_time"] = recv_time
            o["current_status"] = "received"
            o["last_operate_time"] = recv_time
            self._log_status(o["order_id"], STATUS_MAP["received"],
                             recv_time)
            self.newly_received_today.append(o)
            # COD订单在签收时生成支付记录
            if o["pay_type"] == 4:
                o["payment_time"] = recv_time
                self._write_payment(o)

    def _advance_from_received(self, o, now, fate):
        """received → completed / refunded + comment"""
        rt = o["receive_time"]
        # 路径C: 收货后退款
        if fate == 'C':
            refund_delay = random.uniform(60, 4320)  # 1h~3天
            refund_time = add_minutes(rt, refund_delay)
            if refund_time <= now:
                o["current_status"] = "refunded"
                o["last_operate_time"] = refund_time
                self._log_status(o["order_id"], STATUS_MAP["refunded"],
                                 refund_time)
                self._write_refund(o, refund_time, full_refund=False)
                self.newly_refunded_today.append(o)
                # 部分退款后也有after_sales
                if random.random() < 0.5:
                    self._write_after_sales(o, refund_time)
            return

        # 路径A: 自动完成
        comp_days = complete_delay_days()
        comp_time = add_days(rt, comp_days)
        if comp_time <= now:
            o["complete_time"] = comp_time
            o["current_status"] = "completed"
            o["last_operate_time"] = comp_time
            self._log_status(o["order_id"], STATUS_MAP["completed"],
                             comp_time)
            # 完成后写评价
            if random.random() < 0.6:
                self._write_comment(o, comp_time)

    # ── 支付信息 ──
    def _write_payment(self, o):
        """生成 payment_info + payment_detail, Feature #5 重复, Feature #8 迟到"""
        self.payment_id_seq += 1
        pid = self.payment_id_seq
        pay_time = o["payment_time"]
        # Feature #8: 3% callback 延迟
        if should_late_callback():
            cb_time = add_hours(pay_time, late_callback_delay_hours())
        else:
            cb_time = add_minutes(pay_time, random.uniform(0.1, 5))

        # Feature #10: 0.5% 时间异常 (callback早于pay但不早于create)
        if should_time_anomaly():
            cb_time = add_hours(pay_time, -random.uniform(1, 5))
            cb_time = max(cb_time, o["create_time"])

        # 3% 状态为 pending(0)表示"待确认", 其余为1(已支付)
        pay_status = 0 if random.random() < 0.03 else 1
        row = [
            pid, o["order_id"], o["user_id"], o["pay_type"],
            o["total_amount"], pay_status,
            fmt_datetime(o["create_time"]),
            fmt_datetime(pay_time), fmt_datetime(cb_time),
        ]
        self.w_payment.write_row(row)

        # Feature #5: 1% 支付回调重复
        if random.random() < config.DUP_PAYMENT_RATE:
            self.w_payment.write_row(row)

        # payment_detail: 每个SKU一条
        # 按 line_total 比例分配已支付的商品金额(扣运费), 末行补差
        paid_merch = round(o["total_amount"] - o.get("freight", 0.0), 2)
        orig = o.get("original_total_amount", 0.0) or paid_merch
        ratio = paid_merch / orig if orig > 0 else 1.0
        dets = o["details"]
        alloc_sum = 0.0
        for idx, det in enumerate(dets):
            self.pay_detail_id_seq += 1
            if idx < len(dets) - 1:
                amt = round(det["line_total"] * ratio, 2)
            else:
                amt = round(paid_merch - alloc_sum, 2)
            alloc_sum += amt
            self.w_pay_detail.write_row([
                self.pay_detail_id_seq, pid, o["order_id"],
                det["sku_id"], max(0.01, amt),
                fmt_datetime(pay_time),
            ])

        # 发票 (约25%订单开票)
        if random.random() < 0.25:
            self.invoice_id_seq += 1
            inv_type = random.choice(["个人", "企业"])
            if inv_type == "企业":
                inv_title = random.choice(self._COMPANY_POOL)
            else:
                inv_title = random_chinese_name()
            self.w_invoice.write_row([
                self.invoice_id_seq, o["order_id"], o["user_id"],
                inv_type, inv_title,
                o["total_amount"], fmt_datetime(pay_time),
            ])

    # ── 退款 ──
    def _write_refund(self, o, refund_time, full_refund=True):
        """Feature #3 累积快照, Feature #11 金额不一致"""
        audit_time = add_hours(refund_time, random.uniform(1, 48))
        comp_time = add_hours(audit_time, random.uniform(1, 72))
        reasons = ["质量问题", "不想要了", "发错货", "尺码不合", "其他"]
        reason = random.choice(reasons)
        # 退款状态: 1=申请中, 2=已审核, 3=已完成, 4=被驳回
        # 95%完成, 3%审核中, 2%驳回
        refund_status = random.choices(
            [3, 2, 4], weights=[0.95, 0.03, 0.02], k=1)[0]
        if refund_status == 2:
            comp_time = None   # 审核中无完成时间
        elif refund_status == 4:
            comp_time = None   # 驳回无完成时间

        if full_refund:
            # Path D: 全单退款, 为每个SKU明细行各生成一条退款记录
            total = o["total_amount"]
            dets = o["details"]
            orig_sum = sum(d["line_total"] for d in dets)
            alloc_sum = 0.0
            for idx, det in enumerate(dets):
                if idx < len(dets) - 1:
                    amt = round(det["line_total"] / orig_sum * total, 2) \
                        if orig_sum > 0 else round(total / len(dets), 2)
                else:
                    amt = round(total - alloc_sum, 2)
                alloc_sum += amt
                # Feature #11: 0.1% 退款>订单金额
                if random.random() < config.AMOUNT_ANOMALY_RATE:
                    amt = round(o["total_amount"] * 1.1, 2)
                self.refund_id_seq += 1
                self.w_refund.write_row([
                    self.refund_id_seq, o["order_id"], o["user_id"],
                    det["sku_id"], amt, refund_status, reason,
                    fmt_datetime(refund_time),
                    fmt_datetime(audit_time),
                    fmt_datetime(comp_time),
                ])
        else:
            # Path C: 收货后部分退款, 随机退一个SKU
            det = random.choice(o["details"])
            refund_amount = det["line_total"]
            if random.random() < config.AMOUNT_ANOMALY_RATE:
                refund_amount = round(o["total_amount"] * 1.1, 2)
            self.refund_id_seq += 1
            self.w_refund.write_row([
                self.refund_id_seq, o["order_id"], o["user_id"],
                det["sku_id"], refund_amount, refund_status, reason,
                fmt_datetime(refund_time),
                fmt_datetime(audit_time),
                fmt_datetime(comp_time),
            ])

    # ── 评价(组合生成, 500+种) ──
    _GOOD_SUBJECTS = ["质量", "做工", "材质", "手感", "颜色", "功能", "外观", "包装"]
    _GOOD_ADJS = ["很好", "不错", "超赞", "精细", "满意", "出色", "超值"]
    _GOOD_TAILS = [
        "推荐购买", "会回购", "五星好评", "值得入手",
        "强烈推荐", "已推荐给朋友", "比预期好", "非常惊喜",
        "物流也快", "客服态度好", "包装完好", "送礼也合适",
    ]
    _MID_SUBJECTS = ["质量", "做工", "包装", "物流", "色差", "功能"]
    _MID_ADJS = ["一般", "还行", "凑合", "中规中矩", "没惊喜"]
    _MID_TAILS = [
        "用用看吧", "能接受", "下次不一定买", "性价比一般",
        "和想象中有差距", "有小瑕疵", "发货慢了点",
    ]
    _BAD_SUBJECTS = ["质量", "做工", "材质", "包装", "颜色", "味道"]
    _BAD_ADJS = ["太差", "很失望", "粗糙", "不符", "有问题"]
    _BAD_TAILS = [
        "后悔购买", "建议下架", "浪费钱", "不推荐",
        "客服态度差", "用了就坏", "和描述不符", "要求退款",
    ]
    # R2: 口语化/emoji/长评补充素材
    _EMOJIS = ["👍", "❤️", "😊", "🎉", "💯", "⭐", "🔥", "😍",
               "👏", "✨", "😭", "💔", "😅", "🤔", "😠", "👎"]
    _COLLOQUIAL_GOOD = [
        "宝贝收到了，真的太棒了！", "真心好用，安利给姐妹们！",
        "买了三次了，一如既往地好", "等了好久终于到手了，开心！",
        "性价比超高，闭眼入！", "用了一周，确实不错，回购+1",
        "划算划算！比实体店便宜好多", "东西超级好，下次还来！",
    ]
    _COLLOQUIAL_MID = [
        "emmm就那样吧，不功不过", "收到了，和图片有点差距",
        "第一次买，还行，观望中", "马马虎虎，这个价位也就这样了",
        "没有想象中那么好用", "包装有点简陋",
    ]
    _COLLOQUIAL_BAD = [
        "服了，这质量对得起这价格吗？", "差评！收到就后悔了",
        "用了两天就坏了，什么玩意儿", "跟卖家秀差太远了吧！",
        "退退退！完全不行", "买家秀vs卖家秀，被骗了",
    ]

    @staticmethod
    def _gen_comment(subjects, adjs, tails):
        """R2: 多风格评论生成 — 模板/口语/emoji/长评随机混合"""
        style = random.random()
        if style < 0.55:
            # 55% 模板式
            base = f"{random.choice(subjects)}{random.choice(adjs)}，{random.choice(tails)}"
        elif style < 0.80:
            # 25% 口语化
            if tails is OrderEngine._GOOD_TAILS:
                base = random.choice(OrderEngine._COLLOQUIAL_GOOD)
            elif tails is OrderEngine._BAD_TAILS:
                base = random.choice(OrderEngine._COLLOQUIAL_BAD)
            else:
                base = random.choice(OrderEngine._COLLOQUIAL_MID)
        else:
            # 20% 长评: 2-3句拼接
            sents = []
            for _ in range(random.randint(2, 3)):
                sents.append(f"{random.choice(subjects)}{random.choice(adjs)}")
            base = "，".join(sents) + "。" + random.choice(tails)
        # 30% 追加emoji
        if random.random() < 0.30:
            n_emoji = random.randint(1, 3)
            base += "".join(random.choices(OrderEngine._EMOJIS, k=n_emoji))
        return base
    _COMPANY_POOL = [
        # 互联网科技
        "华为技术有限公司", "阿里巴巴集团", "腾讯科技有限公司",
        "字节跳动有限公司", "百度在线网络技术有限公司",
        "京东集团股份有限公司", "小米科技有限责任公司", "网易有限公司",
        "美团科技有限公司", "拼多多有限公司", "滴滴出行科技有限公司",
        "快手科技有限公司", "携程旅游网络技术有限公司",
        # 通信/运营商
        "中国移动通信集团", "中国电信集团有限公司", "中国联合网络通信集团",
        "中国铁塔股份有限公司",
        # 制造业
        "比亚迪股份有限公司", "宁德时代新能源科技股份有限公司",
        "格力电器股份有限公司", "美的集团股份有限公司",
        "海尔智家股份有限公司", "联想集团有限公司",
        "三一重工股份有限公司", "中国中车股份有限公司",
        # 零售/消费
        "永辉超市股份有限公司", "大润发商业有限公司",
        "苏宁易购集团股份有限公司", "国美零售控股有限公司",
        "名创优品国际控股有限公司", "盒马网络科技有限公司",
        # 金融
        "中国平安保险集团", "招商银行股份有限公司",
        "蚂蚁科技集团股份有限公司", "陆金所控股有限公司",
        # 医疗/医药
        "同仁堂国药有限公司", "云南白药集团股份有限公司",
        "恒瑞医药股份有限公司", "华润三九医药股份有限公司",
        # 教育/传媒
        "好未来教育集团", "新东方教育科技集团",
        "中国国际电视台", "湖南广播电视台",
        # 地产/建筑
        "万科企业股份有限公司", "碧桂园控股有限公司",
        "中国建筑国际控股有限公司",
    ]

    def _write_comment(self, o, after_time):
        """状态≥3(已收货)才可评价"""
        comment_time = add_hours(after_time, random.uniform(0.5, 72))
        app = random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1], k=1)[0]
        if app == 1:
            content = self._gen_comment(self._GOOD_SUBJECTS, self._GOOD_ADJS, self._GOOD_TAILS)
        elif app == 2:
            content = self._gen_comment(self._MID_SUBJECTS, self._MID_ADJS, self._MID_TAILS)
        else:
            content = self._gen_comment(self._BAD_SUBJECTS, self._BAD_ADJS, self._BAD_TAILS)
        det = random.choice(o["details"])
        self.comment_id_seq += 1
        self.w_comment.write_row([
            self.comment_id_seq, o["order_id"], o["user_id"],
            det["sku_id"], app, content,
            fmt_datetime(comment_time), fmt_datetime(comment_time),
        ])

    # ── 售后 ──
    def _write_after_sales(self, o, apply_time):
        as_types = ["退货", "换货", "维修"]
        as_type = random.choice(as_types)
        reasons = ["质量问题", "不满意", "发错货", "其他"]
        comp_time = add_days(apply_time, random.uniform(1, 7))
        det = random.choice(o["details"])
        self.after_sales_id_seq += 1
        self.w_after.write_row([
            self.after_sales_id_seq, o["order_id"], o["user_id"],
            det["sku_id"], as_type, "completed",
            random.choice(reasons),
            fmt_datetime(apply_time), fmt_datetime(comp_time),
        ])

    # ── 购物车/收藏 ──
    def _write_carts(self, day: date, dau_users: list):
        """每天 ~20000 条购物车"""
        n = int(len(dau_users) * 0.6)
        for _ in range(n):
            uid = random.choice(dau_users)
            sid = weighted_choice(self.sku_ids, self.sku_weights)
            qty = random.randint(1, 3)
            ct = random_time_on_day(day)
            is_ordered = random.choices([0, 1], weights=[0.6, 0.4], k=1)[0]
            self.cart_id_seq += 1
            self.w_cart.write_row([
                self.cart_id_seq, uid, sid, qty, is_ordered,
                fmt_datetime(ct), fmt_datetime(ct),
            ])

    def _write_favors(self, day: date, dau_users: list):
        """每天 ~8000 条收藏"""
        n = int(len(dau_users) * 0.25)
        for _ in range(n):
            uid = random.choice(dau_users)
            sid = weighted_choice(self.sku_ids, self.sku_weights)
            ct = random_time_on_day(day)
            is_cancel = random.choices([0, 1], weights=[0.8, 0.2], k=1)[0]
            cancel_t = fmt_datetime(add_hours(ct, random.randint(1, 48))) \
                if is_cancel else ""
            self.favor_id_seq += 1
            self.w_favor.write_row([
                self.favor_id_seq, uid, sid,
                fmt_datetime(ct), cancel_t, is_cancel,
            ])

    # ── 每日处理入口 ──
    def process_day(self, day: date, dau_users: list):
        """
        每日处理:
        1) 推进历史订单状态 (5h)
        2) 生成新订单 (5d)
        3) 生成购物车/收藏
        返回当日新建订单列表 (供 shipment_engine 等消费)
        """
        # 每日重置追踪列表
        self.newly_shipped_today = []
        self.newly_received_today = []
        self.newly_refunded_today = []

        # 1) 推进历史订单
        self._advance_orders(day)

        # 2) 生成新订单 (按用户level加权抽选, 高level下单多)
        n_orders = random.randint(
            config.DAILY_ORDER_MIN, config.DAILY_ORDER_MAX)
        dau_weights = [self._user_order_weights.get(u, 1) for u in dau_users]
        day_orders = []
        for i in range(n_orders):
            uid = random.choices(dau_users, weights=dau_weights, k=1)[0]
            # Feature #16: 10% 有 trace_id
            trace_id = ""
            if random.random() < config.FULL_TRACE_RATE:
                trace_id = f"T{self.order_id_seq + 1:08d}"
            order = self._create_new_order(day, uid, trace_id)
            day_orders.append(order)

        # 3) 购物车 + 收藏
        self._write_carts(day, dau_users)
        self._write_favors(day, dau_users)

        return day_orders
