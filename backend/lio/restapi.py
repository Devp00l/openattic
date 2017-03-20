
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

import django_filters
from ifconfig.models import Host

from rest_framework import serializers

from rest import relations
from rest.utilities import DeleteCreateMixin
from rest.restapi import NoCacheModelViewSet

from volumes.models import StorageObject
from lio.models import HostACL, Initiator

from rest.multinode.handlers import RequestHandlers


class HostACLSerializer(DeleteCreateMixin, serializers.HyperlinkedModelSerializer):
    """ Serializer for a HostACL. """
    url = serializers.HyperlinkedIdentityField(view_name="lun-detail")
    volume = relations.HyperlinkedRelatedField(view_name="volume-detail",
                                               source="volume.storageobj",
                                               queryset=StorageObject.objects.all())
    host = relations.HyperlinkedRelatedField(view_name="host-detail", queryset=Host.objects.all())

    class Meta:
        model = HostACL
        # TODO: add portals
        fields = ('url', 'id', 'host', 'volume', 'lun_id')

    def update_validated_data(self, attrs):
        if "volume.storageobj" in attrs:
            attrs["volume"] = attrs["volume.storageobj"].blockvolume_or_none
            del attrs["volume.storageobj"]
        else:
            attrs["volume"] = attrs["volume"]["storageobj"].blockvolume_or_none
        return attrs


class HostACLFilter(django_filters.FilterSet):
    volume = django_filters.NumberFilter(name="volume__storageobj__id")

    class Meta:
        model = HostACL
        fields = ['volume', 'host']


class HostACLViewSet(NoCacheModelViewSet):
    queryset = HostACL.objects.all()
    serializer_class = HostACLSerializer
    filter_class = HostACLFilter


class HostACLProxyViewSet(RequestHandlers, HostACLViewSet):
    queryset = HostACL.all_objects.all()
    api_prefix = 'luns'
    host_filter = 'volume__storageobj__host'
    model = HostACL


class InitiatorSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for a Initiator. """
    url = serializers.HyperlinkedIdentityField(view_name="initiator-detail")
    host = relations.HyperlinkedRelatedField(view_name="host-detail", queryset=Host.objects.all())

    class Meta:
        model = Initiator
        fields = ('url', 'id', 'host', 'wwn', 'type')


class InitiatorViewSet(NoCacheModelViewSet):
    queryset = Initiator.objects.all()
    serializer_class = InitiatorSerializer
    filter_fields = ('host', 'wwn', 'type')


RESTAPI_VIEWSETS = [
    ('luns', HostACLProxyViewSet, 'lun'),
    ('initiators', InitiatorViewSet, 'initiator')
]
