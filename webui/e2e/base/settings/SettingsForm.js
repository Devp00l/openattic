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

var SettingsForm = function () {

  this.saltApiHost = element(by.model("$ctrl.model.deepsea.host"));
  this.saltApiPort = element(by.model("$ctrl.model.deepsea.port"));
  this.saltApiEauth = element(by.model("$ctrl.model.deepsea.eauth"));
  this.saltApiUsername = element(by.model("$ctrl.model.deepsea.username"));
  this.saltApiSharedSecret = element(by.model("$ctrl.model.deepsea.shared_secret"));
  this.saltApiConnectionSuccess = element(by.css(".tc_deepseaConnectionSuccess"));
  this.saltApiConnectionFail = element(by.css(".tc_deepseaConnectionFail"));

  this.rgwManagedByDeepSea = element(by.model("$ctrl.model.rgw.managed_by_deepsea"));
  this.rgwHost = element(by.model("$ctrl.model.rgw.host"));
  this.rgwPort = element(by.model("$ctrl.model.rgw.port"));
  this.rgwAccessKey = element(by.model("$ctrl.model.rgw.access_key"));
  this.rgwSecretKey = element(by.model("$ctrl.model.rgw.secret_key"));
  this.rgwAdminUser = element(by.model("$ctrl.model.rgw.user_id"));
  this.rgwAdminResourcePath = element(by.model("$ctrl.model.rgw.admin_path"));
  this.rgwUseSSL = element(by.model("$ctrl.model.rgw.use_ssl"));
  this.rgwConnectionSuccess = element(by.css(".tc_rgwConnectionSuccess"));
  this.rgwConnectionFail = element(by.css(".tc_rgwConnectionFail"));

  this.grafanaHost = element(by.model("$ctrl.model.grafana.host"));
  this.grafanaPort = element(by.model("$ctrl.model.grafana.port"));
  this.grafanaUsername = element(by.model("$ctrl.model.grafana.username"));
  this.grafanaPassword = element(by.model("$ctrl.model.grafana.password"));
  this.grafanaUseSSL = element(by.model("$ctrl.model.grafana.use_ssl"));
  this.grafanaConnectionSuccess = element(by.css(".tc_grafanaConnectionSuccess"));
  this.grafanaConnectionFail = element(by.css(".tc_grafanaConnectionFail"));

  this.cephClusterConfigFile = element(by.model("cephCluster.config_file_path"));
  this.cephClusterKeyringFile = element(by.model("cephCluster.keyring_file_path"));
  this.cephClusterKeyringFileRequired = element(by.css(".tc_cephClusterKeyringFilePathRequired"));
  this.cephClusterKeyringUser = element(by.model("cephCluster.keyring_user"));
  this.cephClusterKeyringUserRequired = element(by.css(".tc_cephClusterKeyringUserRequired"));
  this.cephClusterConnectionSuccess = element(by.css(".tc_cephConnectionSuccess"));
  this.cephClusterConnectionFail = element(by.css(".tc_cephConnectionFail"));

  this.submitButton = element(by.css(".tc_submitButton"));

  this.selectEauth = function (text) {
    element(by.model("$ctrl.model.deepsea.eauth")).all(by.cssContainingText("option", text)).click();
  };

  this.checkManagedByDeepSea = function (value) {
    var checkbox = element(by.model("$ctrl.model.rgw.managed_by_deepsea"));
    checkbox.isSelected().then(function (selected) {
      if (selected !== value) {
        checkbox.click();
      }
    });
  };

  this.checkRgwUseSSL = function (value) {
    var checkbox = element(by.model("$ctrl.model.rgw.use_ssl"));
    checkbox.isSelected().then(function (selected) {
      if (selected !== value) {
        checkbox.click();
      }
    });
  };

  this.checkGrafanaUseSSL = function (value) {
    var checkbox = element(by.model("$ctrl.model.grafana.use_ssl"));
    checkbox.isSelected().then(function (selected) {
      if (selected !== value) {
        checkbox.click();
      }
    });
  };

};
module.exports = SettingsForm;
