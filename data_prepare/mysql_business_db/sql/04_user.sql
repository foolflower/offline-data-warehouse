-- 用户模块：用户信息 / 收货地址
-- 注意：CSV中有dw_start_date/dw_end_date是数仓拉链字段，业务库不需要
USE ecommerce;

CREATE TABLE IF NOT EXISTS user_info (
    user_id      BIGINT       NOT NULL PRIMARY KEY,
    login_name   VARCHAR(50),
    nick_name    VARCHAR(100),
    name         VARCHAR(50),
    phone_num    VARCHAR(20),
    id_card      VARCHAR(20),
    email        VARCHAR(100),
    gender       VARCHAR(10),
    birthday     VARCHAR(20),
    user_level   INT,
    status       VARCHAR(20)  NOT NULL,
    province_id  BIGINT       NOT NULL,
    city_id      BIGINT       NOT NULL,
    create_time  DATETIME     NOT NULL,
    operate_time DATETIME,
    INDEX idx_create_time (create_time),
    INDEX idx_operate_time (operate_time)
) ENGINE=InnoDB COMMENT='用户信息表';

CREATE TABLE IF NOT EXISTS user_address (
    address_id      BIGINT       NOT NULL PRIMARY KEY,
    user_id         BIGINT       NOT NULL,
    province_id     BIGINT       NOT NULL,
    city_id         BIGINT       NOT NULL,
    district_id     BIGINT       NOT NULL,
    detail_address  VARCHAR(200),
    consignee       VARCHAR(50),
    consignee_phone VARCHAR(20),
    is_default      TINYINT,
    create_time     DATETIME     NOT NULL,
    operate_time    DATETIME,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB COMMENT='用户收货地址表';
