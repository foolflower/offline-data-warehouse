-- 商家 / 供应商 / 仓库 / 承运商（业务配置表）
USE ecommerce;

CREATE TABLE IF NOT EXISTS merchant_info (
    merchant_id     BIGINT       NOT NULL PRIMARY KEY,
    merchant_name   VARCHAR(100),
    merchant_type   VARCHAR(50)  NOT NULL,
    industry        VARCHAR(50),
    province        VARCHAR(50),
    merchant_rating VARCHAR(20),
    open_date       DATE,
    create_time     DATETIME     NOT NULL,
    operate_time    DATETIME
) ENGINE=InnoDB COMMENT='商家信息表';

CREATE TABLE IF NOT EXISTS supplier_info (
    supplier_id   BIGINT       NOT NULL PRIMARY KEY,
    name          VARCHAR(100),
    type          VARCHAR(50)  NOT NULL,
    contact_phone VARCHAR(20),
    bank_account  VARCHAR(50)  NOT NULL,
    create_time   DATETIME     NOT NULL,
    operate_time  DATETIME
) ENGINE=InnoDB COMMENT='供应商信息表';

CREATE TABLE IF NOT EXISTS warehouse_info (
    warehouse_id BIGINT       NOT NULL PRIMARY KEY,
    name         VARCHAR(100),
    type         VARCHAR(50)  NOT NULL,
    province_id  BIGINT       NOT NULL,
    city_id      BIGINT       NOT NULL,
    share        VARCHAR(20)
) ENGINE=InnoDB COMMENT='仓库信息表';

CREATE TABLE IF NOT EXISTS carrier_info (
    carrier_id     BIGINT         NOT NULL PRIMARY KEY,
    carrier_name   VARCHAR(100),
    share          VARCHAR(20),
    speed_factor   VARCHAR(20),
    exception_rate DECIMAL(16,2)
) ENGINE=InnoDB COMMENT='承运商信息表';
