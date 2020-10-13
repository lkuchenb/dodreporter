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

import configparser
import re

from dodreporter.error import DODReporterError, DODReporterConfigError

def is_email(s):
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", s))

def get_config():
    configfile = configparser.ConfigParser()
    configfile.read(['/etc/dod_reporter.conf'])

    # Validate 'General' section
    if "General" not in configfile:
        raise DODReporterConfigError("'General' section is missing in the config file.")
    if "Recipients" not in configfile['General']:
        raise DODReporterConfigError("'General' section is missing 'Recipients' attribute.")
    for email in configfile['General']['Recipients'].split(','):
        if not is_email(email):
            raise DODReporterConfigError(f"Cannot parse email address in config file: {email}")

    # Validate host sections
    for section in configfile.sections():
        if section == "General":
            continue

        for req_host_key in ["Recipients", "Directory"]:
            if req_host_key not in configfile[section]:
                raise DODReporterConfigError(f"Missing config key '{req_host_key}' in section '{section}'")

    return configfile
