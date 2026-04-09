-- 库存与价格管理
USE ecommerce;

CREATE TABLE IF NOT EXISTS sku_stock (
    id           BIGINT NOT NULL PRIMARY KEY,
    sku_id       BIGINT NOT NULL,
    warehouse_id BIGINT NOT NULL,
    stock_date   DATE,
    stock_qty    INT    NOT NULL,
    in_qty       INT    NOT NULL,
    out_qty      INT    NOT NULL,
    INDEX idx_sku_id (sku_id),
    INDEX idx_stock_date (stock_date)
) ENGINE=InnoDB COMMENT='SKU库存表';

CREATE TABLE IF NOT EXISTS sku_price_change (
    change_id   BIGINT        NOT NULL PRIMARY KEY,
    sku_id      BIGINT        NOT NULL,
    old_price   DECIMAL(16,2) NOT NULL,
    new_price   DECIMAL(16,2) NOT NULL,
    change_time DATETIME,
    INDEX idx_sku_id (sku_id)
) ENGINE=InnoDB COMMENT='SKU价格变更记录表';
