-- 支付模块：支付信息 / 支付明细 / 发票
USE ecommerce;

CREATE TABLE IF NOT EXISTS payment_info (
    payment_id     BIGINT        NOT NULL PRIMARY KEY,
    order_id       BIGINT        NOT NULL,
    user_id        BIGINT        NOT NULL,
    payment_type   VARCHAR(30)   NOT NULL,
    payment_amount DECIMAL(16,2) NOT NULL,
    payment_status VARCHAR(20)   NOT NULL,
    create_time    DATETIME      NOT NULL,
    pay_time       DATETIME,
    callback_time  DATETIME,
    INDEX idx_order_id (order_id),
    INDEX idx_pay_time (pay_time)
) ENGINE=InnoDB COMMENT='支付信息表';

CREATE TABLE IF NOT EXISTS payment_detail (
    id          BIGINT       NOT NULL PRIMARY KEY,
    payment_id  BIGINT       NOT NULL,
    order_id    BIGINT       NOT NULL,
    sku_id      BIGINT       NOT NULL,
    amount      VARCHAR(50)  NOT NULL,
    create_time DATETIME     NOT NULL,
    INDEX idx_payment_id (payment_id)
) ENGINE=InnoDB COMMENT='支付明细表';

CREATE TABLE IF NOT EXISTS payment_invoice (
    invoice_id    BIGINT       NOT NULL PRIMARY KEY,
    order_id      BIGINT       NOT NULL,
    user_id       BIGINT       NOT NULL,
    invoice_type  VARCHAR(50)  NOT NULL,
    invoice_title VARCHAR(200),
    amount        VARCHAR(50)  NOT NULL,
    create_time   DATETIME     NOT NULL,
    INDEX idx_order_id (order_id)
) ENGINE=InnoDB COMMENT='支付发票表';
