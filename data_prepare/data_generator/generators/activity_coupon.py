"""
Phase4: 活动优惠券与营销生成器
对应 plan.md Phase 4:
  activity_info(50) / activity_rule(120) / activity_sku(3000)
  campaign_info(30)
  coupon_info(80) / coupon_receive(500000) / coupon_use(200000)
"""
import random
from datetime import datetime, timedelta, date

import config
from utils.csv_writer import CsvWriter
from utils.time_utils import fmt_datetime, fmt_date


# ========== activity_info (50) ==========
_ACT_TYPES = ["满减", "折扣", "满赠", "秒杀"]
_ACT_TYPE_W = [0.40, 0.30, 0.15, 0.15]
_ACT_THEMES = [
    "春季焕新", "三月大促", "品质生活节", "踏青季", "女神节",
    "超级品牌日", "限时抢购", "周末特惠", "会员专享", "新品首发",
    "清仓特卖", "品类狂欢", "节日特惠", "春日精选", "惊喜礼遇",
    "品牌盛典", "爆款直降", "满额好礼", "今日必抢", "价格风暴",
    "甄选好物", "尝鲜特权", "黄金会员日", "限量秒杀", "三月特惠",
    "春季上新", "全场折扣", "超值推荐", "热卖爆款", "惠享生活",
    "春暖焕新", "三月好物节", "品类精选", "极致优惠", "感恩回馈",
    "口碑好货", "爆品直播", "百亿补贴", "拼团优惠", "夜间限定",
    "午间特惠", "国货精品", "品质低价", "全民狂欢", "今日主题",
    "生活好物", "健康精品", "家居特惠", "时尚新潮", "数码焕新",
]
# R1: 活动名称多样化组件
_ACT_PREFIXES = ["", "超级", "限时", "年度", "特别", "VIP", "全场", "极速"]
_ACT_CATEGORIES = [
    "数码", "家电", "美妆", "服饰", "食品", "母婴", "运动", "家居",
    "图书", "生鲜", "个护", "箱包", "鞋靴", "珠宝", "汽车用品",
]


def gen_activity_info(out_dir: str):
    w = CsvWriter(out_dir, "activity_info.csv",
                  ["activity_id", "activity_name", "activity_type",
                   "start_date", "end_date",
                   "create_time", "operate_time"])
    activities = {}
    base = date(2026, 3, 1)
    now_str = fmt_datetime(datetime(2026, 2, 28, 10, 0, 0))
    for i in range(1, 51):
        atype = random.choices(_ACT_TYPES, weights=_ACT_TYPE_W, k=1)[0]
        start_off = random.randint(0, 25)
        dur = random.randint(3, 10)
        sd = base + timedelta(days=start_off)
        ed = sd + timedelta(days=dur)
        theme = _ACT_THEMES[(i - 1) % len(_ACT_THEMES)]
        # R1: 活动名多样化 — 随机组合前缀+品类+主题
        prefix = random.choice(_ACT_PREFIXES)
        cat = random.choice(_ACT_CATEGORIES)
        round_num = (i - 1) // len(_ACT_THEMES)
        suffix = f"第{round_num + 1}期" if round_num > 0 else ""
        aname = f"{prefix}{theme}{suffix}·{cat}{atype}专场"
        w.write_row([i, aname, atype,
                     fmt_date(datetime(sd.year, sd.month, sd.day)),
                     fmt_date(datetime(ed.year, ed.month, ed.day)),
                     now_str, now_str])
        activities[i] = {
            "activity_id": i, "type": atype,
            "start_date": sd, "end_date": ed,
        }
    w.close()
    return activities


# ========== activity_rule (120) ==========
def gen_activity_rule(out_dir: str, activities: dict):
    """每个活动 2~3 条规则"""
    w = CsvWriter(out_dir, "activity_rule.csv",
                  ["rule_id", "activity_id", "rule_type",
                   "condition_amount", "benefit_amount",
                   "benefit_discount", "benefit_level"])
    rule_id = 1
    rules_by_activity = {}  # {activity_id: [rule_dict, ...]}
    for aid, info in activities.items():
        n = random.randint(2, 3)
        rules_by_activity[aid] = []
        for j in range(n):
            if info["type"] == "秒杀":
                cond = 0
                discount = round(random.uniform(0.30, 0.50), 2)
                w.write_row([rule_id, aid, "秒杀", cond,
                             "", discount, j + 1])
                rules_by_activity[aid].append({
                    "rule_type": "秒杀", "condition_amount": cond,
                    "benefit_discount": discount,
                })
            elif info["type"] in ("满减", "满赠"):
                cond = random.choice([99, 199, 299, 499])
                benefit = random.choice([10, 20, 30, 50])
                discount = ""
                actual_rule_type = info["type"]  # 保留 满赠/满减 的真实类型
                w.write_row([rule_id, aid, actual_rule_type, cond,
                             benefit, discount, j + 1])
                rules_by_activity[aid].append({
                    "rule_type": actual_rule_type, "condition_amount": cond,
                    "benefit_amount": benefit,
                })
            else:
                cond = random.choice([0, 99, 199])
                discount = round(random.uniform(0.5, 0.95), 2)
                w.write_row([rule_id, aid, "折扣", cond,
                             "", discount, j + 1])
                rules_by_activity[aid].append({
                    "rule_type": "折扣", "condition_amount": cond,
                    "benefit_discount": discount,
                })
            rule_id += 1
    w.close()
    return rules_by_activity


# ========== activity_sku (3000) ==========
def gen_activity_sku(out_dir: str, activities: dict, skus: dict):
    """每个活动关联 ~60 个SKU, 多对多桥接"""
    w = CsvWriter(out_dir, "activity_sku.csv",
                  ["id", "activity_id", "sku_id", "create_time"])
    sku_ids = list(skus.keys())
    row_id = 1
    target = 3000
    now_str = fmt_datetime(datetime(2026, 2, 28, 10, 0, 0))
    activity_sku_map = {}  # {activity_id: set(sku_id)}
    for aid in activities:
        n = target // len(activities)
        chosen = random.sample(sku_ids, k=min(n, len(sku_ids)))
        activity_sku_map[aid] = set()
        for sid in chosen:
            if row_id > target:
                break
            w.write_row([row_id, aid, sid, now_str])
            activity_sku_map[aid].add(sid)
            row_id += 1
        if row_id > target:
            break
    w.close()
    return activity_sku_map


# ========== campaign_info (30) ==========
_CAMPAIGN_TYPES = ["S", "A", "B", "C"]  # S大促/A品类/B会员/C日常
_CAMPAIGN_TYPE_W = [0.10, 0.25, 0.25, 0.40]
_GMV_BOOST = {"S": 3.5, "A": 1.8, "B": 1.3, "C": 1.0}
_CAMPAIGN_NAMES = {
    "S": ["38女王节大促", "春季品质节", "三月超级大促", "开春焕新节", "春日狂欢节"],
    "A": ["美妆品类周", "数码狂欢节", "家装焕新季", "母婴用品节", "食品生鲜节",
          "服饰尚新周", "运动户外季", "家电超级日"],
    "B": ["会员专属月卡", "VIP等级权益日", "积分兑换狂欢", "会员日专享",
          "超级会员周", "黑卡专属福利"],
    "C": ["每日特惠", "限时秒杀", "新人专享", "周末惊喜价", "品质好物推荐",
          "今日必买", "爆款直降", "超值精选", "午间抢购", "晚间特卖"],
}


def gen_campaign_info(out_dir: str):
    w = CsvWriter(out_dir, "campaign_info.csv",
                  ["campaign_id", "campaign_name", "campaign_type",
                   "start_date", "end_date", "gmv_boost"])
    campaigns = {}
    base = date(2026, 3, 1)
    for i in range(1, 31):
        ctype = random.choices(
            _CAMPAIGN_TYPES, weights=_CAMPAIGN_TYPE_W, k=1)[0]
        start_off = random.randint(0, 25)
        dur = random.randint(3, 10)
        sd = base + timedelta(days=start_off)
        ed = sd + timedelta(days=dur)
        boost = _GMV_BOOST[ctype] * random.uniform(0.8, 1.2)
        _pool = _CAMPAIGN_NAMES[ctype]
        cname = _pool[(i - 1) % len(_pool)]
        w.write_row([
            i, cname, ctype,
            fmt_date(datetime(sd.year, sd.month, sd.day)),
            fmt_date(datetime(ed.year, ed.month, ed.day)),
            round(boost, 2),
        ])
        campaigns[i] = {
            "campaign_id": i, "campaign_type": ctype,
            "start_date": sd, "end_date": ed,
            "gmv_boost": round(boost, 2),
        }
    w.close()
    return campaigns


# ========== coupon_info (80) ==========
_COUPON_TYPES = ["满减券", "折扣券", "无门槛券"]
_COUPON_TYPE_W = [0.50, 0.30, 0.20]


def gen_coupon_info(out_dir: str):
    w = CsvWriter(out_dir, "coupon_info.csv",
                  ["coupon_id", "coupon_name", "coupon_type",
                   "condition_amount", "benefit_amount",
                   "benefit_discount", "start_date", "end_date",
                   "create_time", "operate_time"])
    coupons = {}
    base = date(2026, 3, 1)
    now_str = fmt_datetime(datetime(2026, 2, 28, 10, 0, 0))
    for i in range(1, 81):
        ctype = random.choices(
            _COUPON_TYPES, weights=_COUPON_TYPE_W, k=1)[0]
        sd = base + timedelta(days=random.randint(0, 20))
        ed = sd + timedelta(days=random.randint(7, 30))
        if ctype == "满减券":
            cond = random.choice([50, 100, 200, 300])
            benefit = random.choice([5, 10, 20, 30, 50])
            disc = ""
        elif ctype == "折扣券":
            cond = random.choice([0, 100, 200])
            benefit = ""
            disc = round(random.uniform(0.7, 0.95), 2)
        else:
            cond = 0
            benefit = random.choice([3, 5, 10])
            disc = ""
        if ctype == "满减券":
            cname = f"满{cond}减{benefit}专享券"
        elif ctype == "折扣券":
            cname = f"{int(disc*10)}折优惠券" if disc else f"折扣券"
        else:
            cname = f"{benefit}元无门槛券"
        w.write_row([
            i, cname, ctype,
            cond, benefit, disc,
            fmt_date(datetime(sd.year, sd.month, sd.day)),
            fmt_date(datetime(ed.year, ed.month, ed.day)),
            now_str, now_str,
        ])
        coupons[i] = {
            "coupon_id": i, "type": ctype,
            "start_date": sd, "end_date": ed,
            "condition_amount": cond,
            "benefit_amount": benefit if benefit != "" else 0,
            "benefit_discount": disc if disc != "" else 1.0,
        }
    w.close()
    return coupons


# ========== coupon_receive (500,000) ==========
def gen_coupon_receive(out_dir: str, coupons: dict, users: dict):
    """
    coupon_receive: 领取记录
    status: unused / used / expired
    后续 coupon_use 会将部分 used 记录关联订单
    """
    w = CsvWriter(out_dir, "coupon_receive.csv",
                  ["record_id", "coupon_id", "user_id",
                   "receive_time", "expire_date", "status"])
    user_ids = list(users.keys())
    coupon_ids = list(coupons.keys())
    receives = {}  # record_id -> info
    for rid in range(1, 500001):
        cid = random.choice(coupon_ids)
        uid = random.choice(user_ids)
        cp = coupons[cid]
        # receive_time 在券有效期内
        sd = cp["start_date"]
        ed = cp["end_date"]
        offset = random.randint(0, max(0, (ed - sd).days))
        recv_dt = datetime(sd.year, sd.month, sd.day,
                           random.randint(8, 22),
                           random.randint(0, 59))
        recv_dt = recv_dt + timedelta(days=offset)
        # status: ~40% used, ~30% unused, ~30% expired
        r = random.random()
        if r < 0.40:
            status = "used"
        elif r < 0.70:
            status = "unused"
        else:
            status = "expired"
        w.write_row([
            rid, cid, uid,
            fmt_datetime(recv_dt),
            fmt_date(datetime(ed.year, ed.month, ed.day)),
            status,
        ])
        receives[rid] = {
            "record_id": rid, "coupon_id": cid, "user_id": uid,
            "receive_time": recv_dt, "status": status,
            "expire_date": ed,
        }
    w.close()
    return receives


# ========== coupon_use ==========
# coupon_use 完全由 Phase5 order_engine 实时写入(仅记录实际关联订单的券),
# 此处仅写出CSV表头供Phase5 append模式使用
def gen_coupon_use_header(out_dir: str):
    """写出 coupon_use.csv 表头, Phase5 以 append 模式追加实际记录"""
    w = CsvWriter(out_dir, "coupon_use.csv",
                  ["use_id", "coupon_id", "user_id", "order_id",
                   "use_time", "discount_amount", "receive_record_id"])
    w.close()


# ========== 总入口 ==========
def generate_activity_coupon(out_dir: str, skus: dict, users: dict):
    """生成 Phase4 全部 7 张活动优惠券表"""
    print("[Phase4] 生成 activity_info ...")
    activities = gen_activity_info(out_dir)

    print("[Phase4] 生成 activity_rule ...")
    rules_by_activity = gen_activity_rule(out_dir, activities)

    print("[Phase4] 生成 activity_sku ...")
    activity_sku_map = gen_activity_sku(out_dir, activities, skus)

    print("[Phase4] 生成 campaign_info ...")
    campaigns = gen_campaign_info(out_dir)

    print("[Phase4] 生成 coupon_info ...")
    coupons = gen_coupon_info(out_dir)

    print("[Phase4] 生成 coupon_receive ...")
    receives = gen_coupon_receive(out_dir, coupons, users)

    # coupon_use: 仅写表头, 数据由Phase5 OrderEngine append写入
    gen_coupon_use_header(out_dir)
    print("[Phase4] 活动优惠券全部完成 (6张表 + coupon_use表头)")
    return {
        "activities": activities,
        "rules_by_activity": rules_by_activity,
        "activity_sku_map": activity_sku_map,
        "campaigns": campaigns,
        "coupons": coupons,
        "receives": receives,
    }
