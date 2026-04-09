#!/bin/bash
# 加载库存与价格变更（2张表）
source "$(dirname "$0")/common.sh"

echo "--- 库存与价格 ---"
load_csv "sku_stock" "sku_stock.csv" \
    "id,sku_id,warehouse_id,stock_date,stock_qty,in_qty,out_qty"
load_csv "sku_price_change" "sku_price_change.csv" \
    "change_id,sku_id,old_price,new_price,change_time"
