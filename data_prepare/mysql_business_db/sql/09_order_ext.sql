-- 购物车 / 收藏 / 评价 / 售后 / 退款
USE ecommerce;

CREATE TABLE IF NOT EXISTS cart_info (
    cart_id      BIGINT   NOT NULL PRIMARY KEY,
    user_id      BIGINT   NOT NULL,
    sku_id       BIGINT   NOT NULL,
    sku_num      INT      NOT NULL,
    is_ordered   TINYINT,
    create_time  DATETIME NOT NULL,
    operate_time DATETIME,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB COMMENT='购物车表';

CREATE TABLE IF NOT EXISTS favor_info (
    favor_id    BIGINT   NOT NULL PRIMARY KEY,
    user_id     BIGINT   NOT NULL,
    sku_id      BIGINT   NOT NULL,
    create_time DATETIME NOT NULL,
    cancel_time DATETIME,
    is_cancel   TINYINT,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB COMMENT='商品收藏表';

CREATE TABLE IF NOT EXISTS comment_info (
    comment_id   BIGINT       NOT NULL PRIMARY KEY,
    order_id     BIGINT       NOT NULL,
    user_id      BIGINT       NOT NULL,
    sku_id       BIGINT       NOT NULL,
    appraise     VARCHAR(20),
    content      VARCHAR(500),
    create_time  DATETIME     NOT NULL,
    operate_time DATETIME,
    INDEX idx_order_id (order_id)
) ENGINE=InnoDB COMMENT='商品评价表';

CREATE TABLE IF NOT EXISTS after_sales (
    after_sales_id BIGINT      NOT NULL PRIMARY KEY,
    order_id       BIGINT      NOT NULL,
    user_id        BIGINT      NOT NULL,
    sku_id         BIGINT      NOT NULL,
    type           VARCHAR(50) NOT NULL,
    status         VARCHAR(20) NOT NULL,
    reason         VARCHAR(200),
    apply_time     DATETIME,
    complete_time  DATETIME,
    INDEX idx_order_id (order_id)
) ENGINE=InnoDB COMMENT='售后服务表';

CREATE TABLE IF NOT EXISTS order_refund_info (
    refund_id     BIGINT        NOT NULL PRIMARY KEY,
    order_id      BIGINT        NOT NULL,
    user_id       BIGINT        NOT NULL,
    sku_id        BIGINT        NOT NULL,
    refund_amount DECIMAL(16,2) NOT NULL,
    refund_status VARCHAR(20)   NOT NULL,
    reason        VARCHAR(200),
    apply_time    DATETIME,
    audit_time    DATETIME,
    complete_time DATETIME,
    INDEX idx_order_id (order_id)
) ENGINE=InnoDB COMMENT='退款信息表';
