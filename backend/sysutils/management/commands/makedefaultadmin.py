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

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'If there is no other SuperUser, creates an openattic/openattic default user.'

    def handle(self, **options):
        if User.objects.filter(is_superuser=True).count() == 0:
            oa_username = getattr(settings, "OAUSER")
            admin = User(username=oa_username, is_superuser=True, is_staff=True, is_active=True)
            admin.set_password('openattic')
            admin.save()
            print('Created default user "openattic" with password "openattic".')
        else:
            print('We have an admin already, not creating default user.')
