#!/bin/bash
# 加载活动与优惠券（6张表）
source "$(dirname "$0")/common.sh"

echo "--- 活动与优惠券 ---"
load_csv "activity_info" "activity_info.csv" \
    "activity_id,activity_name,activity_type,start_date,end_date,create_time,operate_time"
load_csv "activity_rule" "activity_rule.csv" \
    "rule_id,activity_id,rule_type,condition_amount,benefit_amount,benefit_discount,benefit_level"
load_csv "activity_sku" "activity_sku.csv" \
    "id,activity_id,sku_id,create_time"
load_csv "coupon_info" "coupon_info.csv" \
    "coupon_id,coupon_name,coupon_type,condition_amount,benefit_amount,benefit_discount,start_date,end_date,create_time,operate_time"
load_csv "coupon_receive" "coupon_receive.csv" \
    "record_id,coupon_id,user_id,receive_time,expire_date,status"
load_csv "coupon_use" "coupon_use.csv" \
    "use_id,coupon_id,user_id,order_id,use_time,discount_amount,receive_record_id"
