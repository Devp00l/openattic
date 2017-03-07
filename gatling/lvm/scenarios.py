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

from unittest import SkipTest

from requests.exceptions import HTTPError

from testcase import GatlingTestCase


class LvTestScenario(GatlingTestCase):
    @classmethod
    def setUpClass(cls):
        super(LvTestScenario, cls).setUpClass()
        cls.require_enabled("lvm")
        cls.require_config("lvm", "vg")
        cls.vg = cls._get_vg_by_name(cls.conf.get("lvm", "vg"))

    @classmethod
    def setUp(self):
        self.delete_old_existing_gatling_volumes()

    @classmethod
    def _get_vg_by_name(cls, vg_name):
        try:
            res = cls.send_request("GET", "pools", search_param=("name={}".format(vg_name)))
        except HTTPError as e:
            raise SkipTest(e.message)

        if res["count"] != 1:
            raise SkipTest("Failed to request VG <{}>. The REST API returned no or more "
                           "than one object(s). But only one is expected.".format(vg_name))

        vg = res["response"][0]

        if ("name" and "type") not in vg or \
                vg["name"] != vg_name or \
                vg["type"]["app_label"] != "lvm" or \
                vg["type"]["model"] != "volumegroup":
            raise SkipTest("VG <{}> not found".format(vg_name))

        return vg

    def _get_pool(self):
        return self.vg

    @property
    def error_messages(self):
        vg_name = self.remote_vg["name"] if hasattr(self, "remote_vg") else self.vg["name"]
        return {
            "test_create_not_enough_space": "Volume Group {} has insufficient free space."
                .format(vg_name),
            "test_create_0mb": "Volumes need to be at least 100MB in size.",
            "test_resize_0mb": "Volumes need to be at least 100MB in size.",
            "test_shrink": "Volumes need to be at least 100MB in size."
        }


class RemoteLvTestScenario(LvTestScenario):
    @classmethod
    def setUpClass(cls):
        super(RemoteLvTestScenario, cls).setUpClass()
        cls.require_enabled("lvm:remote")
        cls.require_config("lvm:remote", "vg")
        cls.remote_vg = cls._get_vg_by_name(cls.conf.get("lvm:remote", "vg"))

    def _get_remote_pool(self):
        return self.remote_vg
