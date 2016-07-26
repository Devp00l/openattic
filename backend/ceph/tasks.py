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
import logging

from nodb.models import NodbManager
from taskqueue.models import task
from ceph import librados

logger = logging.getLogger(__name__)

@task
def set_pgs(fsid, pool_id, pgs):
    from ceph.models import CephCluster, CephPool

    cluster = CephCluster.objects.get(fsid=fsid)
    cluster.cluster = cluster
    NodbManager.set_nodb_context(cluster)
    pool = CephPool.objects.get(id=pool_id)
    api = librados.MonApi(cluster.rados_client)

    api.osd_pool_set(pool.name, 'pg_num', pgs)
    api.osd_pool_set(pool.name, 'pgp_num', pgs)
    return track_pg_creation(fsid, pool_id, pool.pg_num, pgs)


@task
def track_pg_creation(fsid, pool_id, pg_count_before, pg_count_after):
    from ceph.models import CephCluster, CephPg, CephPool

    cluster = CephCluster.objects.get(fsid=fsid)
    cluster.cluster = cluster
    NodbManager.set_nodb_context(cluster)
    pool = CephPool.objects.get(id=pool_id)
    pgs = CephPg.objects.filter(pool_name__exact=pool.name)

    def pg_in_state(state):
        return len([pg for pg in pgs if state in pg.state])

    active = pg_in_state('active')
    creating = pg_in_state('creating')

    logger.info('before={} after={} all={} active={} creating={}'.format(pg_count_after, pg_count_after,
                len(pgs), active, creating))

    if active >= pg_count_after:
        return
    else:
        return track_pg_creation(fsid, pool_id, pg_count_before, pg_count_after)

