#!/bin/bash
# 加载地域、品类、品牌基础数据（12张表）
source "$(dirname "$0")/common.sh"

echo "--- 地域 ---"
load_csv "base_region" "base_region.csv" \
    "region_id,region_name"
load_csv "base_province" "base_province.csv" \
    "province_id,province_name,region_id,area_code,iso_code"
load_csv "base_city" "base_city.csv" \
    "city_id,city_name,province_id"
load_csv "base_district" "base_district.csv" \
    "district_id,district_name,city_id,province_id"

echo "--- 品类与品牌 ---"
load_csv "base_category1" "base_category1.csv" \
    "id,name"
load_csv "base_category2" "base_category2.csv" \
    "id,name,category1_id"
load_csv "base_category3" "base_category3.csv" \
    "id,name,category2_id"
load_csv "base_trademark" "base_trademark.csv" \
    "tm_id,tm_name,logo_url,country,is_owned_brand,brand_category"
