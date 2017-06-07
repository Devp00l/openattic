/**
 *
 * @source: http://bitbucket.org/openattic/openattic
 *
 * @licstart  The following is the entire license notice for the
 *  JavaScript code in this page.
 *
 * Copyright (c) 2017 SUSE LLC
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

var app = angular.module("openattic.cephRgw");
/**
 * Validate the quota maximum size, e.g. 1096, 1K, 30M.
 */
app.directive("cephRgwQuotaMaxSizeValidate", function ($filter) {
  return {
    // Restrict to an attribute type.
    restrict: "A",
    // Element must have ng-model attribute.
    require: "ngModel",
    // scope = The parent scope
    // elem  = The element the directive is on
    // attrs = A dictionary of attributes on the element
    // ctrl  = The controller for ngModel
    link: function (scope, elem, attrs, ctrl) {
      ctrl.$validators.cephRgwQuotaMaxSizeValidate = function (value) {
        if (ctrl.$isEmpty(value)) {
          return true;
        }
        var m = RegExp("^(\\d+)\\s*(B|K(B|iB)?|M(B|iB)?|G(B|iB)?|T(B|iB)?)?$").exec(value);
        if (m === null) {
          return false;
        }
        var bytes = $filter("toBytes")(value);
        return bytes >= 1024;
      };
    }
  };
});
