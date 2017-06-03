# -*- coding: utf-8 -*-

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    test_visa.py - PyVISA test code for visa.py
#
#    Copyright © 2014
#                Florian Bauer <fbauer.devel@gmail.com>
#                     
#    This file is part of PyVISA.
#  
#    PyVISA is free software; you can redistribute it and/or modify it under
#    the terms of the MIT licence:
#
#    Permission is hereby granted, free of charge, to any person obtaining a
#    copy of this software and associated documentation files (the "Software"),
#    to deal in the Software without restriction, including without limitation
#    the rights to use, copy, modify, merge, publish, distribute, sublicense,
#    and/or sell copies of the Software, and to permit persons to whom the
#    Software is furnished to do so, subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included in
#    all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#

from __future__ import division, unicode_literals, print_function, absolute_import
import collections
import struct

from pyvisa import legacy
from pyvisa.legacy import InvalidBinaryFormat
import pytest
from mock import Mock

def packfloats1(fmt, floats):
    data = b''.join(struct.pack(fmt, num) for num in floats)
    datalen =  ("%d" % len(data)).encode('ascii')
    return b"#" + ("%d" % len(datalen)).encode('ascii') + datalen + data

def packfloats2(fmt, floats):
    return b'#0' + b''.join(struct.pack(fmt, num) for num in floats) + b'\n'

class TestInstrument(object):
    
    def pytest_funcarg__instrument(self, request):
        monkeypatch = request.getfuncargvalue('monkeypatch')
        monkeypatch.setattr(legacy.Instrument,
                            'interface_type',
                            legacy.VI_INTF_GPIB)
        my_attr = MyAttribute()
        monkeypatch.setattr(pyvisa.wrapper.vpp43, "get_attribute", my_attr.get_attribute)
        monkeypatch.setattr(pyvisa.wrapper.vpp43, "set_attribute", my_attr.set_attribute)
        return legacy.Instrument(1)

    def test_repr(self, instrument):
        # XXX: refactor so that a resource_name is
        # printed here
        assert repr(instrument) in ("Instrument('')",
                                    "Instrument(b'')")
    
    @pytest.mark.parametrize(('message', 'expected'),
                             [(b"hi there", b"hi there\r\n"),
                              (b"hi there\r", b"hi there\r\r\n"),
                              (b"hi there\n", b"hi there\n\r\n"),
                              (b"hi there\r\n", b"hi there\r\n")])
    def test_write(self, monkeypatch, instrument, message, expected):
        my_write = Mock()
        monkeypatch.setattr(pyvisa.wrapper.vpp43, 'write', my_write)
        instrument.write(message)
        print(repr(instrument.term_chars))
        my_write.assert_called_with(0, expected)

    @pytest.mark.parametrize(('message', 'expected'),
                             [(b"hi there", b"hi there\n"),
                              (b"hi there\r", b"hi there\r\n"),
                              (b"hi there\n", b"hi there\n"),
                              (b"hi there\r\n", b"hi there\r\n")])
    def test_write_termchars_set(self, monkeypatch, instrument,
                                 message, expected):
        my_write = Mock()
        monkeypatch.setattr(pyvisa.wrapper.vpp43, 'write', my_write)
        instrument.term_chars = b'\n'
        instrument.write(message)
        my_write.assert_called_with(0, expected)
        
    @pytest.mark.parametrize(('message', 'expected'),
                             [(b"hi there", b"hi there\r\n"),
                              (b"hi there\r", b"hi there\r\r\n"),
                              (b"hi there\n", b"hi there\n\r\n"),
                              (b"hi there\r\n", b"hi there\r\n")])
    def test_write_delay_set(self, monkeypatch, instrument, message, expected):
        my_write = Mock()
        my_sleep = Mock()
        monkeypatch.setattr(pyvisa.wrapper.vpp43, 'write', my_write)
        monkeypatch.setattr(legacy.time, 'sleep', my_sleep)
        instrument.delay = 1
        instrument.write(message)
        print(repr(instrument.term_chars))
        my_write.assert_called_with(0, expected)
        my_sleep.assert_called_with(1)
        
    @pytest.mark.parametrize(('message', 'expected'),
                             [(b"hi there", b"hi there"),
                              (b"hi there\r\n", b"hi there"),
                              (b"hi there\r\n\r\n", b"hi there"),
                              ])
    def test_strip_term_chars(self, instrument, message, expected):
        assert instrument._strip_term_chars(message) == expected

    @pytest.mark.parametrize(('message', 'expected'),
                             [(b"hi there", b"hi there"),
                              # XXX: \r is stripped here as well. Ok?
                              (b"hi there\r\n", b"hi there"),
                              (b"hi there\n", b"hi there"),
                              (b"hi there\n\n", b"hi there"),
                              ])
    def test_strip_term_chars__term_chars_set(self, instrument,
                                              message, expected):
        instrument.term_chars = b'\n'
        assert instrument._strip_term_chars(message) == expected

    def test_term_chars_default(self, instrument):
        """default term chars are CR+LF, property is set to None"""
        assert instrument.term_chars is None

    @pytest.mark.parametrize("value", [True, False])
    def test_send_end(self, instrument, value):
        instrument.send_end = value
        assert instrument.send_end == value

    def test_read_raw(self, monkeypatch, instrument):
        my_read = Mock(return_value=b'some bytes\r\n')
        my_get_status = Mock(side_effect=[legacy.VI_SUCCESS_MAX_CNT, 0])
        monkeypatch.setattr(pyvisa.wrapper.vpp43, 'read', my_read)
        monkeypatch.setattr(pyvisa.wrapper.vpp43, 'get_status', my_get_status)
        result = instrument.read_raw()
        assert result == b'some bytes\r\nsome bytes\r\n'

    def test_read(self, monkeypatch, instrument):
        my_read = Mock(return_value=b'some bytes\r\n')
        my_get_status = Mock(side_effect=[legacy.VI_SUCCESS_MAX_CNT, 0])
        monkeypatch.setattr(pyvisa.wrapper.vpp43, 'read', my_read)
        monkeypatch.setattr(pyvisa.wrapper.vpp43, 'get_status', my_get_status)
        result = instrument.read()
        assert result == b'some bytes\r\nsome bytes'
        
    @pytest.mark.parametrize(('format', 'input', 'expected'),
                             [(None, b'some bytes\r\n', []),
                              (legacy.ascii, b'some bytes\r\n', []),
                              (legacy.ascii, b'1.25', [1.25]),
                              (legacy.ascii, b'1.25 2.5', [1.25, 2.5]),
                              (legacy.ascii, b'1.25, 2.5', [1.25, 2.5]),

                              (legacy.single, packfloats1('<f', [1.25]), [1.25]),
                              (legacy.single, b'junk' + packfloats1('<f', [1.25]), [1.25]),
                              (legacy.single, packfloats1('<f', [1.25, 2.5]), [1.25, 2.5]),
                              (legacy.single | legacy.big_endian,
                               packfloats1('>f', [1.25]), [1.25]),
                              (legacy.single | legacy.big_endian,
                               b'junk' + packfloats1('>f', [1.25]), [1.25]),
                              (legacy.single | legacy.big_endian,
                               packfloats1('>f', [1.25, 2.5]), [1.25, 2.5]),

                              (legacy.double, packfloats1('<d', [1.25]), [1.25]),
                              (legacy.double, b'junk' + packfloats1('<d', [1.25]), [1.25]),
                              (legacy.double, packfloats1('<d', [1.25, 2.5]), [1.25, 2.5]),
                              (legacy.double | legacy.big_endian,
                               packfloats1('>d', [1.25]), [1.25]),
                              (legacy.double | legacy.big_endian,
                               b'junk' + packfloats1('>d', [1.25]), [1.25]),
                              (legacy.double | legacy.big_endian,
                               packfloats1('>d', [1.25, 2.5]), [1.25, 2.5]),
                              
                              (legacy.single, packfloats2('<f', [1.25]), [1.25]),
                              (legacy.single, b'junk' + packfloats2('<f', [1.25]), [1.25]),
                              (legacy.single, packfloats2('<f', [1.25, 2.5]), [1.25, 2.5]),
                              (legacy.single | legacy.big_endian,
                               packfloats2('>f', [1.25]), [1.25]),
                              (legacy.single | legacy.big_endian,
                               b'junk' + packfloats2('>f', [1.25]), [1.25]),
                              (legacy.single | legacy.big_endian,
                               packfloats2('>f', [1.25, 2.5]), [1.25, 2.5]),

                              (legacy.double, packfloats2('<d', [1.25]), [1.25]),
                              (legacy.double, b'junk' + packfloats2('<d', [1.25]), [1.25]),
                              (legacy.double, packfloats2('<d', [1.25, 2.5]), [1.25, 2.5]),
                              (legacy.double | legacy.big_endian,
                               packfloats2('>d', [1.25]), [1.25]),
                              (legacy.double | legacy.big_endian,
                               b'junk' + packfloats2('>d', [1.25]), [1.25]),
                              (legacy.double | legacy.big_endian,
                               packfloats2('>d', [1.25, 2.5]), [1.25, 2.5]), 
                              ])
    def test_read_values(self, monkeypatch, instrument,
                         format, input, expected):
        my_read = Mock(return_value=input)
        my_get_status = Mock(return_value=0)
        monkeypatch.setattr(pyvisa.wrapper.vpp43, 'read', my_read)
        monkeypatch.setattr(pyvisa.wrapper.vpp43, 'get_status', my_get_status)
        result = instrument.read_values(format)
        assert result == expected
        
    @pytest.mark.parametrize(('format', 'input', 'expected_exception'),
                             [(legacy.single, b'bytes\r\n', InvalidBinaryFormat),
                              (legacy.single, b'#8', InvalidBinaryFormat),
                              (legacy.single, b'#0deadbeef', InvalidBinaryFormat),
                              (legacy.single, b'#deadbeef', InvalidBinaryFormat),
                              (legacy.double, packfloats1('<f', [1.25]), InvalidBinaryFormat),
                              ])
    def test_read_values_errors(self, monkeypatch, instrument,
                                format, input, expected_exception):
        my_read = Mock(return_value=input)
        my_get_status = Mock(return_value=0)
        monkeypatch.setattr(pyvisa.wrapper.vpp43, 'read', my_read)
        monkeypatch.setattr(pyvisa.wrapper.vpp43, 'get_status', my_get_status)
        with pytest.raises(expected_exception):
            instrument.read_values(format)


    
    
class TestGpibInstrument(TestInstrument):
    
    def pytest_funcarg__instrument(self, request):
        monkeypatch = request.getfuncargvalue('monkeypatch')
        monkeypatch.setattr(legacy.GpibInstrument,
                            'interface_type',
                            legacy.VI_INTF_GPIB)
        monkeypatch.setattr(legacy.GpibInstrument, 'stb', 0x40)
        my_attr = MyAttribute()
        monkeypatch.setattr(pyvisa.wrapper.vpp43, "get_attribute", my_attr.get_attribute)
        monkeypatch.setattr(pyvisa.wrapper.vpp43, "set_attribute", my_attr.set_attribute)
        return legacy.GpibInstrument(1)
    
    @pytest.mark.parametrize('timeout', [None, 0, 25, 4294967])
    def test_wait_for_srq(self, instrument, timeout):
        instrument.wait_for_srq(timeout)

    @pytest.mark.parametrize('timeout', [-1, 4294968])
    def test_wait_for_srq_raises(self, instrument, timeout):
        with pytest.raises(ValueError):
            instrument.wait_for_srq(timeout)
            
    def test_repr(self, instrument):
        # XXX: refactor so that a resource_name is
        # printed here
        # XXX: maybe test can be merged with parent class
        assert repr(instrument) in  ("GpibInstrument('')",
                                     "GpibInstrument(b'')")


class TestSerialInstrument(TestInstrument):

    def pytest_funcarg__instrument(self, request):
        monkeypatch = request.getfuncargvalue('monkeypatch')
        monkeypatch.setattr(legacy.SerialInstrument,
                            'interface_type',
                            legacy.VI_INTF_ASRL)
        my_attr = MyAttribute()
        monkeypatch.setattr(pyvisa.wrapper.vpp43, "get_attribute", my_attr.get_attribute)
        monkeypatch.setattr(pyvisa.wrapper.vpp43, "set_attribute", my_attr.set_attribute)
        return legacy.SerialInstrument(1)
    
    def test_term_chars_default(self, instrument):
        """default term char is CR"""
        assert instrument.term_chars == b'\r'
        
    def test_repr(self, instrument):
        # XXX: refactor so that a resource_name is
        # printed here
        # XXX: maybe test can be merged with parent class
        assert repr(instrument) in ("SerialInstrument('')",
                                    "SerialInstrument(b'')")

    
    @pytest.mark.parametrize(('message', 'expected'),
                             [(b"hi there", b"hi there\r"),
                              (b"hi there\r", b"hi there\r"),
                              (b"hi there\n", b"hi there\n\r"),
                              (b"hi there\r\n", b"hi there\r\n\r")])
    def test_write(self, monkeypatch, instrument, message, expected):
        TestInstrument.test_write(self, monkeypatch, instrument,
                                  message, expected)

    @pytest.mark.parametrize(("message", "expected"),
                             [(b"hi there", b"hi there\r"),
                              (b"hi there\r", b"hi there\r"),
                              (b"hi there\n", b"hi there\n\r"),
                              (b"hi there\r\n", b"hi there\r\n\r")])
    def test_write_delay_set(self, monkeypatch, instrument, message, expected):
        TestInstrument.test_write_delay_set(self, monkeypatch, instrument,
                                            message, expected)

    def test_baud_rate(self, instrument):
        instrument.baud_rate = 115200
        assert instrument.baud_rate == 115200
        
    def test_data_bits(self, instrument):
        instrument.data_bits = 5
        assert instrument.data_bits == 5
        
    @pytest.mark.parametrize("values", [4, 9])
    def test_data_bits_bad_values(self, instrument, values):
        with pytest.raises(ValueError):
            instrument.data_bits = values

    @pytest.mark.parametrize("value", [1., 1.5, 2.])
    def test_stop_bits(self, instrument, value):
        instrument.stop_bits = value
        assert instrument.stop_bits == value
        
    @pytest.mark.parametrize("value", [0.8, 3])
    def test_stop_bits_bad_values(self, instrument, value):
        with pytest.raises(ValueError):
            instrument.stop_bits = value

    @pytest.mark.parametrize("value", [
        legacy.no_parity,
        legacy.odd_parity,
        legacy.even_parity,
        legacy.mark_parity,
        legacy.space_parity,])
    def test_parity(self, instrument, value):
        instrument.parity = value
        assert instrument.parity == value

    @pytest.mark.parametrize("value", [
        legacy.no_end_input,
        legacy.last_bit_end_input,
        legacy.term_chars_end_input,
        ])
    def test_end_input(self, instrument, value):
        instrument.end_input = value
        assert instrument.end_input == value
        
class MyAttribute(object):
    
    def __init__(self):
        self.data = collections.defaultdict(lambda: b"")
        
    def set_attribute(self, vi, attribute, value):
        self.data[(vi, attribute)] = value
        
    def get_attribute(self, vi, attribute):
        return self.data[(vi, attribute)]
