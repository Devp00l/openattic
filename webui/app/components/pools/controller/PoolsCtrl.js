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

var app = angular.module("openattic");
app.controller("PoolsCtrl", function ($scope, $state, PoolService, tabViewService) {
  $scope.data = {};

  $scope.filterConfig = {
    page: 0,
    entries: null,
    search: "",
    sortfield: null,
    sortorder: null
  };

  $scope.selection = {};

  $scope.tabData = {
    active: 0,
    tabs: {
      status: {
        show: "selection.item",
        state: "pools.detail.status",
        class: "tc_status_tab",
        name: "Status"
      },
      storage: {
        show: "selection.item",
        state: "pools.detail.storage",
        class: "tc_storage_tab",
        name: "Storage"
      },
      cephPool: {
        show: "selection.item.type.app_label === 'ceph'",
        state: "pools.detail.cephpool",
        class: "tc_ceph_pool_tab",
        name: "Ceph Pool"
      }
    }
  };
  $scope.tabConfig = {
    type: "pool",
    linkedBy: "id",
    jumpTo: "more"
  };
  tabViewService.setScope($scope);
  $scope.changeTab = tabViewService.changeTab;

  $scope.$watch("filterConfig", function (newVal) {
    if (newVal.entries === null) {
      return;
    }
    PoolService.filter({
      page: $scope.filterConfig.page + 1,
      pageSize: $scope.filterConfig.entries,
      search: $scope.filterConfig.search,
      ordering: ($scope.filterConfig.sortorder === "ASC" ? "" : "-") + $scope.filterConfig.sortfield
    })
        .$promise
        .then(function (res) {
          $scope.data = res;
        })
        .catch(function (error) {
          console.log("An error occurred", error);
        });
  }, true);

  $scope.$watch("selection.item", function (selitem) {
    if (selitem) {
      if ($state.current.name === "pools" ||
          $state.current.name === "pools.detail.cephpool" && selitem.type.app_label !== "ceph") {
        $scope.changeTab("pools.detail.status");
      } else {
        $scope.changeTab($state.current.name);
      }
    } else {
      $state.go("pools");
    }
  });

  $scope.$watchCollection("selection.item", function (item) {
    $scope.hasSelection = Boolean(item);
  });

  $scope.addAction = function () {
    console.log(["addAction", arguments]);
  };

  $scope.deleteAction = function () {
    console.log(["deleteAction", arguments]);
  };
});
