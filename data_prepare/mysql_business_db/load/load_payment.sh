#!/bin/bash
# 加载支付模块（3张表）
source "$(dirname "$0")/common.sh"

echo "--- 支付模块 ---"
load_csv "payment_info" "payment_info.csv" \
    "payment_id,order_id,user_id,payment_type,payment_amount,payment_status,create_time,pay_time,callback_time"
load_csv "payment_detail" "payment_detail.csv" \
    "id,payment_id,order_id,sku_id,amount,create_time"
load_csv "payment_invoice" "payment_invoice.csv" \
    "invoice_id,order_id,user_id,invoice_type,invoice_title,amount,create_time"
