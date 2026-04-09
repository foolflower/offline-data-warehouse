#!/bin/bash
# ============================================================
# 电商业务数据库 一键初始化脚本
#
# 功能：创建数据库 → 建表(45张业务表) → 装载CSV数据
# 使用：chmod +x init_all.sh && ./init_all.sh
#
# 说明：本脚本还原的是电商公司的MySQL业务数据库，不是数仓。
#       以下类型的数据不包含在业务库中：
#       - 数仓维度表：dim_date, dim_device（由数仓团队构建）
#       - 数仓派生表：session_info, user_tag_snapshot,
#                     campaign_attribution（由ETL计算生成）
#       - 应用日志：*.jsonl 文件（由Flume采集到HDFS，不经过MySQL）
#       - 数仓字段：dw_start_date/dw_end_date（拉链表字段）
#
# 前置要求：
#   MySQL需开启 local_infile（my.cnf中 local_infile=1）
# ============================================================

set -e

# =============================================================
# ======= 请根据实际环境修改以下配置 ========
# =============================================================
export MYSQL_HOST="localhost"
export MYSQL_PORT="3306"
export MYSQL_USER="root"
export MYSQL_PASS="your_password"
export MYSQL_DB="ecommerce"
export CSV_DIR="/path/to/RawData"
# =============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SQL_DIR="${SCRIPT_DIR}/sql"
LOAD_DIR="${SCRIPT_DIR}/load"

export MYSQL_CMD="mysql --local-infile -h${MYSQL_HOST} -P${MYSQL_PORT} -u${MYSQL_USER} -p${MYSQL_PASS} ${MYSQL_DB}"
MYSQL_ADMIN="mysql -h${MYSQL_HOST} -P${MYSQL_PORT} -u${MYSQL_USER} -p${MYSQL_PASS}"

echo "============================================"
echo " 电商业务数据库初始化（非数仓）"
echo " 主机: ${MYSQL_HOST}:${MYSQL_PORT}"
echo " 数据库: ${MYSQL_DB}"
echo " CSV目录: ${CSV_DIR}"
echo "============================================"

# ---------- 检查环境 ----------
echo ""
echo "[步骤 1/4] 检查环境..."

if ! command -v mysql &> /dev/null; then
    echo "[ERROR] mysql 命令未找到"
    exit 1
fi

if [ ! -d "${CSV_DIR}" ]; then
    echo "[ERROR] CSV目录不存在: ${CSV_DIR}"
    exit 1
fi

echo "[OK] 环境检查通过"

# ---------- 创建数据库 ----------
echo ""
echo "[步骤 2/4] 创建数据库..."
${MYSQL_ADMIN} < "${SQL_DIR}/00_create_database.sql"
echo "[OK] 数据库 ${MYSQL_DB} 已就绪"

# ---------- 建表 ----------
echo ""
echo "[步骤 3/4] 创建业务表..."

for sql_file in \
    01_geography.sql \
    02_category_brand.sql \
    03_business_config.sql \
    04_user.sql \
    05_product.sql \
    06_activity_coupon.sql \
    07_marketing.sql \
    08_order.sql \
    09_order_ext.sql \
    10_payment.sql \
    11_shipment.sql \
    12_inventory.sql
do
    echo "  执行 ${sql_file} ..."
    ${MYSQL_ADMIN} < "${SQL_DIR}/${sql_file}"
done

TABLE_COUNT=$(${MYSQL_CMD} -N --execute="SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='${MYSQL_DB}';")
echo "[OK] 建表完成，共 ${TABLE_COUNT} 张业务表"

# ---------- 装载数据 ----------
echo ""
echo "[步骤 4/4] 装载CSV数据..."

for loader in \
    load_base.sh \
    load_business.sh \
    load_user.sh \
    load_product.sh \
    load_activity.sh \
    load_marketing.sh \
    load_order.sh \
    load_payment.sh \
    load_shipment.sh \
    load_inventory.sh
do
    echo ""
    bash "${LOAD_DIR}/${loader}"
done

# ---------- 完成汇总 ----------
echo ""
echo "============================================"
echo " 初始化完成！各表数据量："
echo "============================================"

${MYSQL_CMD} -N --execute="
    SELECT table_name, table_rows
    FROM information_schema.tables
    WHERE table_schema='${MYSQL_DB}'
    ORDER BY table_name;
" | while IFS=$'\t' read -r tname trows; do
    printf "  %-30s %s 行\n" "${tname}" "${trows}"
done

echo ""
echo "业务数据库还原完成！"
echo ""
echo "以下数据不在业务库中（需要在数仓侧处理）："
echo "  [DW维度] dim_date, dim_device"
echo "  [DW派生] session_info, user_tag_snapshot, campaign_attribution"
echo "  [应用日志] *.jsonl（7个日志文件由Flume采集）"
