# -*- coding: utf-8 -*-

"""
 *  Copyright (C) 2011-2016, it-novum GmbH <community@openattic.org>
 *
 *  openATTIC is free software; you can redistribute it and/or modify it
 *  under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; version 2.
 *
 *  This package is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
"""

import os
import pwd
import errno
import os.path
import logging
import subprocess

from datetime import datetime
from select import select, error

from django.conf import settings

from cmdlog.models import LogEntry
from ifconfig.models import Host
from utilities import is_executable_installed


def invoke(args, close_fds=True, return_out_err=False, log=True, stdin=None, fail_on_err=True):
    """ Invoke a subprocess with the given args and log the output.

        Parameters:

        * close_fds=True       -- If False, file descriptors will not be closed for the child
                                  process.
        * return_out_err=False -- If True, stdout and stderr of the child will be returned.
        * log=True             -- If False, the command's execution will not be logged.
        * stdin=None           -- Any string given will be sent to the child's stdin.
        * fail_on_err=True     -- If the child's exit code is not zero, raise SystemError.

        Returns the exit code if return_out_err is False, and a tuple of (exit code, stdout, stderr)
        otherwise.
    """
    starttime = datetime.now()

    procenv = os.environ.copy()
    procenv["LANG"] = procenv["LANGUAGE"] = procenv["LC_ALL"] = "C"

    proc = subprocess.Popen(
        [arg.encode("UTF-8") if isinstance(arg, unicode) else arg for arg in args],
        stdin=(None if stdin is None else subprocess.PIPE), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, close_fds=close_fds, env=procenv)

    procout = ""
    procerr = ""

    cmdline = ' '.join(['"' + arg + '"' for arg in args])
    out = ["> " + cmdline]

    if stdin is not None:
        try:
            proc.stdin.write(stdin)
        except IOError:
            pass
        proc.stdin.close()

    process_alive = True
    last_data_has_been_read = False
    while process_alive or not last_data_has_been_read:
        try:
            rdy_read, rdy_write, rdy_other = select([proc.stdout, proc.stderr], [], [], 0.1)
            if proc.stdout in rdy_read:
                data = proc.stdout.read().decode("UTF-8")
                procout += data
                out.extend(["O " + line for line in data.split("\n") if line])
            if proc.stderr in rdy_read:
                data = proc.stderr.read().decode("UTF-8")
                procerr += data
                out.extend(["E " + line for line in data.split("\n") if line])
            if proc.poll() is not None:
                if process_alive:
                    proc.wait()
                    process_alive = False
                else:
                    last_data_has_been_read = True
        except error, err:
            # Catch and ignore Interrupted System Call exceptions.
            # Those can occur when a background queue is terminating while we're select()ing
            # or read()ing or wait()ing, in order to give our SIGCHLD handler a chance to run.
            # This doesn't really have to concern us here, carry on.
            if err.args[0] != errno.EINTR:
                raise

    proc.stdout.close()
    proc.stderr.close()

    if log or proc.returncode != 0:
        logent = LogEntry(host=Host.objects.get_current(), user=pwd.getpwuid(os.getuid()).pw_name,
                          starttime=starttime, command=args[0][:250])
        logent.endtime = datetime.now()
        logent.exitcode = proc.returncode
        logent.text = '\n'.join(out)
        logent.save()

        if proc.returncode == 0:
            logging.debug(logent.text)
        else:
            logging.error(logent.text)

    if fail_on_err and proc.returncode != 0:
        raise SystemError("%s failed: %s" % (cmdline, procerr))

    if return_out_err:
        return proc.returncode, procout, procerr
    return proc.returncode


def service_command(service, command="reload"):
    """ Restart a service, preferrably by telling systemd(1) to do so via its
        DBus API, and if that is not available, by executing '/usr/sbin/service $service restart'
        or '/etc/init.d/$service restart'.
    """

    if command not in ("start", "stop", "reload", "restart"):
        raise ValueError("invalid command %s" % command)

    if is_executable_installed('systemctl'):
        if command == 'reload':
            command = 'reload-or-restart'  # Also handles units which cannot be reloaded.
        logging.info('service_command({}): invoking `systemctl {} {}`'.format(service, command,
                                                                              service))
        invoke(['systemctl', command, service])
        return

    if is_executable_installed('service'):
        logging.info("service_command(%s): invoking `service %s %s`" % (service, service, command))
        invoke(['service', service, command])
        return

    initscript = os.path.join("/etc/init.d", service)
    if os.path.exists(initscript):
        logging.info("service_command(%s): invoking `%s %s`" % (service, initscript, command))
        invoke([initscript, command])
        return

    raise SystemError("service_command(%s): don't know how (no systemd, no service installed, no "
                      "init script found)" % service)
