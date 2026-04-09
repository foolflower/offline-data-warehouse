#!/bin/bash
# 加载商品表（4张表）
# sku_info.csv含dw_start_date/dw_end_date，用@dummy跳过
source "$(dirname "$0")/common.sh"

echo "--- 商品模块 ---"
load_csv "spu_info" "spu_info.csv" \
    "spu_id,spu_name,category3_id,tm_id,create_time,operate_time"
load_csv "sku_info" "sku_info.csv" \
    "sku_id,sku_name,spu_id,category3_id,tm_id,original_price,cost_price,weight,volume,merchant_id,is_hot,price_band,create_time,operate_time,@dummy1,@dummy2"
load_csv "sku_attr_value" "sku_attr_value.csv" \
    "id,sku_id,attr_name,attr_value"
load_csv "sku_sale_attr_value" "sku_sale_attr_value.csv" \
    "id,sku_id,sale_attr_name,sale_attr_value"
