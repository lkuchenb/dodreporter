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
import os
import socket

from dodreporter import config, log

class DODCryptRunner(threading.Thread):

    def notify_crypt_unavailable(self, paths):
        self.reporter.smtp_send(
                recipients = self.reporter.config.global_settings.recipients,
                subject = f"[BACKUP][{socket.gethostname()}] ⚠️ Filesystem decryption required",
                message_text = f"""Dear user,

the backup server '{socket.gethostname()}' was recently restarted. To enable
automated backups, please unlock the backup filesystem using the key device.
                """)

    def notify_crypt_available(self):
        self.reporter.smtp_send(
                recipients = self.reporter.config.global_settings.recipients,
                subject = f"[BACKUP][{socket.gethostname()}] 👌 Filesystem decryption complete.",
                message_text = f"""Dear user,

the backup filesystems on the backup server '{socket.gethostname()}' are now
available and ready to use.
                """)

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
                self.notify_crypt_available()
                return
            else:
                if not self.failmail:
                    log.log("[crypt_run] Missing crypt paths. Sending out email notification.")
                    self.notify_crypt_unavailable(failed_paths)
                    self.failmail = True
            self.reporter.terminate_event.wait(3)
