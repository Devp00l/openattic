# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; replace-tabs on;

"""
 *  Copyright (C) 2011-2014, it-novum GmbH <community@open-attic.org>
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

from rpcd.handlers import ProxyModelHandler

from zfs.models import Zpool, Zfs
from volumes.rpcapi import AbstractVolumePoolHandler, AbstractFileSystemVolumeHandler

class ZpoolHandler(AbstractVolumePoolHandler):
    model = Zpool

class ZpoolProxy(ProxyModelHandler, ZpoolHandler):
    pass

class ZfsHandler(AbstractFileSystemVolumeHandler):
    model = Zfs

class ZfsProxy(ProxyModelHandler, ZfsHandler):
    pass

RPCD_HANDLERS = [ZpoolProxy, ZfsProxy]
