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

import sys
import time
import signal
import os
import threading

####################################################################################################

from dodreporter.error import DODReporterConfigError, DODReporterError
from dodreporter import config, log, SMTPClient
from dodreporter.runners import DODCryptRunner
from dodreporter.runners import DODHostRunner

####################################################################################################

class DODReporter:
    """Encapsulates the DOD reporter runtime logic."""

    terminate_event = threading.Event()
    smtp_lock       = threading.Lock()

    def terminate(self):
        """Terminate the runner threads by triggering the terminate event."""

        self.terminate_event.set()
        for t in self.threads:
            t.join()

    def join(self):
        """Join all runner threads."""

        for t in self.threads:
            t.join()

    def smtp_send(self, *args, **kwargs):
        """Wrapper for SMTPClient.sendMessage() that sets the sender address
        configured in the global settings."""

        with self.smtp_lock:
            self.smtp_client.sendMessage(
                    sender = self.config.global_settings.smtp_from,
                    *args,
                    **kwargs)

    def __init__(self, config):
        """Construct a new DODReporter instance.

        Parameters:
        config: The global runtime configuration"""

        self.config = config
        gs = config.global_settings

        # Set up smtp client
        self.smtp_client = SMTPClient.SMTPClient(
                hostname = gs.smtp_host,
                port     = gs.smtp_port,
                user     = gs.smtp_user,
                password = gs.smtp_pass,
                tls      = not gs.smtp_no_tls)

        # Set up runner threads
        self.threads = [ DODCryptRunner(self) ] + [ DODHostRunner(self, host_setting.name) for host_setting in config.host_settings ]

        # Start runner threads
        for t in self.threads:
            t.start()

####################################################################################################

def main(argv=sys.argv):
    """Main function for the dod_reporter entry point."""
    try:
        cfg = config.get_config()
        dod = DODReporter(cfg)
        signal.signal(signal.SIGTERM, lambda _, __ : dod.terminate())
        dod.join()
    except DODReporterConfigError as e:
        print(f'\nERROR: {e}')
        sys.exit(1)
    except DODReporterError as e:
        print(f'\nERROR: {e}')
        sys.exit(2)
    except KeyboardInterrupt:
        dod.terminate()
#    except Exception as e:
#        print(f'\nUnknown error: {e}')
#        sys.exit(9)
#
    log.log(f'\nShutting down DOD reporter.')
    sys.exit(0)
