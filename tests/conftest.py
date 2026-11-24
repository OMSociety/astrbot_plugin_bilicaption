"""测试环境未安装 AstrBot 时，提供 astrbot.api.logger 的最小替身。"""

import logging
import sys
import types

try:
    import astrbot.api  # noqa: F401
except ImportError:
    api = types.ModuleType("astrbot.api")
    api.logger = logging.getLogger("astrbot")
    pkg = types.ModuleType("astrbot")
    pkg.api = api
    sys.modules["astrbot"] = pkg
    sys.modules["astrbot.api"] = api
