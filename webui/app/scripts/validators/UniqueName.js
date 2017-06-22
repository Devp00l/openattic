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
app.directive("uniquename", function ($timeout, cephErasureCodeProfilesService, cephPoolsService, cephRbdService,
    usersService) {
  return {
    restrict: "A",
    require: "ngModel",
    link: function (scope, elem, attrs, ctrl) {
      var stopTimeout;
      ctrl.model = attrs.uniquename;
      ctrl.field = attrs.name;

      return scope.$watch(function () {
        return ctrl.$modelValue;
      }, function (modelValue) {
        ctrl.$setValidity("uniquename", true);
        $timeout.cancel(stopTimeout);

        if (modelValue === "" || angular.isUndefined(modelValue)) {
          return;
        }
        stopTimeout = $timeout(function () {
          var obj;
          var query = {};
          switch (ctrl.model) {
            case "user":
              obj = {
                model: usersService,
                current: scope.user.id,
                attribute: "id"
              };
              break;
            case "rbd":
              query.clusterId = scope.data.cluster.fsid;
              obj = {
                model: cephRbdService,
                current: null, // Has no renaming feature.
                attribute: "name"
              };
              break;
            case "ceph-pool":
              query.fsid = scope.data.cluster.fsid;
              obj = {
                model: cephPoolsService,
                current: null, // Has no renaming feature.
                attribute: "name"
              };
              break;
            case "erasure-code-profiles":
              query.fsid = scope.cluster.fsid;
              obj = {
                model: cephErasureCodeProfilesService,
                current: null, // Has no renaming feature.
                attribute: "name"
              };
              break;

            default:
              Notification.warning({
                title: "Service not implemened",
                msg: "Please add the Service to 'UniqueName.js'."
              });
              return;
          }
          var resCheck = function (res) {
            if (res.length !== 0 && obj.current) {
              ctrl.$setValidity("uniquename", res[0][obj.attribute] === obj.current);
            } else {
              ctrl.$setValidity("uniquename", res.length === 0);
            }
          };
          query[ctrl.field] = modelValue;
          obj.model.query(query)
              .$promise
              .then(resCheck);
        }, 300);
      });
    }
  };
});
