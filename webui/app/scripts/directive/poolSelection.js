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
app.directive("poolSelection", function () {
  return {
    restrict: "E",
    scope: {
      pool: "=",
      validation: "=",
      megs: "=",
      submitted: "=",
      wizard: "="
    },
    templateUrl: "templates/poolSelection.html",
    controller: function ($scope, poolsService, toasty) {
      $scope.waitingMsg = "Retrieving pool list...";
      poolsService.query()
        .$promise
        .then(function (res) {
          $scope.pools = res;
          $scope.waitingMsg = "-- Select a pool --";
        }, function (error) {
          console.log("An error occurred", error);
          toasty.error({
            title: "Pool list couldn't be loaded",
            msg: "Server failure."
          });
          $scope.waitingMsg = "Error: List couldn't be loaded!";
          $scope.validation.$setValidity("loading", false);
        });
      $scope.selPoolUsedPercent = 0;
      $scope.$watch("pool", function (pool) {
        if (pool) {
          $scope.selPoolUsedPercent = parseFloat(pool.usage.used_pcnt).toFixed(2);
        }
      });
    }
  };
});
