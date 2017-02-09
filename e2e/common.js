'use strict';

(function(){

  var configs = require('./configs.js');
  var volumesItem = element(by.css('ul .tc_menuitem_volumes > a'));
  var hostsItem = element(by.css('ul .tc_menuitem_hosts > a'));

  //TODO: Remove static item names.
  var snapshotname = 'protractor_test_snap';
  var snapshot = element(by.cssContainingText('tr', snapshotname));

  var clonename = 'protractor_test_clone';
  var clone = element(by.cssContainingText('tr', clonename));

  var hostname = 'protractor_test_host';

  var volumePoolSelect = element(by.model('pool'));

  var helper = {
    configs: configs,

    get_list_element: function(itemName){
      return element(by.cssContainingText('tr', itemName));
    },

    delete_selection: function(){
      element(by.css('.tc_menudropdown')).click();
      element(by.css('.tc_deleteItem > a')).click();
      browser.sleep(400);
      element(by.model('input.enteredName')).sendKeys('yes');
      element(by.id('bot2-Msg1')).click();
      browser.sleep(400);
    },

    search_for: function(query){
      var search = element.all(by.model('filterConfig.search')).first();
      search.clear();
      search.sendKeys(query);
      browser.sleep(helper.configs.sleep);
    },

    login: function(){
      browser.get(configs.url);
      element.all(by.model('username')).sendKeys(configs.username);
      element.all(by.model('password')).sendKeys(configs.password);
      element.all(by.css('input[type="submit"]')).click();

      browser.sleep(configs.sleep);
    },

    create_volume: function(volumename, type, size, poolName){
      var pool;
      size = size == null ? '100MB' : size;

      volumesItem.click();
      element(by.css('oadatatable .tc_add_btn')).click();

      if(!poolName){
        for(var key in configs.pools){
          pool = configs.pools[key];
          poolName = pool.name;
          break;
        }
      }
      element(by.model('result.name')).sendKeys(volumename);
      volumePoolSelect.sendKeys(poolName);
      element(by.id(type)).click();
      element(by.model('data.megs')).sendKeys(size);
      element(by.css('.tc_submitButton')).click();
      browser.sleep(configs.sleep);
      expect(helper.get_list_element(volumename).isDisplayed()).toBe(true);
      return pool;
    },

    delete_volume: function(volume, volumename){
      volumesItem.click();
      browser.sleep(400);
      element(by.css('.tc_entries_dropdown')).click();
      browser.sleep(400);
      element(by.css('.tc_entries_100')).click();
      browser.sleep(400);
      volume.click();
      browser.sleep(400);
      helper.delete_selection();
      volume = helper.get_list_element(volumename);
      expect(volume.isPresent()).toBe(false);
    },

    create_snapshot: function(volume){
      expect(volume.isDisplayed()).toBe(true);
      volume.click();
      browser.sleep(400);
      element(by.css('.tc_snapshotTab')).click();
      browser.sleep(400);
      element(by.css('.tc_snapshotAdd')).click();
      browser.sleep(400);
      element(by.id('snap.name')).clear();
      browser.sleep(400);
      element(by.model('snap.name')).sendKeys(snapshotname);
      browser.sleep(400);
      element(by.css('.tc_submitButton')).click();
    },

    delete_snapshot: function(volume){
      volume.click();
      browser.sleep(400);
      element(by.css('.tc_snapshotTab')).click();
      browser.sleep(400);
      expect(snapshot.isPresent()).toBe(true);
      snapshot.click();
      browser.sleep(400);
      element(by.css('.tc_deleteSnapItem')).click();
      browser.sleep(400);
      element(by.id('bot2-Msg1')).click();
      browser.sleep(400);
    },

    create_snap_clone: function(volume){
      volume.click();
      browser.sleep(400);
      element(by.css('.tc_snapshotTab')).click();
      browser.sleep(400);
      expect(snapshot.isDisplayed()).toBe(true);
      snapshot.click();
      element.all(by.css('.tc_menudropdown')).get(1).click();
      browser.sleep(400);
      element(by.css('.tc_snap_clone')).click();
      browser.sleep(400);
      element(by.model('clone_obj.name')).sendKeys(clonename);
      element(by.id('bot2-Msg1')).click();
      browser.sleep(800);
    },

    delete_snap_clone: function(){
      clone.click();
      browser.sleep(400);
      helper.delete_selection();
    },

    create_host: function(iqn, fc, $hostname){
      element(by.css('ul .tc_menuitem_hosts > a')).click();
      element(by.css('.tc_addHost')).click();
      var name = $hostname ? $hostname : hostname;
      element(by.model('host.name')).sendKeys(name);
      if(iqn){
        element.all(by.model('type.check')).get(0).click();
        element.all(by.model('data[key]')).get(0).click();
        element.all(by.model('newTag.text')).get(0).sendKeys(iqn);
      }
      if(fc){
        element.all(by.model('type.check')).get(1).click();
        element.all(by.model('data[key]')).get(1).click();
        element.all(by.model('newTag.text')).get(0).sendKeys(fc);
      }
      browser.sleep(400);
      element(by.css('.tc_submitButton')).click();
      browser.sleep(400);
      expect(helper.get_list_element(name).isDisplayed()).toBe(true);
    },

    delete_host: function($hostname){
      hostsItem.click();
      var name = $hostname ? $hostname : hostname;
      var host = helper.get_list_element(name);
      host.click();
      helper.delete_selection();
      expect(host.isPresent()).toBe(false);
    },

    check_wizard_titles: function(){
      var wizards = element.all(by.repeater('wizard in wizards'))
        .then(function(wizards){
          wizards[0].element(by.css('.tc_wizardTitle')).evaluate('wizard.title').then(function(title){
            expect(title).toEqual('File Storage');
            //console.log(title);
          });

          wizards[1].element(by.css('.tc_wizardTitle')).evaluate('wizard.title').then(function(vm_title){
            expect(vm_title).toEqual('VM Storage');
            //console.log(vm_title);
          });

          wizards[2].element(by.css('.tc_wizardTitle')).evaluate('wizard.title').then(function(block_title){
            expect(block_title).toEqual('iSCSI/Fibre Channel target');
            //console.log(block_title);
          });
        });
    },

    delete_nfs_share: function(volName, nfsName){
      volumesItem.click();
      var volume = helper.get_list_element(volName);
      expect(browser.getCurrentUrl()).toContain('/openattic/#/volumes');
      expect(volume.isDisplayed()).toBe(true);
      volume.click();
      element(by.css('.tc_nfsShareTab')).click();
      var share = element(by.cssContainingText('td', nfsName));
      expect(share.isDisplayed()).toBe(true);
      share.click();
      element(by.css('.tc_nfsShareDelete')).click();
      element(by.id('bot2-Msg1')).click();
      expect(share.isPresent()).toBe(false);
    },

    delete_cifs_share: function(volName, cifsName){
      volumesItem.click();
      var volume = helper.get_list_element(volName);
      expect(browser.getCurrentUrl()).toContain('/openattic/#/volumes');
      expect(volume.isDisplayed()).toBe(true);
      volume.click();
      element(by.css('.tc_cifsShareTab')).click();
      var share = element(by.cssContainingText('tr', cifsName));
      expect(share.isDisplayed()).toBe(true);
      share.click();
      element.all(by.css('.tc_menudropdown')).get(1).click();
      element(by.css('.tc_cifsShareDelete > a')).click();
      element(by.id('bot2-Msg1')).click();
      expect(share.isPresent()).toBe(false);
    },

    delete_fc_share: function(volName, hostname){
      volumesItem.click();
      var volume = helper.get_list_element(volName);
      expect(volume.isPresent()).toBe(true);
      volume.click();
      element(by.css('.tc_iscsi_fcTab')).click();
      var share = helper.get_list_element(hostname);
      share.click();
      element(by.css('.tc_lunDelete')).click();
      element(by.id('bot2-Msg1')).click();
      expect(share.isPresent()).toBe(false);
    }
  };
  module.exports = helper;
}());
