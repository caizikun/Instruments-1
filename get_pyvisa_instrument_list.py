#!/usr/bin/env python

import pyvisa.visa as visa
import pyvisa.pyvisa.util as visa_util

print visa_util.get_debug_info()

RESOURCEMANAGER = visa.ResourceManager()
INSTRUMENTS = RESOURCEMANAGER.list_resources()
for instrument in INSTRUMENTS:
    print instrument
