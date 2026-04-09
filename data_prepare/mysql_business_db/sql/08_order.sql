-- 订单核心：订单主表 / 订单明细 / 订单状态流水
USE ecommerce;

CREATE TABLE IF NOT EXISTS order_info (
    order_id               BIGINT        NOT NULL PRIMARY KEY,
    user_id                BIGINT        NOT NULL,
    merchant_id            BIGINT        NOT NULL,
    province_id            BIGINT        NOT NULL,
    city_id                BIGINT        NOT NULL,
    order_status           VARCHAR(30)   NOT NULL,
    total_amount           DECIMAL(16,2) NOT NULL,
    original_total_amount  DECIMAL(16,2) NOT NULL,
    activity_reduce_amount DECIMAL(16,2) NOT NULL,
    coupon_reduce_amount   DECIMAL(16,2) NOT NULL,
    discount_reduce_amount DECIMAL(16,2) NOT NULL,
    freight_amount         DECIMAL(16,2) NOT NULL,
    payment_type           VARCHAR(30)   NOT NULL,
    source_type            VARCHAR(30)   NOT NULL,
    is_first_order         TINYINT,
    session_id             BIGINT        NOT NULL,
    trace_id               BIGINT        NOT NULL,
    create_time            DATETIME      NOT NULL,
    payment_time           DATETIME,
    send_time              DATETIME,
    receive_time           DATETIME,
    complete_time          DATETIME,
    operate_time           DATETIME,
    INDEX idx_user_id (user_id),
    INDEX idx_create_time (create_time),
    INDEX idx_operate_time (operate_time)
) ENGINE=InnoDB COMMENT='订单主表';

CREATE TABLE IF NOT EXISTS order_detail (
    detail_id        BIGINT        NOT NULL PRIMARY KEY,
    order_id         BIGINT        NOT NULL,
    sku_id           BIGINT        NOT NULL,
    sku_name         VARCHAR(200),
    order_price      DECIMAL(16,2) NOT NULL,
    sku_num          INT           NOT NULL,
    sku_total_amount DECIMAL(16,2) NOT NULL,
    merchant_id      BIGINT        NOT NULL,
    create_time      DATETIME      NOT NULL,
    operate_time     DATETIME,
    INDEX idx_order_id (order_id),
    INDEX idx_sku_id (sku_id)
) ENGINE=InnoDB COMMENT='订单明细表';

CREATE TABLE IF NOT EXISTS order_status_log (
    log_id       BIGINT      NOT NULL PRIMARY KEY,
    order_id     BIGINT      NOT NULL,
    order_status VARCHAR(30) NOT NULL,
    operate_time DATETIME,
    INDEX idx_order_id (order_id)
) ENGINE=InnoDB COMMENT='订单状态流水表';
