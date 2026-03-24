"""
stages/ — pipeline stage implementations.

Adds the project root to sys.path so stage modules can import from root-level
modules (interfaces, context, tools, config, llm) without needing a full
package restructure.
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
