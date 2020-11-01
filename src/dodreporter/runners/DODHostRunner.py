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

import threading

from dodreporter import config, log

class DODHostRunner(threading.Thread):
    """Runner that periodically checks recent backups.

    TO BE IMPLEMENTED"""

    def __init__(self, reporter):
        """Construct a new DODHostRunner object.
        
        Parameters:
        reporter: The managing DODReporter instance"""

        threading.Thread.__init__(self)
        self.reporter = reporter

    def run(self):
        """Overrides Thread.run()."""

        log.log("[host_run] Host runner started.")
        while not self.reporter.terminate_event.is_set():
            self.reporter.terminate_event.wait(3)
        pass

