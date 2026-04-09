#!/bin/bash
# 加载订单模块（8张表）
source "$(dirname "$0")/common.sh"

echo "--- 订单核心 ---"
load_csv "order_info" "order_info.csv" \
    "order_id,user_id,merchant_id,province_id,city_id,order_status,total_amount,original_total_amount,activity_reduce_amount,coupon_reduce_amount,discount_reduce_amount,freight_amount,payment_type,source_type,is_first_order,session_id,trace_id,create_time,payment_time,send_time,receive_time,complete_time,operate_time"
load_csv "order_detail" "order_detail.csv" \
    "detail_id,order_id,sku_id,sku_name,order_price,sku_num,sku_total_amount,merchant_id,create_time,operate_time"
load_csv "order_status_log" "order_status_log.csv" \
    "log_id,order_id,order_status,operate_time"

echo "--- 购物车/收藏/评价/售后 ---"
load_csv "cart_info" "cart_info.csv" \
    "cart_id,user_id,sku_id,sku_num,is_ordered,create_time,operate_time"
load_csv "favor_info" "favor_info.csv" \
    "favor_id,user_id,sku_id,create_time,cancel_time,is_cancel"
load_csv "comment_info" "comment_info.csv" \
    "comment_id,order_id,user_id,sku_id,appraise,content,create_time,operate_time"
load_csv "after_sales" "after_sales.csv" \
    "after_sales_id,order_id,user_id,sku_id,type,status,reason,apply_time,complete_time"
load_csv "order_refund_info" "order_refund_info.csv" \
    "refund_id,order_id,user_id,sku_id,refund_amount,refund_status,reason,apply_time,audit_time,complete_time"
