#!/bin/bash
# 加载商家、供应商、仓库、承运商（4张表）
# 注意：dim_carrier.csv -> carrier_info表（DW命名->业务命名）
source "$(dirname "$0")/common.sh"

echo "--- 业务配置表 ---"
load_csv "merchant_info" "merchant_info.csv" \
    "merchant_id,merchant_name,merchant_type,industry,province,merchant_rating,open_date,create_time,operate_time"
load_csv "supplier_info" "supplier_info.csv" \
    "supplier_id,name,type,contact_phone,bank_account,create_time,operate_time"
load_csv "warehouse_info" "warehouse_info.csv" \
    "warehouse_id,name,type,province_id,city_id,share"

# dim_carrier.csv是数仓命名，在业务库中表名为carrier_info
load_csv "carrier_info" "dim_carrier.csv" \
    "carrier_id,carrier_name,share,speed_factor,exception_rate"
