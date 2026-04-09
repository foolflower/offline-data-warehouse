-- 物流模块：发货 / 轨迹 / 异常 / 签收
USE ecommerce;

CREATE TABLE IF NOT EXISTS shipment_info (
    shipment_id            BIGINT        NOT NULL PRIMARY KEY,
    order_id               BIGINT        NOT NULL,
    warehouse_id           BIGINT        NOT NULL,
    carrier_id             BIGINT        NOT NULL,
    logistics_type         VARCHAR(50)   NOT NULL,
    ship_time              DATETIME,
    pickup_time            DATETIME,
    estimated_arrival      VARCHAR(50),
    actual_arrival         VARCHAR(50),
    promised_delivery_time DATETIME,
    waybill_no             VARCHAR(50),
    signed_flag            TINYINT,
    signed_time            DATETIME,
    last_mile_type         VARCHAR(50)   NOT NULL,
    delivery_cost          DECIMAL(16,2),
    cod_flag               TINYINT,
    re_dispatch_count      INT           NOT NULL,
    INDEX idx_order_id (order_id)
) ENGINE=InnoDB COMMENT='发货信息表';

CREATE TABLE IF NOT EXISTS shipment_track (
    track_id    BIGINT       NOT NULL PRIMARY KEY,
    shipment_id BIGINT       NOT NULL,
    node_seq    VARCHAR(20),
    node_name   VARCHAR(100),
    node_time   DATETIME,
    city        VARCHAR(50),
    INDEX idx_shipment_id (shipment_id)
) ENGINE=InnoDB COMMENT='物流轨迹表';

CREATE TABLE IF NOT EXISTS delivery_exception (
    exception_id   BIGINT       NOT NULL PRIMARY KEY,
    shipment_id    BIGINT       NOT NULL,
    order_id       BIGINT       NOT NULL,
    exception_type VARCHAR(50)  NOT NULL,
    exception_time DATETIME,
    description    VARCHAR(500),
    INDEX idx_shipment_id (shipment_id)
) ENGINE=InnoDB COMMENT='配送异常表';

CREATE TABLE IF NOT EXISTS shipment_sign_log (
    sign_id     BIGINT   NOT NULL PRIMARY KEY,
    shipment_id BIGINT   NOT NULL,
    order_id    BIGINT   NOT NULL,
    signed_time DATETIME,
    INDEX idx_shipment_id (shipment_id)
) ENGINE=InnoDB COMMENT='签收日志表';
