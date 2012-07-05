# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; replace-tabs on;

"""
 *  Copyright (C) 2011-2012, it-novum GmbH <community@open-attic.org>
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

from django.dispatch import Signal

pre_install     = Signal()
post_install    = Signal()

pre_uninstall   = Signal()
post_uninstall  = Signal()

pre_shrink      = Signal(providing_args=["jid"])
post_shrink     = Signal(providing_args=["jid"])
pre_grow        = Signal(providing_args=["jid"])
post_grow       = Signal(providing_args=["jid"])

pre_format      = Signal()
post_format     = Signal()

pre_mount       = Signal(providing_args=["mountpoint"])
post_mount      = Signal(providing_args=["mountpoint"])
pre_unmount     = Signal(providing_args=["mountpoint"])
post_unmount    = Signal(providing_args=["mountpoint"])


# Signals for oavgmanager.
# oavgmanager start: send pre_activate, update host field, send activate, mount volumes, send post_activate
# oavgmanager stop:  send pre_deactivate, unmount volumes, send deactivate, update host field, send post_deactivate
pre_activate    = Signal(providing_args=["host"])
activate        = Signal()
post_activate   = Signal()
pre_deactivate  = Signal()
deactivate      = Signal()
post_deactivate = Signal()

