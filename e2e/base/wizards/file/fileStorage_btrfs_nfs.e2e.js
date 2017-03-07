var helpers = require('../../../common.js');
var wizardsCommon = require('../wizardsCommon.js');

describe('Wizard panel', function(){
  var wizardProperties = new wizardsCommon();
  var volumeName = 'protractor_wizard_fileVol01';
  var volume = element(by.cssContainingText('tr', volumeName));
  var shareName = 'oadev.domain.here';

  beforeAll(function(){
    helpers.login();
  });

  it('should land on the dashboard site after login', function(){
    expect(browser.getCurrentUrl()).toContain('#/dashboard');
  });

  // TODO: implement this test in the dashboard tests
  //it('should a widget title', function(){
  //  expect(element.all(by.css('.tc_widget_title')).get(1).getText()).toEqual('openATTIC Wizards');
  //  helpers.check_wizard_titles();
  //});

  //<-- begin wizard --->
  it('should open the "File Storage" wizard', function(){
    wizardProperties.openWizard('File Storage');
  });

  it('should test step 1 and fill it out and go to the next step', function(){
    wizardProperties.handleFirstPage('File Storage Step 1 - Create Volume', 'volume group', volumeName, '100MB', 'btrfs');
  });

  it('should test step 2 and fill it out and go to the last step', function(){
    wizardProperties.shareCreationElementCheck('File Storage Step 2 - Which Shares do you need?');
    wizardProperties.shareCreateNfs(shareName);
    wizardProperties.nextBtn.click();
  });

  it('should test step 3 and hit done to create everything set so far and close the wizard', function(){
    wizardProperties.configurationExecution('File Storage Step 3 - Save configuration');
  });
  //<-- end wizard --->

  afterAll(function(){
    helpers.delete_nfs_share(volumeName, shareName);
    helpers.delete_volume(volume, volumeName);
    console.log('fs_wiz_btrfs_nfs -> fileStorage_btrfs_nfs.e2e.js');
  });
});
