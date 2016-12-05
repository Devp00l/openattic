var helpers = require('../../common.js');
var rbdCommons = require('./cephRbdCommon.js');

describe('ceph rbd creation and deletion', function(){
  var rbdProperties = new rbdCommons();
  var featureRbdName = "e2eFeatures";

  beforeAll(function(){
    helpers.login();
  });

  beforeEach(function(){
    rbdProperties.cephMenu.click();
    rbdProperties.cephRBDs.click();
    browser.sleep(helpers.configs.sleep);
  });

  var objSizeTests = [
    [4, "KiB"],
    [8, 'KiB'],
    [16, 'KiB'],
    [32, 'KiB'],
    [64, 'KiB'],
    [128, 'KiB'],
    [256, 'KiB'],
    [512, 'KiB'],
    [1, 'MiB'],
    [2, 'MiB'],
    [4, 'MiB'],
    [8, 'MiB'],
    [16, 'MiB'],
    [32, 'MiB']
  ];

  rbdProperties.useWriteablePools(function(cluster, pool){
    objSizeTests.forEach(function(sizeArr, index){
      var objSize = sizeArr[0] + '.00 ' + sizeArr[1];
      var rbdName = "e2eObjectSize" + index;
      it('should create a rbd with a specific object size: "' + objSize + '" object and rbd size on pool "' + pool.name
          + '" in cluster "' + cluster.name + '"', function(){
        rbdProperties.selectClusterAndPool(cluster, pool);
        rbdProperties.createRbd(rbdName, objSize);
      });
      it('should delete created rbd with a specific object size: "' + objSize + '" object and rbd size on pool "' + pool.name
        + '" in cluster "' + cluster.name + '"', function(){
        rbdProperties.deleteRbd(rbdName);
      });
    });
  });

  rbdProperties.useWriteablePools(function(cluster, pool){
    rbdProperties.expandedFeatureCases.forEach(function(testCase){
      var keys = Object.keys(rbdProperties.formElements.features.items);
      var values = rbdProperties.formElements.features.items;
      it('should create a rbd with the following expert option case: "[' + testCase + ']" options on pool "' + pool.name
          + '" in cluster "' + cluster.name + '"', function(){
        rbdProperties.selectClusterAndPool(cluster, pool);
        for (var i=0; i<7; i++){ // uncheck all boxes
          rbdProperties.checkCheckboxToBe(element(by.className(values[keys[i]])), false);
        }
        testCase.forEach(function(state, index){ // check the features
          rbdProperties.checkFeature(element(by.className(values[keys[index]])), state);
        });
        rbdProperties.createRbd(featureRbdName, null, testCase);
      });
      it('should delete created rbd with the following expert option case: "[' + testCase + ']" options on pool "' +
        pool.name + '" in cluster "' + cluster.name + '"', function(){
        rbdProperties.deleteRbd(featureRbdName);
      })
    });
  });

  afterAll(function(){
    console.log('ceph_rbd_creation -> ceph_rbd_creation.e2e.js');
  });
});
