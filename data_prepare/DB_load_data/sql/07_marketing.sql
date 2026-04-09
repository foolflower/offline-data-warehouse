-- 营销模块：Campaign / 渠道 / 触达 / 广告花费
USE ecommerce;

CREATE TABLE IF NOT EXISTS campaign_info (
    campaign_id   BIGINT       NOT NULL PRIMARY KEY,
    campaign_name VARCHAR(100),
    campaign_type VARCHAR(50)  NOT NULL,
    start_date    DATE         NOT NULL,
    end_date      DATE         NOT NULL,
    gmv_boost     VARCHAR(20)
) ENGINE=InnoDB COMMENT='营销Campaign表';

CREATE TABLE IF NOT EXISTS marketing_channel (
    channel_id   BIGINT       NOT NULL PRIMARY KEY,
    channel_name VARCHAR(100),
    channel_type VARCHAR(50)  NOT NULL,
    source       VARCHAR(50),
    medium       VARCHAR(50)
) ENGINE=InnoDB COMMENT='营销渠道表';

CREATE TABLE IF NOT EXISTS marketing_touch (
    touch_id         BIGINT      NOT NULL PRIMARY KEY,
    campaign_id      BIGINT      NOT NULL,
    user_id          BIGINT      NOT NULL,
    touch_channel    VARCHAR(50),
    touch_time       DATETIME,
    is_click         TINYINT,
    touch_type       VARCHAR(50) NOT NULL,
    creative_id      BIGINT      NOT NULL,
    crowd_package_id BIGINT      NOT NULL,
    INDEX idx_campaign_id (campaign_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB COMMENT='营销触达记录表';

CREATE TABLE IF NOT EXISTS ad_spend (
    id          BIGINT      NOT NULL PRIMARY KEY,
    campaign_id BIGINT      NOT NULL,
    channel_id  BIGINT      NOT NULL,
    spend_date  DATE        NOT NULL,
    impressions VARCHAR(20),
    clicks      VARCHAR(20),
    cost        VARCHAR(20),
    cpc         VARCHAR(20),
    cpm         VARCHAR(20),
    cpa         VARCHAR(20),
    conversions VARCHAR(20),
    INDEX idx_campaign_id (campaign_id),
    INDEX idx_spend_date (spend_date)
) ENGINE=InnoDB COMMENT='广告投放花费表';
