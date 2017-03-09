# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; replace-tabs on;

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

from rest_framework import serializers

from ifconfig import models
from rest import relations
from rest.multinode.handlers import RequestHandlers
from rest.utilities import mk_method_field_params, NoCacheModelViewSet


class IPAddressSerializer(serializers.ModelSerializer):
    device = relations.HyperlinkedRelatedField(view_name='netdevice-detail', many=False,
                                               read_only=False,
                                               queryset=models.NetDevice.objects.all())

    class Meta:
        model = models.IPAddress


class NetDeviceSerializer(serializers.HyperlinkedModelSerializer):
    ipaddress_set = relations.HyperlinkedRelatedField(view_name='ipaddress-detail', many=True,
                                                      read_only=True)
    host = relations.HyperlinkedRelatedField(view_name='host-detail', many=False, read_only=False,
                                             queryset=models.Host.objects.all())

    class Meta:
        model = models.NetDevice


class HostSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='host-detail')
    netdevice_set = relations.HyperlinkedRelatedField(view_name='netdevice-detail', many=True,
                                                      read_only=True)
    hostgroup_set = relations.HyperlinkedRelatedField(view_name='hostgroup-detail', many=True,
                                                      read_only=True)
    primary_ip_address = serializers.SerializerMethodField(*mk_method_field_params(
        'primary_ip_address'))
    installed_apps = serializers.SerializerMethodField(*mk_method_field_params('installed_apps'))
    oa_version = serializers.SerializerMethodField(*mk_method_field_params('oa_version'))

    class Meta:
        model = models.Host
        fields = ('id', 'name', 'url', 'netdevice_set', 'hostgroup_set', 'primary_ip_address',
                  'installed_apps', 'oa_version')

    def get_primary_ip_address(self, obj):
        host = models.Host.objects.get(id=obj.id)

        try:
            ip = host.get_primary_ip_address()
        except models.IPAddress.DoesNotExist:
            return None
        else:
            serializer = IPAddressSerializer(ip, many=False, context=self.context)
            return serializer.data

    def get_installed_apps(self, obj):
        return obj.installed_apps

    def get_oa_version(self, obj):
        return obj.oa_version


class HostGroupSerializer(serializers.ModelSerializer):
    hosts = relations.HyperlinkedRelatedField(view_name='host-detail', many=True, read_only=True)

    class Meta:
        model = models.HostGroup


class IPAddressViewSet(NoCacheModelViewSet):
    queryset = models.IPAddress.all_objects.all()
    serializer_class = IPAddressSerializer


class IPAddressProxyViewSet(RequestHandlers, IPAddressViewSet):
    api_prefix = "ipaddresses"
    model = models.IPAddress
    host_filter = "device"


class NetDeviceViewSet(NoCacheModelViewSet):
    queryset = models.NetDevice.all_objects.all()
    serializer_class = NetDeviceSerializer


class NetDeviceProxyViewSet(RequestHandlers, NetDeviceViewSet):
    api_prefix = 'netdevices'
    model = models.NetDevice


class HostViewSet(NoCacheModelViewSet):
    queryset = models.Host.objects.all()
    serializer_class = HostSerializer
    filter_fields = ('name',)
    search_fields = ('name',)


class HostProxyViewSet(RequestHandlers, HostViewSet):
    api_prefix = 'hosts'
    model = models.Host


class HostGroupViewSet(NoCacheModelViewSet):
    queryset = models.HostGroup.objects.all()
    serializer_class = HostGroupSerializer


RESTAPI_VIEWSETS = [
    ('hosts', HostProxyViewSet, 'host'),
    ('hostgroups', HostGroupViewSet),
    ('netdevices', NetDeviceProxyViewSet, 'netdevice'),
    ('ipaddresses', IPAddressProxyViewSet, 'ipaddress'),
]
