from __future__ import annotations

from . import cli as _cli
from . import common as _common
from . import conversion as _conversion
from . import html_parser as _html_parser
from . import schema_inference as _schema_inference
from . import snippet_parser as _snippet_parser

_MODULES = (
    _common,
    _html_parser,
    _snippet_parser,
    _schema_inference,
    _conversion,
    _cli,
)

for _module in _MODULES:
    for _name, _value in vars(_module).items():
        if _name.startswith("__"):
            continue
        globals()[_name] = _value

__all__ = [name for name in globals() if not name.startswith("__")]
