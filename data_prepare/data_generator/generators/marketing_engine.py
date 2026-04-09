"""
Phase5: 营销触达/归因/广告投放生成器
对应 plan.md: marketing_touch, campaign_attribution, ad_spend
"""
import random
from datetime import datetime, timedelta, date

import config
from utils.csv_writer import CsvWriter
from utils.time_utils import random_time_on_day, fmt_datetime, fmt_date
from utils.distribution import weighted_choice


class MarketingEngine:
    """营销触达 + 归因 + 广告投放"""

    def __init__(self, out_dir: str, campaigns: dict,
                 channels: dict, users: dict):
        self.out_dir = out_dir
        self.campaigns = campaigns
        self.channels = channels
        self.user_ids = list(users.keys())
        self.touch_id = 0
        self.attribution_id = 0
        self.ad_id = 0

        # 近7天触达记录池 (支持跨天归因)
        self._touch_history = []  # [(touch_dict, day), ...]
        self.day_touches = []

    def open_writers(self):
        d = self.out_dir
        self.w_touch = CsvWriter(d, "marketing_touch.csv", [
            "touch_id", "campaign_id", "user_id",
            "touch_channel", "touch_time", "is_click",
            "touch_type", "creative_id", "crowd_package_id",
        ])
        self.w_attr = CsvWriter(d, "campaign_attribution.csv", [
            "attribution_id", "order_id", "campaign_id",
            "touch_id", "model", "credit",
            "touch_time", "order_time",
        ])
        self.w_ad = CsvWriter(d, "ad_spend.csv", [
            "id", "campaign_id", "channel_id", "spend_date",
            "impressions", "clicks", "cost",
            "cpc", "cpm", "cpa", "conversions",
        ])

    def close_writers(self):
        self.w_touch.close()
        self.w_attr.close()
        self.w_ad.close()

    def process_day(self, day: date, dau_users: list,
                    day_orders: list):
        """
        每日处理:
        1) 触达 (活动期间向用户发送 push/sms/in_app)
        2) 广告投放 (每日×活动×渠道)
        3) 归因 (已支付订单匹配触达触点)
        """
        self.day_touches = []

        # 清理超过7天的历史触达 (B5: 用 > 保留严格7天)
        from datetime import timedelta as _td
        cutoff = day - _td(days=7)
        self._touch_history = [
            (t, d) for t, d in self._touch_history if d > cutoff
        ]

        # 1) 找出当日活跃的营销活动
        active_camps = [
            c for c in self.campaigns.values()
            if c["start_date"] <= day <= c["end_date"]
        ]
        if not active_camps:
            return

        # 2) 营销触达: 每个活跃活动向部分用户发送
        # 统计每个(campaign, channel)的曝光和点击数 (P2: 供ad_spend使用)
        touch_stats = {}  # {(cid, ch): {"imps": int, "clicks": int}}
        for camp in active_camps:
            cid = camp["campaign_id"]
            # 每个活动每天触达 ~1000 用户
            n_touch = random.randint(500, 1500)
            sample_users = random.sample(
                dau_users, k=min(n_touch, len(dau_users)))
            for uid in sample_users:
                ch = random.choice(config.TOUCH_CHANNELS)
                click_rate = config.TOUCH_CLICK_RATES[ch]
                is_click = 1 if random.random() < click_rate else 0
                # touch_type: send → open → click 漏斗
                if is_click:
                    touch_type = "click"
                elif random.random() < 0.6:
                    touch_type = "open"
                else:
                    touch_type = "send"
                creative = random.choice(config.CREATIVE_IDS)
                crowd = random.choice(config.CROWD_PACKAGES)
                t_time = random_time_on_day(day)
                self.touch_id += 1
                self.w_touch.write_row([
                    self.touch_id, cid, uid,
                    ch, fmt_datetime(t_time), is_click,
                    touch_type, creative, crowd,
                ])
                # 累计 (campaign, channel) 曝光和点击
                key = (cid, ch)
                if key not in touch_stats:
                    touch_stats[key] = {"imps": 0, "clicks": 0}
                touch_stats[key]["imps"] += 1
                if is_click:
                    touch_stats[key]["clicks"] += 1
                if is_click:
                    touch_record = {
                        "touch_id": self.touch_id,
                        "campaign_id": cid,
                        "user_id": uid,
                        "touch_time": t_time,
                    }
                    self.day_touches.append(touch_record)
                    self._touch_history.append((touch_record, day))

        # 3) 归因: 已支付订单匹配触达 (先于ad_spend, 统计实际转化数)
        camp_conversions = self._gen_attribution(day_orders)

        # 4) ad_spend: 每个活跃活动×每个渠道 一行
        # P2: 基于真实touch统计计算展示/点击, conversions用补差法
        channel_ids = list(self.channels.keys())
        n_channels = max(len(channel_ids), 1)
        # 汇总每个campaign的touch总量作为ad_spend基准
        camp_touch_totals = {}
        for (cid_key, _), st in touch_stats.items():
            if cid_key not in camp_touch_totals:
                camp_touch_totals[cid_key] = {"imps": 0, "clicks": 0}
            camp_touch_totals[cid_key]["imps"] += st["imps"]
            camp_touch_totals[cid_key]["clicks"] += st["clicks"]
        for camp in active_camps:
            cid = camp["campaign_id"]
            total_conv = camp_conversions.get(cid, 0)
            ct = camp_touch_totals.get(cid, {"imps": 500, "clicks": 50})
            allocated_conv = 0
            for idx, ch_id in enumerate(channel_ids):
                # 展示量: 基于touch量放大(广告投放覆盖更广)
                base_imps = max(100, ct["imps"] * random.randint(3, 8) // n_channels)
                imps = base_imps + random.randint(0, base_imps // 2)
                clicks = int(imps * random.uniform(0.01, 0.08))
                cost = round(clicks * random.uniform(0.5, 5.0), 2)
                cpc = round(cost / max(clicks, 1), 2)
                cpm = round(cost / max(imps, 1) * 1000, 2)
                # conversions: 补差法, 确保sum == total_conv
                if idx < len(channel_ids) - 1:
                    conversions = max(0, total_conv // n_channels)
                    allocated_conv += conversions
                else:
                    conversions = max(0, total_conv - allocated_conv)
                cpa = round(cost / max(conversions, 1), 2)
                self.ad_id += 1
                self.w_ad.write_row([
                    self.ad_id, camp["campaign_id"], ch_id,
                    fmt_date(datetime(day.year, day.month, day.day)),
                    imps, clicks, cost,
                    cpc, cpm, cpa, conversions,
                ])

    def _gen_attribution(self, day_orders: list) -> dict:
        """对已支付订单按4种归因模型分配credit, 使用近7天触达历史
        返回 {campaign_id: 转化订单数}"""
        camp_conversions: dict[int, int] = {}
        all_touches = [t for t, _ in self._touch_history]
        if not all_touches:
            return camp_conversions
        # 索引: user_id -> [touch]
        user_touches = {}
        for t in all_touches:
            uid = t["user_id"]
            user_touches.setdefault(uid, []).append(t)

        for o in day_orders:
            if o["current_status"] in ("cancelled", "created"):
                continue
            uid = o["user_id"]
            touches = user_touches.get(uid, [])
            if not touches:
                continue
            order_time = o["create_time"]
            # 确保触达发生在下单之前 (因果关系)
            touches = [t for t in touches if t["touch_time"] < order_time]
            if not touches:
                continue
            # 统计每个campaign的转化订单数(last_click归因)
            last_camp = touches[-1]["campaign_id"]
            camp_conversions[last_camp] = camp_conversions.get(last_camp, 0) + 1
            # 按每种模型写一组
            for model in config.ATTRIBUTION_MODELS:
                n = len(touches)
                if model == "last_click":
                    credits = [0.0] * n
                    credits[-1] = 1.0
                elif model == "first_click":
                    credits = [0.0] * n
                    credits[0] = 1.0
                elif model == "linear":
                    unit = round(1.0 / n, 4)
                    credits = [unit] * n
                    credits[-1] = round(1.0 - unit * (n - 1), 4)
                else:  # time_decay
                    raw = [2 ** (-(n - 1 - i)) for i in range(n)]
                    total = sum(raw)
                    credits = [round(r / total, 4) for r in raw]
                for idx, t in enumerate(touches):
                    self.attribution_id += 1
                    self.w_attr.write_row([
                        self.attribution_id, o["order_id"],
                        t["campaign_id"], t["touch_id"],
                        model, credits[idx],
                        fmt_datetime(t["touch_time"]),
                        fmt_datetime(order_time),
                    ])
        return camp_conversions
