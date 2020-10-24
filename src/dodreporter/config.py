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
from dataclasses import dataclass, field
from email.utils import parseaddr

from dodreporter.error import DODReporterError, DODReporterConfigError

####################################################################################################

@dataclass
class DODGlobalSettings:
    """Global settings"""
    recipients : list
    smtp_from : str
    initial_wait : int = 0
    smtp_host : str = None
    smtp_port : int = None
    smtp_user : str = None
    smtp_pass : str = None
    smtp_no_tls : bool = False
    crypt_dirs : list  = field(default_factory=list)

    def __init__(self, config : configparser.ConfigParser):
        """Construct a DODGlobalSettings from a ConfigParser object"""
        general = config['General']
        # Mandatory
        self.recipients = [ parseaddr(addr) for addr in str(general['recipients']).split(',') ]
        self.smtp_from  = parseaddr(str(general['smtpfrom']))
        # Optional
        self.initial_wait = general.getint('initialwait', 0)
        self.smtp_host    = general.get('smtphost', 'localhost')
        self.smtp_port    = general.get('smtpport', '25')
        self.smtp_user    = general.get('smtpuser', None)
        self.smtp_pass    = general.get('smtppass', None)
        self.smtp_no_tls  = general.getboolean('smtpno_tls', False)
        self.crypt_dirs   = general.get('cryptdirs', None).split(',') if general.get('cryptdirs', None) else []

        if self.smtp_from == ('',''):
            s = general['smtpfrom']
            raise DODReporterConfigError(f"Cannot parse email address '{s}'")

        for email in self.recipients:
            if email == ('',''):
                raise DODReporterConfigError(f"Cannot parse email address in global recipients: '{email}'")

####################################################################################################

@dataclass
class DODHostSettings:
    """Per host settings"""

    name       : str
    directory  : str
    recipients : list

    def __init__(self, config : configparser.ConfigParser, section_name : str):
        self.name = section_name
        host = config[self.name]
        # Mandatory
        self.directory = host['Directory']
        self.recipients = [ parseaddr(addr) for addr in host['Recipients'].split(',') ]

        for email in self.recipients:
            if email == ('',''):
                raise DODReporterConfigError(f"Cannot parse email address in global recipients: '{email}'")

####################################################################################################

@dataclass
class DODSettings:
    """DOD runtime settings"""
    global_settings : DODGlobalSettings
    host_settings   : list

####################################################################################################

def get_config():
    configfile = configparser.ConfigParser()
    configfile.read(['/etc/dod_reporter.conf'])

    # Validate 'General' section
    if "General" not in configfile:
        raise DODReporterConfigError("'General' section is missing in the config file.")
    try:
        settings = DODSettings(
                global_settings = DODGlobalSettings(configfile),
                host_settings = []
                )
    except KeyError as e:
        raise DODReporterConfigError(f"Missing global configuration key: {e}")

    # Validate host sections
    for section in configfile.sections():
        if section != "General":
            try:
                settings.host_settings.append(DODHostSettings(configfile, section))
            except KeyError as e:
                raise DODReporterConfigError(f"Missing configuration key {e} in section '{section}'")

    return settings
