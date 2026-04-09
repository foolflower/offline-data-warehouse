-- 品类与品牌
USE ecommerce;

CREATE TABLE IF NOT EXISTS base_category1 (
    id   BIGINT       NOT NULL PRIMARY KEY,
    name VARCHAR(100)
) ENGINE=InnoDB COMMENT='一级品类';

CREATE TABLE IF NOT EXISTS base_category2 (
    id           BIGINT       NOT NULL PRIMARY KEY,
    name         VARCHAR(100),
    category1_id BIGINT       NOT NULL
) ENGINE=InnoDB COMMENT='二级品类';

CREATE TABLE IF NOT EXISTS base_category3 (
    id           BIGINT       NOT NULL PRIMARY KEY,
    name         VARCHAR(100),
    category2_id BIGINT       NOT NULL
) ENGINE=InnoDB COMMENT='三级品类';

CREATE TABLE IF NOT EXISTS base_trademark (
    tm_id          BIGINT       NOT NULL PRIMARY KEY,
    tm_name        VARCHAR(100),
    logo_url       VARCHAR(500),
    country        VARCHAR(50),
    is_owned_brand TINYINT,
    brand_category VARCHAR(50)
) ENGINE=InnoDB COMMENT='品牌商标表';
