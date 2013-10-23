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

from rpcd.handlers import ModelHandler
from rpcd.handlers import ProxyModelHandler

from mdraid.models import Array
from volumes.rpcapi import AbstractBlockVolumeHandler

class ArrayHandler(AbstractBlockVolumeHandler):
    model = Array

    def _override_get(self, obj, data):
        data["member_set"] = [
            self._get_handler_instance(member.__class__)._idobj(member)
            for member in obj.member_set.all()
            ]
        return data

    def get_raid_params(self, id):
        return Array.objects.get(id=id).raid_params

RPCD_HANDLERS = [ArrayHandler]
