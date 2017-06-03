# -*- coding: utf-8 -*-
"""
    pyvisa
    ~~~~~~

    Python wrapper of National Instrument (NI) Virtual Instruments Software
    Architecture library (VISA).

    This file is part of PyVISA.

    :copyright: (c) 2014 by the PyVISA authors.
    :license: MIT, see COPYING for more details.
"""

from __future__ import division, unicode_literals, print_function, absolute_import
import os
import logging
import subprocess

#import pkg_resources

from . import compat
logger = logging.getLogger('pyvisa')
logger.addHandler(compat.NullHandler())

__version__ = "unknown"
try:  # try to grab the commit version of our package
    __version__ = (subprocess.check_output(["git", "describe"],
                                           stderr=subprocess.STDOUT,
                                           cwd=os.path.dirname(os.path.abspath(__file__)))).strip()
except:  # on any error just try to grab the version that is installed on the system
    try:
        __version__ = pkg_resources.get_distribution('pyvisa').version
    except:
        pass  # we seem to have a local copy without any repository control or installed without setuptools
              # so the reported version will be __unknown__

from . import ctwrapper
from .errors import *
