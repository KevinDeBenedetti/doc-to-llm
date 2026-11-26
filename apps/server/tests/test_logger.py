import logging
import sys

from src.core import logger
from src.core.logger import build_handlers


def test_logs_go_to_stdout_only_by_default():
    handlers = build_handlers()

    assert len(handlers) == 1
    assert isinstance(handlers[0], logging.StreamHandler)
    assert handlers[0].stream is sys.stdout


def test_log_file_is_opt_in_and_rotated(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, "LOG_FILE_MAX_BYTES", 100)
    log_file = tmp_path / "server.log"

    stdout, file_handler = build_handlers(str(log_file))
    for i in range(10):
        record = {"msg": f"line {i} " + "x" * 30, "levelno": logging.INFO}
        file_handler.emit(logging.makeLogRecord(record))
    file_handler.close()

    assert stdout.stream is sys.stdout
    assert "line 9" in log_file.read_text()
    backups = sorted(path.name for path in tmp_path.glob("server.log.*"))
    assert backups == [f"server.log.{n}" for n in range(1, logger.LOG_FILE_BACKUPS + 1)]
