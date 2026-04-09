"""
JSONL(JSON Lines)批量写入器
行为日志类数据以JSONL格式输出, 贴近真实大数据采集场景
P2优化: 攒buffer批量写入减少IO调用
"""
import json
import os

from config import CSV_BEHAVIOR_BATCH

# 内存buffer行数上限
_WRITE_BUFFER_SIZE = 2000


class JsonlWriter:
    """流式JSONL写入器, 每行一个JSON对象"""

    def __init__(self, out_dir: str, filename: str, fieldnames: list,
                 batch_size: int = CSV_BEHAVIOR_BATCH):
        self.table_name = filename.replace('.jsonl', '')
        self.fieldnames = fieldnames
        self.batch_size = batch_size
        self.filepath = os.path.join(out_dir, filename)
        self._total_rows = 0
        self._file = None
        self._buffer = []
        self._buf_size = _WRITE_BUFFER_SIZE
        self.open()

    def open(self):
        self._file = open(self.filepath, 'w', encoding='utf-8')
        return self

    def write_row(self, row: list):
        """接收与CsvWriter相同的list参数, 内部转为dict后写JSON"""
        if not self._file:
            return
        obj = dict(zip(self.fieldnames, row))
        self._buffer.append(json.dumps(obj, ensure_ascii=False))
        self._total_rows += 1
        if len(self._buffer) >= self._buf_size:
            self._flush_buffer()
        if self.batch_size > 0 and self._total_rows % self.batch_size == 0:
            self._file.flush()

    def write_rows(self, rows: list):
        for row in rows:
            self.write_row(row)

    def _flush_buffer(self):
        if self._buffer and self._file:
            self._file.write('\n'.join(self._buffer))
            self._file.write('\n')
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
