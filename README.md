# auto_config_parser

A drop-in replacement for Python’s builtin [`configparser.ConfigParser`](https://docs.python.org/3/library/configparser.html) that automatically reloads the INI configuration file when it is modified on disk.

`AutoConfigParser` uses the lightweight [`watchdog`](https://pypi.org/project/watchdog/) library to monitor the directory that contains your configuration file. Changes are detected instantly and the parser transparently refreshes its internal state, so every read operation (`get`, `items`, mapping access, …) always reflects the current file contents.

## Installation

```bash
pip install git+https://github.com/rhhayward/auto_config_parser.git@main
```

## Quick-start

```python
from auto_config_parser import AutoConfigParser

# Create a parser bound to the file (it will be created if it does not exist)
parser = AutoConfigParser("settings.ini")

# Read a value
value = parser.get("server", "host")
print(value)

# …later, after you _edit & save_ settings.ini in another process…
print(parser.get("server", "host"))  # ➜ Updated value without reload()!

# Stop the background watcher when you are done
parser.close()
```

`AutoConfigParser` implements the entire public API of `ConfigParser`, so you can use it as a **drop-in replacement** in existing projects.

### Context manager

```python
with AutoConfigParser("settings.ini") as cfg:
    print(cfg.sections())
    # watcher stops automatically at the end of the with-block
```

## Why?

This is built for a k8s service where configuration is provided via a ConfigMap mounted as a file. Without this, the service would need to be restarted to pick up configuration changes.  This allows configuration changes to be executed without downtime.

## License

MIT © Ryan Hayward
