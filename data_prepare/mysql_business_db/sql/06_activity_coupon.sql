-- 活动与优惠券模块
USE ecommerce;

CREATE TABLE IF NOT EXISTS activity_info (
    activity_id   BIGINT       NOT NULL PRIMARY KEY,
    activity_name VARCHAR(100),
    activity_type VARCHAR(50)  NOT NULL,
    start_date    DATE         NOT NULL,
    end_date      DATE         NOT NULL,
    create_time   DATETIME     NOT NULL,
    operate_time  DATETIME
) ENGINE=InnoDB COMMENT='活动信息表';

CREATE TABLE IF NOT EXISTS activity_rule (
    rule_id          BIGINT        NOT NULL PRIMARY KEY,
    activity_id      BIGINT        NOT NULL,
    rule_type        VARCHAR(50)   NOT NULL,
    condition_amount DECIMAL(16,2) NOT NULL,
    benefit_amount   DECIMAL(16,2) NOT NULL,
    benefit_discount DECIMAL(16,2) NOT NULL,
    benefit_level    INT,
    INDEX idx_activity_id (activity_id)
) ENGINE=InnoDB COMMENT='活动规则表';

CREATE TABLE IF NOT EXISTS activity_sku (
    id          BIGINT   NOT NULL PRIMARY KEY,
    activity_id BIGINT   NOT NULL,
    sku_id      BIGINT   NOT NULL,
    create_time DATETIME NOT NULL,
    INDEX idx_activity_id (activity_id),
    INDEX idx_sku_id (sku_id)
) ENGINE=InnoDB COMMENT='活动SKU关联表';

CREATE TABLE IF NOT EXISTS coupon_info (
    coupon_id        BIGINT        NOT NULL PRIMARY KEY,
    coupon_name      VARCHAR(100),
    coupon_type      VARCHAR(50)   NOT NULL,
    condition_amount DECIMAL(16,2) NOT NULL,
    benefit_amount   DECIMAL(16,2) NOT NULL,
    benefit_discount DECIMAL(16,2) NOT NULL,
    start_date       DATE          NOT NULL,
    end_date         DATE          NOT NULL,
    create_time      DATETIME      NOT NULL,
    operate_time     DATETIME
) ENGINE=InnoDB COMMENT='优惠券信息表';

CREATE TABLE IF NOT EXISTS coupon_receive (
    record_id    BIGINT       NOT NULL PRIMARY KEY,
    coupon_id    BIGINT       NOT NULL,
    user_id      BIGINT       NOT NULL,
    receive_time DATETIME,
    expire_date  DATE,
    status       VARCHAR(20)  NOT NULL,
    INDEX idx_coupon_id (coupon_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB COMMENT='优惠券领取记录表';

CREATE TABLE IF NOT EXISTS coupon_use (
    use_id            BIGINT        NOT NULL PRIMARY KEY,
    coupon_id         BIGINT        NOT NULL,
    user_id           BIGINT        NOT NULL,
    order_id          BIGINT        NOT NULL,
    use_time          DATETIME,
    discount_amount   DECIMAL(16,2) NOT NULL,
    receive_record_id BIGINT        NOT NULL,
    INDEX idx_order_id (order_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB COMMENT='优惠券使用记录表';
