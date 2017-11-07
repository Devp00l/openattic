/**
 *
 * @source: http://bitbucket.org/openattic/openattic
 *
 * @licstart  The following is the entire license notice for the
 *  JavaScript code in this page.
 *
 * Copyright (C) 2011-2016, it-novum GmbH <community@openattic.org>
 *
 *
 * The JavaScript code in this page is free software: you can
 * redistribute it and/or modify it under the terms of the GNU
 * General Public License as published by the Free Software
 * Foundation; version 2.
 *
 * This package is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * As additional permission under GNU GPL version 2 section 3, you
 * may distribute non-source (e.g., minimized or compacted) forms of
 * that code without the copy of the GNU GPL normally required by
 * section 1, provided you include this license notice and a URL
 * through which recipients can access the Corresponding Source.
 *
 * @licend  The above is the entire license notice
 * for the JavaScript code in this page.
 *
 */
"use strict";

import "../ceph-cluster/ceph-cluster.module";
import cephPoolsAdd from "./ceph-pools-add/ceph-pools-add.component";
import cephPoolsDeleteModal from "./ceph-pools-delete-modal/ceph-pools-delete-modal.component";
import cephPoolsList from "./ceph-pools-list/ceph-pools-list.component";

angular.module("openattic.cephPools", [
  "openattic.cephCluster",
  "openattic.cephErasureCodeProfiles",
  "openattic.cephOsd"
])
  .component("cephPoolsAdd", cephPoolsAdd)
  .component("cephPoolsDeleteModal", cephPoolsDeleteModal)
  .component("cephPoolsList", cephPoolsList);

require("./ceph-pools.route");
require("./shared/ceph-pools.service");