-- 商品模块: SPU / SKU / 平台属性 / 销售属性
-- 注意：sku_info的CSV含dw_start_date/dw_end_date，业务库不需要
USE ecommerce;

CREATE TABLE IF NOT EXISTS spu_info (
    spu_id       BIGINT       NOT NULL PRIMARY KEY,
    spu_name     VARCHAR(200),
    category3_id BIGINT       NOT NULL,
    tm_id        BIGINT       NOT NULL,
    create_time  DATETIME     NOT NULL,
    operate_time DATETIME
) ENGINE=InnoDB COMMENT='SPU信息表';

CREATE TABLE IF NOT EXISTS sku_info (
    sku_id         BIGINT        NOT NULL PRIMARY KEY,
    sku_name       VARCHAR(200),
    spu_id         BIGINT        NOT NULL,
    category3_id   BIGINT        NOT NULL,
    tm_id          BIGINT        NOT NULL,
    original_price DECIMAL(16,2) NOT NULL,
    cost_price     DECIMAL(16,2) NOT NULL,
    weight         VARCHAR(20),
    volume         VARCHAR(20),
    merchant_id    BIGINT        NOT NULL,
    is_hot         TINYINT,
    price_band     VARCHAR(20),
    create_time    DATETIME      NOT NULL,
    operate_time   DATETIME,
    INDEX idx_spu_id (spu_id),
    INDEX idx_category3_id (category3_id),
    INDEX idx_merchant_id (merchant_id)
) ENGINE=InnoDB COMMENT='SKU商品信息表';

CREATE TABLE IF NOT EXISTS sku_attr_value (
    id         BIGINT       NOT NULL PRIMARY KEY,
    sku_id     BIGINT       NOT NULL,
    attr_name  VARCHAR(100),
    attr_value VARCHAR(200),
    INDEX idx_sku_id (sku_id)
) ENGINE=InnoDB COMMENT='SKU平台属性值表';

CREATE TABLE IF NOT EXISTS sku_sale_attr_value (
    id              BIGINT       NOT NULL PRIMARY KEY,
    sku_id          BIGINT       NOT NULL,
    sale_attr_name  VARCHAR(100),
    sale_attr_value VARCHAR(200),
    INDEX idx_sku_id (sku_id)
) ENGINE=InnoDB COMMENT='SKU销售属性值表';
