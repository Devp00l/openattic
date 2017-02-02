var helpers = require('../common.js');

describe('should test the ceph osd panel', function(){
  var cephOSDs = element(by.css('.tc_menuitem_ceph_pools'));

  beforeAll(function(){
    helpers.login();
    cephOSDs.click();
  });

  var tableHeaders = [
    'Name',
    'Hostname',
    'Status',
    'Crush Weight'
  ];

  it('should check the ceph OSDs url', function(){
    expect(browser.getCurrentUrl()).toContain('/ceph/osds');
  });

  it('should display the ceph OSD table after selecting a cluster', function(){
    expect(element(by.css('.tc_cephOsdTable')).isDisplayed()).toBe(true);
  });

  it('should display the following table headers', function(){
    for(tableHeader in tableHeaders){
      expect(element(by.cssContainingText('th', tableHeaders[tableHeader])).isDisplayed()).toBe(true);
      //check: console.log(tableHeaders[tableHeader]);
    }
  });

  it('should have at least one ceph osd table entry', function(){
    expect(element.all(by.binding('row.name')).count()).toBeGreaterThan(0);
  });

  /* TODO: Update the tests to use the configuration
   it('should select a cluster', function(){
   selectCluster.click();
   });

  it('should still have the cluster selected and display OSDs when switching between panels', function(){
    element(by.css('ul .tc_menuitem_pools > a')).click();
    expect(browser.getCurrentUrl()).toContain('/#/pools');
    cephMenu.click();
    cephOSDs.click();
    expect(browser.getCurrentUrl()).toContain('/ceph/osds');
    expect(element(by.id('cluster-selection')).getText()).toContain('ceph (');
    expect(element.all(by.binding('row.name')).count()).toBeGreaterThan(0);
  });
  */

  afterAll(function(){
    console.log('ceph_osds -> ceph_osds.e2e.js');
  });

});

