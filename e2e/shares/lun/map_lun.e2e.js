var helpers = require('../../common.js');

describe('Should map a LUN to an host', function(){

  var volumesItem = element.all(by.css('ul .tc_menuitem')).get(3);
  var hostsItem = element.all(by.css('ul .tc_menuitem')).get(4);

  var hostSelect = element(by.model('share.host'));
  var hostname = "protractor_test_host";
  var host = element(by.cssContainingText('tr', hostname));

  var volumename = "protractor_test_volume";
  var volume = element(by.cssContainingText('tr', volumename));

  var iscsiShareTab = element(by.css('.tc_iscsi_fcTab'));

  beforeAll(function(){
    helpers.login();
    helpers.create_host();
    helpers.create_volume("lun");
  });

  var iqn = "iqn.1991-05.com.microsoft:protractor_test_host";

  it('should add the iqn as attribute of the host', function(){
    hostsItem.click();
    browser.sleep(400);
    expect(host.isPresent()).toBe(true);
    host.click();
    browser.sleep(400);
    element(by.model('data.iscsiInis')).click();
    element.all(by.model('newTag.text')).get(1).sendKeys(iqn);
    browser.sleep(400);
    //get out of the iqn input field in order to save entered iqn
    host.click();
  });

  it('should configure the lun', function(){
    volumesItem.click();
    browser.sleep(400);
    element.all(by.css('.tc_entries_dropdown')).get(0).click();
    element.all(by.css('.tc_entries_100')).get(0).click();
    browser.sleep(400);
    expect(volume.isPresent()).toBe(true);
    volume.click();
    browser.sleep(400);
    iscsiShareTab.click();
    browser.sleep(400);
    element(by.css('.tc_lunAdd')).click();
    hostSelect.element(by.cssContainingText('option', hostname)).click();
    element(by.css('.tc_submitButton')).click();
  });

  it('should display the lun', function(){
    volumesItem.click();
    browser.sleep(400);
    element.all(by.css('.tc_entries_dropdown')).get(0).click();
    element.all(by.css('.tc_entries_100')).get(0).click();
    browser.sleep(400);
    expect(volume.isPresent()).toBe(true);
    volume.click();
    browser.sleep(400);
    iscsiShareTab.click();
    browser.sleep(400);
    expect(element(by.cssContainingText('tr', hostname)).isDisplayed()).toBe(true);
  });

  it('should remove the lun', function(){
    volumesItem.click();
    browser.sleep(400);
    element.all(by.css('.tc_entries_dropdown')).get(0).click();
    element.all(by.css('.tc_entries_100')).get(0).click();
    browser.sleep(400);
    expect(volume.isPresent()).toBe(true);
    volume.click();
    browser.sleep(400);
    iscsiShareTab.click();
    browser.sleep(400);
    element(by.cssContainingText('tr', hostname)).click();
    element(by.css('.tc_lunDelete')).click();
    browser.sleep(400);
    element(by.id('bot2-Msg1')).click();
    browser.sleep(800);
  });

  it('should not display the lun anymore', function(){
    volumesItem.click();
    browser.sleep(400);
    element.all(by.css('.tc_entries_dropdown')).get(0).click();
    element.all(by.css('.tc_entries_100')).get(0).click();
    browser.sleep(400);
    expect(volume.isPresent()).toBe(true);
    volume.click();
    browser.sleep(400);
    iscsiShareTab.click();
    browser.sleep(400);
    expect(element(by.cssContainingText('tr', hostname)).isPresent()).toBe(false);
  });

  afterAll(function(){
    console.log('map_lun');
    helpers.delete_volume();
    helpers.delete_host();
  });

});