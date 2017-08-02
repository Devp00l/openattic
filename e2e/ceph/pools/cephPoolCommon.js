'use strict';

var cephPoolCommons = function(){
  var helpers = require('../../common.js');
  this.cephPools = element(by.css('.tc_menuitem_ceph_pools'));

  this.clusters = helpers.configs.cephCluster;
  this.clusterCount = Object.keys(this.clusters).length;
  this.clusterSelect = element(by.model('registry.selectedCluster'));

  this.addButton = element(by.css('oadatatable .tc_add_btn'));
  this.statusTab = element(by.css('.tc_statusTab'));
  this.statisticsTab = element(by.className('tc_statisticsTab'));
  //this.cacheTieringTab = element(by.css('.tc_cacheTieringTab'));

  // Describes the attributes seen in the detail tab.
  this.detailAttributes = [
    'ID',
    'Placement Groups',
    'Type',
    'Flags',
    'Last change'
  ];

  // Description of headers in the table.
  this.tableHeaders = [
    {
      name: 'Name',
      displayed: true
    },
    {
      name: 'ID',
      displayed: true
    },
    {
      name: 'Used',
      displayed: true
    },
    {
      name: 'Placement groups',
      displayed: true
    },
    {
      name: 'Replica size',
      displayed: true
    },
    {
      name: 'Erasure code profile',
      displayed: true
    },
    {
      name: 'Type',
      displayed: true
    },
    {
      name: 'Crush ruleset',
      displayed: true
    }
  ];

  // Describes the form elements.
  this.formElements = {
    name: {
      name: 'Name',
      byClass: element(by.className('tc_pool_name')),
      byModel: element(by.model('pool.name')),
      type: 'text',
      displayed: true,
      items: {
        required: element(by.className('tc_nameRequired')),
        uniqueName: element(by.className('tc_noUniqueName')),
        validName: element(by.className('tc_noValidName'))
      }
    },
    /* Only for multi cluster systems
    cluster: {
      name: 'Cluster',
      byClass: element.all(by.className('tc_cluster_selection')),
      byModel: element(by.model('data.cluster')),
      displayed: false,
      type: 'select',
      items: {
        clusterSelection: element(by.className('tc_clusterOption')),
        helpCluster: element(by.className('tc_clusterRequired')),
        helpLoad: element(by.className('tc_clusterLoading'))
      }
    },
    */
    types: {
      name: 'Pool type',
      byClass: element.all(by.className('tc_poolTypes_selection')),
      byModel: element(by.model('pool.type')),
      displayed: true,
      type: 'select',
      items: {
        typeSelection: element(by.className('tc_poolTypesOption')),
        required: element(by.className('tc_typeRequired'))
      }
    },
    pgnum: {
      name: 'Placement groups',
      byClass: element(by.className('tc_pool_pgNum')),
      byModel: element(by.model('pool.pg_num')),
      displayed: false,
      displayedIf: 'replicated', // and 'erasure'
      type: 'number',
      items: {
        helpPgnum: element(by.className('tc_pgNumRequired'))
      }
    },
    replicatedSize: {
      name: 'Replicated size',
      byClass: element(by.className('tc_pool_size')),
      byModel: element(by.model('pool.size')),
      type: 'number',
      displayed: false,
      presented: false,
      displayedIf: 'replicated',
      items: {
        helpSize: element(by.className('tc-applied-rule-set')),
        helpSize: element(by.className('tc-size-out-of-range')),
        helpSize: element(by.className('tc_sizeRequired'))
      }
    },
    crushRules: {
      name: 'Crush ruleset',
      byClass: element(by.className('tc_crushSet_selection')),
      displayed: false,
      displayedIf: 'replicated', // and 'erasure'
      type: 'select',
      items: {
        crushSelection: element(by.className('tc_crushSetOption')),
        helpRuleReq: element(by.className('tc_crushSetRequired'))
      }
    },
    erasureProfiles: {
      name: 'Erasure code profile',
      byClass: element.all(by.className('tc_erasureProfiles_selection')),
      byModel: element(by.model('pool.erasure.profile')),
      type: 'select',
      displayed: false,
      displayedIf: 'erasure',
      items: {
        erasureSelection: element(by.className('tc_erasureProfilesOption')),
        erasureRequired: element(by.className('tc_erasureRequired'))
      },
    },
    ecOverwriteFlag: {
      name: 'EC Overwrites',
      byClass: element.all(by.id('ec-overwrites')),
      byModel: element(by.model('data.flags.ec_overwrites')),
      type: 'checkbox',
      displayed: false,
      presented: false,
      displayedIf: 'erasure',
    },
    backButton: {
      name: 'Back',
      byClass: element(by.className('tc_backButton')),
      type: 'button',
      displayed: true
    },
    createButton: {
      name: 'Create',
      byClass: element(by.className('tc_submitButton')),
      type: 'button',
      displayed: true
    }
  };

  this.formLabels = {
    header: {
      text: 'Create Ceph pool:',
      where: 'header',
      byClass: element(by.className('tc_formHeadline'))
    }
  };

  this.isListInSelectBox = function(e){
    if(e.displayedIf === 'replicated'){
      self.formElements.types.byModel.sendKeys('Replicated');
      self.formElements.name.byModel.click();
    }else if(e.displayedIf === 'erasure'){
      self.formElements.types.byModel.sendKeys('Erasure');
      self.formElements.name.byModel.click();
    }
    e.byClass.click();
    var listEntries = e.byClass.all(by.css('option'));

    expect(listEntries.count()).toBeGreaterThan(1);
  };

  this.checkCheckboxToBe = function(e, bool){
    e.getAttribute('checked').then(function(value){
      if(Boolean(value) !== bool){
        e.click();
      }
    });
  };

  /*
   Selects cluster if a selection is available in the listing.
   */
  this.selectCluster = function(cluster){
    if(self.clusterCount > 1){
      self.clusterSelect.sendKeys(cluster.name);
      expect(self.clusterSelect.getText()).toContain(cluster.name);
    }
  };

  var self = this;
};

module.exports = cephPoolCommons;
