#!/bin/bash
# 加载物流模块（4张表）
source "$(dirname "$0")/common.sh"

echo "--- 物流模块 ---"
load_csv "shipment_info" "shipment_info.csv" \
    "shipment_id,order_id,warehouse_id,carrier_id,logistics_type,ship_time,pickup_time,estimated_arrival,actual_arrival,promised_delivery_time,waybill_no,signed_flag,signed_time,last_mile_type,delivery_cost,cod_flag,re_dispatch_count"
load_csv "shipment_track" "shipment_track.csv" \
    "track_id,shipment_id,node_seq,node_name,node_time,city"
load_csv "delivery_exception" "delivery_exception.csv" \
    "exception_id,shipment_id,order_id,exception_type,exception_time,description"
load_csv "shipment_sign_log" "shipment_sign_log.csv" \
    "sign_id,shipment_id,order_id,signed_time"
