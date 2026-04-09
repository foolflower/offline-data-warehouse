#!/bin/bash
# 公共函数：CSV数据加载到MySQL
# 被其他load_*.sh脚本source引用

load_csv() {
    local table="$1"
    local csv_file="$2"
    local columns="$3"
    local filepath="${CSV_DIR}/${csv_file}"

    if [ ! -f "${filepath}" ]; then
        echo "[WARN] 文件不存在，跳过: ${filepath}"
        return 1
    fi

    echo "[INFO] 正在加载 ${table} <- ${csv_file} ..."
    ${MYSQL_CMD} --execute="
        LOAD DATA LOCAL INFILE '${filepath}'
        INTO TABLE ${table}
        CHARACTER SET utf8mb4
        FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"'
        LINES TERMINATED BY '\n'
        IGNORE 1 LINES
        (${columns});
    "

    if [ $? -eq 0 ]; then
        local cnt=$(${MYSQL_CMD} -N --execute="SELECT COUNT(*) FROM ${table};")
        echo "[OK]   ${table} -> ${cnt} 条记录"
    else
        echo "[FAIL] ${table} 加载失败！"
        return 1
    fi
}
