"""auto_config_parser

Drop-in replacement for Python's builtin configparser.ConfigParser that
automatically reloads configuration data from the INI file as soon as it
changes on disk using the ``watchdog`` file-system observer.

Example
-------
>>> from auto_config_parser import AutoConfigParser
>>> parser = AutoConfigParser("settings.ini")
>>> print(parser.get("section", "key"))  # value is read
# ... later, someone edits settings.ini and saves it ...
>>> print(parser.get("section", "key"))  # value is automatically refreshed

The watcher runs in a background thread. Call ``close()`` or use the parser
as a context manager to stop it when you are done.
"""

from .auto_config_parser import AutoConfigParser

__all__ = ["AutoConfigParser"]
