#!/bin/bash
# 加载营销模块（4张表）
source "$(dirname "$0")/common.sh"

echo "--- 营销模块 ---"
load_csv "campaign_info" "campaign_info.csv" \
    "campaign_id,campaign_name,campaign_type,start_date,end_date,gmv_boost"
load_csv "marketing_channel" "marketing_channel.csv" \
    "channel_id,channel_name,channel_type,source,medium"
load_csv "marketing_touch" "marketing_touch.csv" \
    "touch_id,campaign_id,user_id,touch_channel,touch_time,is_click,touch_type,creative_id,crowd_package_id"
load_csv "ad_spend" "ad_spend.csv" \
    "id,campaign_id,channel_id,spend_date,impressions,clicks,cost,cpc,cpm,cpa,conversions"
