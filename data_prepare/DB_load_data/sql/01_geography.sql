-- 地域模块：大区 / 省份 / 城市 / 区县
USE ecommerce;

CREATE TABLE IF NOT EXISTS base_region (
    region_id   BIGINT       NOT NULL PRIMARY KEY,
    region_name VARCHAR(50)
) ENGINE=InnoDB COMMENT='大区表';

CREATE TABLE IF NOT EXISTS base_province (
    province_id   BIGINT       NOT NULL PRIMARY KEY,
    province_name VARCHAR(50),
    region_id     BIGINT       NOT NULL,
    area_code     VARCHAR(20),
    iso_code      VARCHAR(20)
) ENGINE=InnoDB COMMENT='省份表';

CREATE TABLE IF NOT EXISTS base_city (
    city_id     BIGINT       NOT NULL PRIMARY KEY,
    city_name   VARCHAR(50),
    province_id BIGINT       NOT NULL
) ENGINE=InnoDB COMMENT='城市表';

CREATE TABLE IF NOT EXISTS base_district (
    district_id   BIGINT       NOT NULL PRIMARY KEY,
    district_name VARCHAR(50),
    city_id       BIGINT       NOT NULL,
    province_id   BIGINT       NOT NULL
) ENGINE=InnoDB COMMENT='区县表';
