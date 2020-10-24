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

import sys
import time
import threading
import signal
import os
import socket

####################################################################################################

from dodreporter.error import DODReporterConfigError, DODReporterError
from dodreporter import config, log, SMTPClient

####################################################################################################

class DODCryptRunner(threading.Thread):

    def notify_crypt_unavailable(self, paths):
        self.reporter.smtp_send(
                recipients = self.reporter.config.global_settings.recipients,
                subject = f"[BACKUP][{socket.gethostname()}] Filesystem decryption",
                message_text = "Please decrypt the filesystem.")

    def notify_crypt_available(self):
        pass

    def __init__(self, settings : config.DODSettings, reporter):
        threading.Thread.__init__(self)
        self.enabled           = True
        self.paths             = settings.global_settings.crypt_dirs
        self.failmail          = False
        self.last_status       = None
        self.reporter          = reporter

    def check(self):
        status = [ os.path.exists(p) for p in self.paths ]

        # Log current state if it has changed from the previous observed state
        if status != self.last_status:
            for path, exists in zip(self.paths, status):
                if exists:
                    log.log(f"[crypt_run] Crypt path '{path}' exists.")
                else:
                    log.log(f"[crypt_run] Crypt path '{path}' does not exist.")

        # Keep in mind last state for future checks
        self.last_status = status

        # Return all missing paths
        return [ path for path, exists in zip(self.paths, status) if not exists ]

    def run(self):
        if not self.paths:
            log.log("[crypt_run] Crypt runner not starting up, no crypt dir paths configured.")
            return
        log.log("[crypt_run] Crypt runner started.")
        while not self.reporter.terminate_event.is_set():
            failed_paths = self.check()
            if not failed_paths:
                log.log("[crypt_run] All crypt paths are available. Crypt runner terminating.")
                return
            else:
                if not self.failmail:
                    log.log("[crypt_run] Missing crypt paths. Sending out email notification.")
                    self.notify_crypt_unavailable(failed_paths)
                    self.failmail = True
            self.reporter.terminate_event.wait(3)

####################################################################################################

class DODHostRunner(threading.Thread):

    def __init__(self, settings : config.DODSettings, reporter):
        threading.Thread.__init__(self)
        self.reporter = reporter

    def run(self):
        log.log("[host_run] Host runner started.")
        while not self.reporter.terminate_event.is_set():
            self.reporter.terminate_event.wait(3)
        pass

####################################################################################################

class DODReporter:

    terminate_event = threading.Event()
    smtp_lock       = threading.Lock()

    def terminate(self):
        self.terminate_event.set()
        for t in self.threads:
            t.join()

    def join(self):
        for t in self.threads:
            t.join()

    def smtp_send(self, *args, **kwargs):
        with self.smtp_lock:
            self.smtp_client.sendMessage(
                    sender = self.config.global_settings.smtp_from,
                    *args,
                    **kwargs)

    def __init__(self, config):
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
        self.threads = [
                DODCryptRunner(config, self),
                DODHostRunner(config, self)
                ]

        # Start runner threads
        for t in self.threads:
            t.start()

####################################################################################################

def main(argv=sys.argv):
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
    except Exception as e:
        print(f'\nUnknown error: {e}')
        sys.exit(9)

    log.log(f'\nShutting down DOD reporter.')
    sys.exit(0)
