instruments
===================

Repository for shared instruments. This includes things controlled over serial directly and visa through gbip, serial, or usb. This also provides the Python serial library, as many instruments require it, and it is often useful in parallel for talking to devices under test. <Edited by Ishaan,2>

Note for OSX/VISA:
-------------------
- Install NI-VISA (http://www.ni.com/download/ni-visa-5.3/3824/en/)
- NI only provides a 32-bit version of the VISA library for OSX.  Python needs to be run in 32bit mode to deal with that.
    Make this happen by setting an environment variable VERSIONER_PYTHON_PREFER_32_BIT to 'yes.'
    "export VERSIONER_PYTHON_PREFER_32_BIT=yes"
- To use GPIB instruments you will need a driver for the usb bridge. NI's is here: http://www.ni.com/download/ni-488.2-3.0.1/2703/en/

RUNNING TESTS/ GUIDELINES:
-------------------
- All code in this repository should be linted BEFORE opening a PR. This can be done by:
    - Checking out the test_utils (ssh://git@git.corp.squareup.com/hw/test_utils.git) repository to your ~/Development/ Directory
    - Running: <code>python ../test_utils/pygiene.py . -cfg pygiene.cfg -pep8 ../test_utils/pep8.cfg -pylint ../test_utils/pylint.cfg </code> in the root directory of this repository
- If possible, run the tests/ on any files you may have changed. This is a bit wonky. One needs to run the tests as a module to get around python import from above weirdness:
    - e.g. dmm test: python -m tests.e34461_dmm_test TCPIP::172.24.1.215
- If you implement a new driver, please implement a test if at all possible! (come see Cliff for how to Jenkins)


VISA:
-------------------
- visa_instrument provides a generic base class that wraps pyvisa's Instrument with some convenience functions.
    All drivers for visa instruments should inherit from this.
- Agilent 34461A dmm (Command-compatible with 34460, 34410 and 34411, but ranges/settings may differ.):
    - http://literature.cdn.keysight.com/litweb/pdf/34460-90901.pdf
    - Tested on OSX:
        - TCP/IP
        - USB
    - Tested on Windows:
        - USB
- Agilent e364x Power supplies:
    - http://cp.literature.agilent.com/litweb/pdf/E3646-90001.pdf * only 1 channel.
    - http://cp.literature.agilent.com/litweb/pdf/E3640-90001.pdf
    - Tested on OSX:
        - USB -> GPIB (using NI module)
    - Tested on Windows:
        - USB -> GPIB (using NI Module)
- Agilent 34972 MUX/DMM chassis (command-compatible with 34970)
    - Tested on OSX USB.

Serial:
-------------------
(Library provided with minor fix to make windows work)
- BK8500 dc load (provided my manufacturer)
- KTA Relay
    - Tested on OSX and Windows
- linmotasf(currently not in this repo, fix!)

Note for LitePoint equipments iqNFC and iqXel:
-------------------
- Both support SCPI and communicate with ethernet cable.
- The drivers are stored here: sftp1.corp.squareup.com:/app/factories/home/foxlink1/drivers

Other:
-------------------
- nircmd windows utility (see http://www.nirsoft.net/utils/nircmd.html)
- jlink programmer
- ni_frequency_ctr
- ni_usb_dio
- generic_gpib_driver (to be deprecated)
- iqNFC 
- iqXel 
