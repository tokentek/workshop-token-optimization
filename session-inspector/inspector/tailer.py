"""Incremental JSONL reader.

Reads only the bytes that were appended since the last poll. Keeps an
incomplete last line (and split UTF-8 sequences) in a buffer until the rest
arrives. Detects truncation and file replacement.
"""
import json
import os


class JsonlTail:
    def __init__(self, path):
        self.path = path
        self.offset = 0
        self.buf = b""
        self.ident = None
        self.bad_lines = 0

    def poll(self):
        """Read new complete records.

        Returns (reset, records). reset=True means the file was truncated or
        replaced: the caller must drop all state built from earlier records.
        """
        try:
            st = os.stat(self.path)
        except OSError:
            return False, []
        ident = (st.st_dev, st.st_ino)
        reset = False
        if self.ident is not None and (ident != self.ident or st.st_size < self.offset):
            reset = True
            self.offset = 0
            self.buf = b""
            self.bad_lines = 0
        self.ident = ident
        if st.st_size == self.offset:
            return reset, self._flush_complete_buffer()
        with open(self.path, "rb") as f:
            f.seek(self.offset)
            data = f.read(st.st_size - self.offset)
        self.offset += len(data)
        data = self.buf + data
        lines = data.split(b"\n")
        self.buf = lines.pop()
        records = []
        for line in lines:
            rec = self._parse(line)
            if rec is not None:
                records.append(rec)
        records.extend(self._flush_complete_buffer())
        return reset, records

    def _flush_complete_buffer(self):
        # A last line without "\n" is only accepted when it is valid JSON.
        if not self.buf.strip():
            return []
        try:
            rec = json.loads(self.buf.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return []
        self.buf = b""
        return [rec] if isinstance(rec, dict) else []

    def _parse(self, line):
        line = line.strip()
        if not line:
            return None
        try:
            rec = json.loads(line.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self.bad_lines += 1
            return None
        return rec if isinstance(rec, dict) else None
