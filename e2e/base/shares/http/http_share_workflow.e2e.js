var helpers = require('../../../common.js');

describe('HTTP Share workflow', function(){

  var volumename = 'protractor_httpWorkflow_vol';
  var volume = element.all(by.cssContainingText('tr', volumename)).get(0);

  beforeAll(function(){
    helpers.login();
    helpers.create_volume(volumename, "btrfs");
  });

  beforeEach(function(){
    expect(volume.isDisplayed()).toBe(true);
    volume.click();
    browser.sleep(400);
    element(by.css('.tc_httpShareTab')).click();
    browser.sleep(400);
    element(by.css('.tc_httpShareAdd')).click();
    browser.sleep();
  });

  it('should have a "Create HTTP Share" title', function(){
    expect(element(by.css('.tc_formHeadline h3')).getText()).toEqual('Create HTTP Share');
  });

  it('should have one input field', function(){
    expect(element(by.id('sharePath')).isDisplayed()).toBe(true);
  });

  it('should should have a back button', function(){
    expect(element(by.css('.tc_backButton')).isPresent()).toBe(true);
  });

  it('should have a submit button', function(){
    expect(element(by.css('.tc_submitButton')).isPresent()).toBe(true);
  });

  it('should show an error message when hitting the submit button without any data', function(){
    element(by.id('sharePath')).clear();
    element(by.css('.tc_submitButton')).click();
    expect(element(by.css('.tc_pathRequired')).isDisplayed()).toBe(true);
  });

  it('should navigate back to the HTTP-Shares overview when hitting the button', function(){
    var backButton = element(by.css('.tc_backButton'));
    backButton.click();

    expect(element(by.css('.tc_oadatatable_http_shares')).isPresent()).toBe(true);
  });

  afterAll(function(){
    helpers.delete_volume(volume, volumename);
    console.log('http_share -> http_share_workflow.e2e.js');
  });

});