# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import sys

from commons.compat import Path
from git_hooks_1c.core import run

sys.path.insert(0, str(Path(__file__).absolute().parent.parent))

if __name__ == '__main__':
    run()
