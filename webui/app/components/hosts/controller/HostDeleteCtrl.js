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

var app = angular.module("openattic.hosts");
app.controller("HostDeleteCtrl", function ($scope, $filter, HostService, $uibModalInstance, hosts, toasty, $q) {
  $scope.hosts = hosts;
  $scope.input = {
    enteredName: "",
    pattern: "yes"
  };

  /**
   * Deletes all hosts in the selection.
   */
  $scope.delete = function () {
    var hosts = $scope.hosts;
    var requests = [];
    hosts.forEach(function (host) {
      var deferred = $q.defer();
      HostService.delete({id: host.id}, deferred.resolve, deferred.reject);
      requests.push(deferred.promise);
    });
    $q.all(requests).then(function () {
      $uibModalInstance.close("deleted");
    }, function (error) {
      toasty.error({
        title: "Error " + error.status + " when deleting host" + hosts.length === 1 ? "" : "s",
        msg: $filter("json")(error.data)
      });
      $uibModalInstance.close("deleted");
      throw error;
    });
  };

  $scope.cancel = function () {
    $uibModalInstance.dismiss("cancel");
    toasty.warning({
      title: "Cancelled delete host",
      msg: "Cancelled host delete."
    });
  };
});
