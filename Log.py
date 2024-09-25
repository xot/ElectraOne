# Log
# - Logging and debugging
#
# Part of ElectraOne
#
# Ableton Live MIDI Remote Script for the Electra One
#
# Author: Jaap-henk Hoepman (info@xot.nl)
#
# Distributed under the MIT License, see LICENSE
#

# Python imports
import threading

# Local imports
from .config import *

class Log:

    # Main thread identifier; used to differentiate main thread and spawned
    # thread log messages
    _mainthread =  None
    
    def __init__(self, c_instance):
        """Initialise.
           - c_instance: Live interface object (see __init.py__)
        """
        # c_instance is/should be the object passed by Live when
        # initialising the remote script (see __init.py__). Through
        # c_instance we have access to Live: the log file, the midi map
        # the current song (and through that all devices and mixers)
        assert c_instance
        self._c_instance = c_instance
        # the first time Log is initialised it is in the main ElectraOne thread
        if not Log._mainthread:
            Log._mainthread = threading.get_ident()

    def debug(self, level, m):
        """Write a debug message to the log, if level < DEBUG.
           Distinguish between main and thread messages; and between mixer-only
           and other control modes.
        """
        if Log._mainthread == threading.get_ident():
            debugprefix = '-' if (CONTROL_MODE == CONTROL_MIXER_ONLY) else '='
        else: # we are in a thread
            debugprefix = '/' if (CONTROL_MODE == CONTROL_MIXER_ONLY) else 'X'
        if level <= DEBUG:
            indent = debugprefix * (level+1)
            # write readable log entries also for multi-line messages
            for l in m.splitlines(keepends=True):
                self._c_instance.log_message(f'E1 (debug): {indent} {l}')  

    def warning(self, m):
        """Write a warning message to the log.
        """
        # write readable log entries also for multi-line messages
        for l in m.splitlines(keepends=True):
            self._c_instance.log_message(f'E1 (warning): ! {l}')
                
    def log_message(self, m):
        """Write a log message to the log.
        """
        self._c_instance.log_message(f'E1 (log): {m}')

    def show_message(self, m):
        """Show a message in the Live message line (lower left corner).
        """
        self._c_instance.show_message(m)

