"""
全局配置 - 集中管理所有可调参数
对应 plan.md 一、核心参数 + 四、20项特殊数据特征注入策略
"""
import os
from datetime import date, datetime

# ── 随机种子(保证可重现) ──
RANDOM_SEED = 42

# ── 日期范围 ──
SIM_START = date(2026, 3, 1)        # 模拟主期间起始
SIM_END = date(2026, 3, 30)         # 模拟主期间结束 (30天)
SIM_DAYS = 30
USER_REG_START = date(2025, 10, 1)  # 用户注册跨度起始 (180天)
USER_REG_END = date(2026, 3, 30)    # 用户注册跨度结束

# ── 核心数量 ──
TOTAL_USERS = 100_000
TOTAL_SKU = 5_000
TOTAL_SPU = 1_500
TOTAL_BRANDS = 100
TOTAL_MERCHANTS = 200
TOTAL_CARRIERS = 10
TOTAL_CAMPAIGNS = 30
CAT1_COUNT = 15
CAT2_COUNT = 60
CAT3_COUNT = 300

# ── 日级指标 ──
DAU_MIN = 30_000
DAU_MAX = 35_000
DAILY_ORDER_MIN = 1_500
DAILY_ORDER_MAX = 2_800

# ── Phase 1 维表数量 ──
REGION_COUNT = 7
PROVINCE_COUNT = 34
CITY_COUNT = 340
DISTRICT_COUNT = 3_000
SUPPLIER_COUNT = 50
WAREHOUSE_COUNT = 8
CHANNEL_COUNT = 15
DIM_DATE_DAYS = 365     # dim_date 行数
DIM_DEVICE_COUNT = 2_000

# ── Phase 2 ──
SKU_ATTR_PER_SKU = (3, 8)       # 每个SKU 3-8个属性 (特征#9)
SKU_SALE_ATTR_PER_SKU = (1, 5)

# ── Phase 3 ──
USER_ADDRESS_PER_USER = (1, 5)  # 每用户1-5个地址 (特征#9)

# ── Phase 4 ──
ACTIVITY_COUNT = 50
ACTIVITY_RULE_COUNT = 120
ACTIVITY_SKU_COUNT = 3_000
COUPON_COUNT = 80
COUPON_RECEIVE_COUNT = 500_000
COUPON_USE_COUNT = 200_000

# ── Phase 5 表行数预估 ──
ORDER_INFO_COUNT = 320_000
ORDER_DETAIL_COUNT = 800_000
ORDER_STATUS_LOG_COUNT = 1_300_000
PAYMENT_INFO_COUNT = 290_000
PAYMENT_DETAIL_COUNT = 750_000
PAYMENT_INVOICE_COUNT = 80_000
ORDER_REFUND_COUNT = 16_000
CART_COUNT = 600_000
FAVOR_COUNT = 250_000
COMMENT_COUNT = 180_000
SHIPMENT_COUNT = 280_000
SHIPMENT_TRACK_COUNT = 1_500_000
DELIVERY_EXCEPTION_COUNT = 5_000
SKU_STOCK_ROWS = 1_200_000     # 5000 SKU × 8 仓库 × 30 天
SKU_PRICE_CHANGE_COUNT = 12_000
AD_SPEND_COUNT = 900
MARKETING_TOUCH_COUNT = 600_000
CAMPAIGN_ATTRIBUTION_COUNT = 400_000
AFTER_SALES_COUNT = 8_000

# ── Phase 6 行为日志行数 ──
LOGIN_LOG_COUNT = 1_500_000
PAGE_VIEW_COUNT = 28_000_000
EXPOSE_LOG_COUNT = 16_000_000
ACTION_LOG_COUNT = 6_000_000
START_LOG_COUNT = 2_000_000
SEARCH_LOG_COUNT = 3_500_000
ERROR_LOG_COUNT = 150_000
SESSION_INFO_COUNT = 3_000_000
USER_TAG_SNAPSHOT_COUNT = 600_000

# ── 订单命运路径占比 (plan.md 三、事件驱动生成法) ──
ORDER_FATE_WEIGHTS = {
    'A': 0.82,  # 正常完成: 下单→支付→发货→收货→完成
    'B': 0.08,  # 取消: 下单→超时/主动取消
    'C': 0.05,  # 退款: 下单→支付→发货→收货→退款
    'D': 0.03,  # 支付后退款: 下单→支付→退款
    'E': 0.02,  # 超时未支付: 下单→超时
}

# ── 订单阶段时间间隔参数 ──
# 下单→支付: 指数分布, 中位数30分钟 (1分钟~72小时)
PAY_DELAY_LAMBDA = 1.0 / 30.0  # 指数分布参数 (分钟)
PAY_DELAY_MAX_HOURS = 72

# 支付→发货: 对数正态, 中位数12小时 (2小时~3天)
SHIP_DELAY_MU = 2.485         # ln(12)
SHIP_DELAY_SIGMA = 0.5
SHIP_DELAY_MIN_HOURS = 2
SHIP_DELAY_MAX_HOURS = 72

# 发货→收货: 正态, 均值3天 (1天~7天)
RECEIVE_DELAY_MEAN_DAYS = 3.0
RECEIVE_DELAY_STD_DAYS = 1.0
RECEIVE_DELAY_MIN_DAYS = 1
RECEIVE_DELAY_MAX_DAYS = 7

# 收货→完成: 0~15天 (自动确认)
COMPLETE_DELAY_MAX_DAYS = 15

# ── 20项特殊数据特征注入比例 ──
# #1 零点漂移
MIDNIGHT_DRIFT_RATE = 0.05       # 5%订单23:50-23:59创建

# #2 SCD/拉链
SCD_USER_LEVEL_RATE = 0.10       # 10%用户30天内level变更
SCD_SKU_PRICE_RATE = 0.20        # 20%SKU有price变更

# #4 空值缺失
NULL_BIRTHDAY_RATE = 0.30        # 30%用户birthday=null
NULL_COUPON_RATE = 0.40          # 40%订单coupon字段null
NULL_USER_ID_LOG_RATE = 0.15     # 15%行为日志user_id=null
NULL_UTM_RATE = 0.60             # utm字段60%null

# #5 重复数据
DUP_PAYMENT_RATE = 0.01          # 1%支付回调重复
DUP_PAGE_VIEW_RATE = 0.005       # 0.5%行为日志重复

# #6 热点倾斜
HOT_SKU_COUNT = 50               # Top50 SKU(1%)
HOT_SKU_ORDER_SHARE = 0.30       # 产生30%订单
HOT_CITY_COUNT = 3               # Top3城市
HOT_CITY_ORDER_SHARE = 0.40      # 占40%订单

# #8 迟到数据
LATE_PAYMENT_CALLBACK_RATE = 0.03   # 3%支付callback延迟1-24h
LATE_SHIPMENT_TRACK_RATE = 0.05     # 5%物流轨迹节点延迟上报

# #10 时间异常
TIME_ANOMALY_RATE = 0.005        # 0.5%时间逻辑问题

# #11 金额不一致
AMOUNT_ANOMALY_RATE = 0.001      # 0.1%异常(退款>订单金额)

# #12 匿名用户
ANONYMOUS_LOG_RATE = 0.15        # 15%行为日志user_id=null

# #16 完整行为链
FULL_TRACE_RATE = 0.10           # 10%订单有trace_id全链路 (plan.md)

# ── 行为日志参数 ──
START_PER_USER = (1, 3)          # 每用户1-3次启动
PAGE_VIEW_PER_USER = (5, 50)     # 5-50次浏览
EXPOSE_PER_PAGE = (3, 10)        # 每页3-10次曝光
SEARCH_PER_USER = (0, 5)         # 0-5次搜索
ERROR_RATE = 0.005               # 0.5%触发错误

# ── 物流参数 ──
LAST_MILE_WEIGHTS = {
    'delivery': 0.60,
    'locker': 0.20,
    'store': 0.15,
    'station': 0.05,
}
RE_DISPATCH_WEIGHTS = {0: 0.95, 1: 0.04, 2: 0.01}
PROMISED_DAYS = {
    'same_province': 2,
    'intra_region': 3,
    'inter_province': 5,
}
TRACK_NODES = ['揽收', '始发分拣', '转运中心', '目的分拣', '配送站', '派件中', '签收']

# ── 营销参数 ──
TOUCH_CHANNELS = ['push', 'sms', 'in_app']
TOUCH_CLICK_RATES = {'push': 0.25, 'sms': 0.10, 'in_app': 0.35}
CREATIVE_IDS = [f'CRE{i:03d}' for i in range(1, 21)]
CROWD_PACKAGES = [f'PKG{i:03d}' for i in range(1, 11)]
ATTRIBUTION_MODELS = ['last_click', 'first_click', 'linear', 'time_decay']

# ── CSV写入参数 ──
CSV_BATCH_SIZE = 100_000         # 每10万行flush
CSV_BEHAVIOR_BATCH = 500_000     # 行为日志每50万行flush

# ── 输出目录 ──
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
