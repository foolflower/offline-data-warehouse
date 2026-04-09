"""
Phase5a: 维度变更注入(SCD) + 用户标签快照
对应 plan.md 特征#2 SCD/拉链, 特征#20 价格变更
user_tag_snapshot: 每7天(Day7/14/21/28)全量快照
"""
import random
from datetime import datetime, date

import config
from utils.csv_writer import CsvWriter
from utils.time_utils import fmt_datetime, fmt_date


class DailyChangeEngine:
    """SCD变更注入 + 价格变更日志 + 用户标签快照"""

    def __init__(self, out_dir: str, users: dict, skus: dict,
                 order_stats_fn=None):
        self.out_dir = out_dir
        self.users = users
        self.skus = skus
        self.price_change_id = 0
        self.snapshot_id = 0
        # 获取用户订单统计的回调 (返回 {uid: {order_count, total_amount, ...}})
        self._order_stats_fn = order_stats_fn

        # 选定需要SCD变更的用户 (Feature #2: 10%)
        all_uids = list(users.keys())
        n_scd = int(len(all_uids) * config.SCD_USER_LEVEL_RATE)
        self.scd_user_ids = random.sample(all_uids, n_scd)

        # 选定需要价格变更的SKU (Feature #2: 20%)
        all_sids = list(skus.keys())
        n_price = int(len(all_sids) * config.SCD_SKU_PRICE_RATE)
        self.scd_sku_ids = random.sample(all_sids, n_price)
        # 每个SKU分配变更到某一天 (均匀分布在30天)
        self.sku_change_day = {}
        for sid in self.scd_sku_ids:
            self.sku_change_day[sid] = random.randint(1, 30)

        # SCD变更日期追踪 (用于关闭旧记录的dw_end_date)
        self._user_change_dates = {}  # {uid: change_date_str}
        self._sku_change_dates = {}   # {sid: change_date_str}

    def open_writers(self):
        self.w_price = CsvWriter(self.out_dir, "sku_price_change.csv", [
            "change_id", "sku_id", "old_price", "new_price",
            "change_time",
        ])
        self.w_tag = CsvWriter(self.out_dir, "user_tag_snapshot.csv", [
            "snapshot_id", "user_id", "snapshot_date",
            "rfm_segment", "lifecycle_stage", "risk_level",
            "active_days_30d", "order_count_30d", "amount_30d",
        ])
        # SCD: 以 append 模式向已有 user_info / sku_info 追加变更行
        self.w_user_scd = CsvWriter(self.out_dir, "user_info.csv", [
            "user_id", "login_name", "nick_name", "name",
            "phone_num", "id_card", "email", "gender",
            "birthday", "user_level", "status",
            "province_id", "city_id",
            "create_time", "operate_time",
            "dw_start_date", "dw_end_date",
        ], append=True)
        self.w_sku_scd = CsvWriter(self.out_dir, "sku_info.csv", [
            "sku_id", "sku_name", "spu_id", "category3_id",
            "tm_id", "original_price", "cost_price",
            "weight", "volume", "merchant_id",
            "is_hot", "price_band",
            "create_time", "operate_time",
            "dw_start_date", "dw_end_date",
        ], append=True)

    def close_writers(self):
        self.w_price.close()
        self.w_tag.close()
        self.w_user_scd.close()
        self.w_sku_scd.close()
        # 回写SCD旧记录的dw_end_date
        self._fix_scd_end_dates()

    def _fix_scd_end_dates(self):
        """后处理: 将user_info/sku_info中旧版本行的dw_end_date从9999-12-31改为变更前一天"""
        import csv
        import os
        from datetime import timedelta as _td
        if self._user_change_dates:
            self._rewrite_scd_csv(
                os.path.join(self.out_dir, "user_info.csv"),
                id_col=0, dw_end_col=16,
                change_map=self._user_change_dates)
        if self._sku_change_dates:
            self._rewrite_scd_csv(
                os.path.join(self.out_dir, "sku_info.csv"),
                id_col=0, dw_end_col=15,
                change_map=self._sku_change_dates)

    @staticmethod
    def _rewrite_scd_csv(filepath, id_col, dw_end_col, change_map):
        """读取CSV, 为变更的ID关闭旧版本dw_end_date, 原地重写"""
        import csv
        import os
        from datetime import datetime as _dt, timedelta as _td
        tmp_path = filepath + ".tmp"
        first_row_seen = {}  # {id_str: True} 标记每个ID首次遇到的行(即旧版本)
        with open(filepath, "r", encoding="utf-8") as fin, \
             open(tmp_path, "w", newline="", encoding="utf-8") as fout:
            reader = csv.reader(fin)
            writer = csv.writer(fout)
            header = next(reader)
            writer.writerow(header)
            for row in reader:
                row_id = row[id_col]
                # 匹配: ID在变更表中 且 dw_end_date=9999-12-31 且 首次遇到
                if row_id in change_map or (row_id.isdigit() and int(row_id) in change_map):
                    key = int(row_id) if row_id.isdigit() else row_id
                    if key not in first_row_seen and row[dw_end_col] == "9999-12-31":
                        # 旧版本行: 关闭dw_end_date为变更日期前一天
                        chg_str = change_map[key]
                        chg_date = _dt.strptime(chg_str, "%Y-%m-%d").date()
                        end_date = chg_date - _td(days=1)
                        row[dw_end_col] = end_date.strftime("%Y-%m-%d")
                        first_row_seen[key] = True
                writer.writerow(row)
        os.replace(tmp_path, filepath)

    def process_day(self, day: date, day_num: int):
        """
        day_num: 1~30
        1) 用户level变更 (分散到30天)
        2) SKU价格变更 + sku_price_change
        3) Day7/14/21/28 生成 user_tag_snapshot
        """
        # 1) 用户 SCD: 每天变更 n/30 个用户的 level
        self.changed_user_ids = []  # 本日变更的用户ID列表
        chunk_size = max(1, len(self.scd_user_ids) // 30)
        start_idx = (day_num - 1) * chunk_size
        end_idx = min(start_idx + chunk_size, len(self.scd_user_ids))
        now = datetime(day.year, day.month, day.day,
                       random.randint(8, 20), random.randint(0, 59))
        for i in range(start_idx, end_idx):
            uid = self.scd_user_ids[i]
            user = self.users[uid]
            old_level = user["user_level"]
            new_level = random.choice([l for l in [1, 2, 3, 4, 5]
                                       if l != old_level])
            user["user_level"] = new_level
            user["level_change_time"] = now  # 记录变更时间供下游对齐
            self.changed_user_ids.append(uid)
            self._user_change_dates[uid] = fmt_date(now)
            # operate_time 更新并追加变更行到 user_info.csv (拷贝完整原始行)
            operate_str = fmt_datetime(now)
            self.w_user_scd.write_row([
                uid, f"user{uid:06d}",
                user.get("nick_name", ""), user.get("name", ""),
                user.get("phone_num", ""), user.get("id_card", ""),
                user.get("email", ""), user.get("gender", ""),
                user.get("birthday", ""), new_level,
                user.get("status", "active"),
                user.get("province_id", ""), user.get("city_id", ""),
                user.get("create_time", ""), operate_str,
                fmt_date(now), "9999-12-31",
            ])

        # 2) SKU价格变更 (Feature #20)
        for sid, change_day in self.sku_change_day.items():
            if change_day == day_num:
                sku = self.skus[sid]
                old_price = sku["original_price"]
                factor = random.uniform(0.8, 1.3)
                new_price = round(old_price * factor, 2)
                sku["original_price"] = new_price
                self.price_change_id += 1
                self._sku_change_dates[sid] = fmt_date(now)
                self.w_price.write_row([
                    self.price_change_id, sid,
                    old_price, new_price,
                    fmt_datetime(now),
                ])
                # 追加变更行到 sku_info.csv (SCD, 拷贝完整原始行)
                self.w_sku_scd.write_row([
                    sid, sku.get("sku_name", f"SKU{sid:05d}"),
                    sku.get("spu_id", ""),
                    sku.get("cat3_id", ""), sku.get("tm_id", ""),
                    new_price, sku.get("cost_price", ""),
                    sku.get("weight", ""), sku.get("volume", ""),
                    sku.get("merchant_id", ""),
                    sku.get("is_hot", 0), sku.get("price_band", ""),
                    sku.get("create_time", ""), fmt_datetime(now),
                    fmt_date(now), "9999-12-31",
                ])

        # 3) 用户标签快照 (Day7/14/21/28)
        if day_num in (7, 14, 21, 28):
            self._gen_tag_snapshot(day)

    def _gen_tag_snapshot(self, day: date):
        """全量用户快照, 基于实际订单统计计算 RFM/生命周期/风险"""
        day_str = fmt_date(datetime(day.year, day.month, day.day))
        stats = self._order_stats_fn() if self._order_stats_fn else {}

        for uid in self.users:
            self.snapshot_id += 1
            s = stats.get(uid)
            if s:
                order_c = s["order_count"]
                amount = round(s["total_amount"], 2)
                active_d = len(s.get("active_days", set()))
                last_day = s.get("last_order_day")
                recency = (day - last_day).days if last_day else 999
            else:
                order_c = 0
                amount = 0.0
                active_d = 0
                recency = 999

            # RFM分群: 基于 recency + frequency + monetary 三维度
            if order_c == 0:
                rfm = "lost" if recency > 14 else "new"
            elif recency <= 7 and order_c >= 5 and amount >= 2000:
                rfm = "high"
            elif recency <= 14 and order_c >= 2 and amount >= 500:
                rfm = "mid"
            elif recency > 21 and order_c > 0:
                rfm = "lost"
            else:
                rfm = "low"

            # 生命周期: 基于活跃天数和下单量
            if order_c == 0:
                lc = "new" if recency <= 14 else "churned"
            elif active_d >= 10 and order_c >= 3:
                lc = "mature"
            elif order_c >= 2:
                lc = "growing"
            else:
                lc = "declining" if recency > 7 else "growing"

            # 风险: 退款率高/近期无活动=高风险
            risk = "low"
            if recency > 14 and order_c > 0:
                risk = "high"
            elif recency > 7:
                risk = "medium"

            self.w_tag.write_row([
                self.snapshot_id, uid, day_str,
                rfm, lc, risk,
                active_d, order_c, amount,
            ])
