# Copyright (c) 2020 Leon Kuchenbecker
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

####################################################################################################

import threading
import calendar
from datetime import datetime, timedelta

####################################################################################################

from dodreporter import config, log

####################################################################################################

class DODHostRunner(threading.Thread):
    """Runner that periodically checks recent backups.

    TO BE IMPLEMENTED"""

    def __check(self):
        """Run the periodical check for previously successful backups."""
        print(f"Performing check. Initial check: {self.__initial}")
        self.__initial = False
        pass

    def __init__(self, reporter, host):
        """Construct a new DODHostRunner object.
        
        Parameters:
        reporter: The managing DODReporter instance"""

        threading.Thread.__init__(self)
        self.__reporter = reporter
        self.__host     = host
        self.__initial  = True

    def run(self):
        """Overrides Thread.run()."""

        log.log("[host_run] Host runner started.")

        while not self.__reporter.terminate_event.is_set():
            self.__check()

            # Calculate next reporting timepoint
            # TODO replace hard coded Saturday 12:00 with runtime configuration
            now = datetime.now()
            next_alert = now + timedelta( (5-now.weekday()) % 7 )
            next_alert = next_alert.replace(hour=12, minute=0, second=0, microsecond=0)

            if next_alert - datetime.now() < timedelta(0):
                next_alert += timedelta(days = 7)

            delta = next_alert - datetime.now()

            # Sleep until next reporting timepoint
            log.log(f"DODHostRunner for host '{self.__host}' will be triggered next at {next_alert}")
            self.__reporter.terminate_event.wait(delta.total_seconds())

