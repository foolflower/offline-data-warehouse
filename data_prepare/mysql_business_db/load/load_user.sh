#!/bin/bash
# 加载用户表（2张表）
# user_info.csv含dw_start_date/dw_end_date，用@dummy跳过
source "$(dirname "$0")/common.sh"

echo "--- 用户模块 ---"
load_csv "user_info" "user_info.csv" \
    "user_id,login_name,nick_name,name,phone_num,id_card,email,gender,birthday,user_level,status,province_id,city_id,create_time,operate_time,@dummy1,@dummy2"
load_csv "user_address" "user_address.csv" \
    "address_id,user_id,province_id,city_id,district_id,detail_address,consignee,consignee_phone,is_default,create_time,operate_time"
