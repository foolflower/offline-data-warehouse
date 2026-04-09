"""
CSV分批写入(控制内存, 每10万行flush)
对应 plan.md 十、进一步考量 #1 内存控制
P2优化: 攒buffer批量writerows减少Python/C边界调用
"""
import csv
import os
from config import OUTPUT_DIR, CSV_BATCH_SIZE

# 内存buffer行数上限 (攒满后一次性writerows)
_WRITE_BUFFER_SIZE = 2000


class CsvWriter:
    """流式CSV写入器，按行写入并定期flush，避免一次性写入大量内容"""

    def __init__(self, out_dir: str, filename: str, fieldnames: list,
                 batch_size: int = CSV_BATCH_SIZE, append: bool = False):
        self.table_name = filename.replace('.csv', '')
        self.fieldnames = fieldnames
        # batch_size 仅用于控制 flush 频率
        self.batch_size = batch_size
        self.filepath = os.path.join(out_dir, filename)
        self._total_rows = 0
        self._file = None
        self._writer = None
        self._append = append
        self._buffer = []
        self._buf_size = _WRITE_BUFFER_SIZE
        self.open()

    def open(self):
        mode = 'a' if self._append else 'w'
        self._file = open(self.filepath, mode, newline='', encoding='utf-8')
        self._writer = csv.writer(self._file)
        if not self._append:
            self._writer.writerow(self.fieldnames)
        return self

    def write_row(self, row: list):
        if not self._writer:
            return
        self._buffer.append(row)
        self._total_rows += 1
        # 攒满buffer后批量写入, 减少Python→C调用次数
        if len(self._buffer) >= self._buf_size:
            self._flush_buffer()
        # 到达 batch_size 行时 flush 到磁盘
        if self._file and self.batch_size > 0 and self._total_rows % self.batch_size == 0:
            self._file.flush()

    def write_rows(self, rows: list):
        for row in rows:
            self.write_row(row)

    def _flush_buffer(self):
        """将内存buffer批量写入csv"""
        if self._buffer and self._writer:
            self._writer.writerows(self._buffer)
            self._buffer.clear()
            self._file.flush()

    def _flush(self):
        self._flush_buffer()
        if self._file:
            self._file.flush()

    def close(self):
        self._flush()
        if self._file:
            self._file.close()
            self._file = None
        print(f'  [{self.table_name}] wrote {self._total_rows} rows -> {self.filepath}')

    @property
    def total_rows(self):
        return self._total_rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
