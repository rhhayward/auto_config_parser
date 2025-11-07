"""Tests for AutoConfigParser live reload capability."""

from __future__ import annotations

import time

import pytest

from auto_config_parser import AutoConfigParser


def test_auto_reload(tmp_path):
    """AutoConfigParser should reflect file updates automatically."""
    ini_path = tmp_path / "settings.ini"

    # 1. write initial config
    ini_path.write_text("""[server]\nhost = localhost\n""", encoding="utf-8")

    # 2. read value via AutoConfigParser
    parser = AutoConfigParser(ini_path)
    assert parser.get("server", "host") == "localhost"

    # 3. update file on disk
    ini_path.write_text("""[server]\nhost = 127.0.0.1\n""", encoding="utf-8")

    # 4. verify updated value (allow small delay for watchdog event)
    for _ in range(20):  # up to 2 seconds
        if parser.get("server", "host") == "127.0.0.1":
            break
        time.sleep(0.1)
    else:
        pytest.fail("Parser did not reflect updated value within timeout")

    assert parser.get("server", "host") == "127.0.0.1"

    parser.close()
