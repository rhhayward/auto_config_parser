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
    assert parser.get("server", "host", fallback=None) == "localhost"

    # 3. update file on disk
    ini_path.write_text("""[server]\nhost = 127.0.0.1\n""", encoding="utf-8")

    # 4. verify updated value (allow small delay for watchdog event)
    for _ in range(20):  # up to 2 seconds
        if parser.get("server", "host", fallback=None) == "127.0.0.1":
            break
        time.sleep(0.1)
    else:
        pytest.fail("Parser did not reflect updated value within timeout")

    assert parser.get("server", "host", fallback=None) == "127.0.0.1"

    parser.close()

def test_auto_reload_from_symlink(tmp_path):
    """AutoConfigParser should reflect updates when using a symlinked file."""
    target_ini_path = tmp_path / "real_settings.ini"
    symlink_ini_path = tmp_path / "settings_symlink.ini"

    # 1. write initial config to target file
    target_ini_path.write_text("""[database]\nuser = admin\n""", encoding="utf-8")

    # 2. create symlink to the target file
    symlink_ini_path.symlink_to(target_ini_path)

    # 3. read value via AutoConfigParser using the symlink
    parser = AutoConfigParser(symlink_ini_path)
    assert parser.get("database", "user", fallback=None) == "admin"

    # 4. update target file on disk
    target_ini_path.write_text("""[database]\nuser = root\n""", encoding="utf-8")

    # 5. verify updated value (allow small delay for watchdog event)
    for _ in range(20):  # up to 2 seconds
        if parser.get("database", "user", fallback=None) == "root":
            break
        time.sleep(0.1)
    else:
        pytest.fail("Parser did not reflect updated value within timeout")

    assert parser.get("database", "user", fallback=None) == "root"

    # 6. create a new target file and update the symlink
    new_target_ini_path = tmp_path / "new_real_settings.ini"
    new_target_ini_path.write_text("""[database]\nuser = superuser\n""", encoding="utf-8")
    symlink_ini_path.unlink()
    symlink_ini_path.symlink_to(new_target_ini_path)

    # 7. verify updated value from new target (allow small delay for watchdog event)
    for _ in range(20):  # up to 2 seconds
        if parser.get("database", "user", fallback=None) == "superuser":
            break
        time.sleep(0.1)
    else:
        pytest.fail("Parser did not reflect updated value from new target within timeout")

    assert parser.get("database", "user", fallback=None) == "superuser"

    parser.close()
