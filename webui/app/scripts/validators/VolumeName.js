'use strict';

angular.module('openattic')
  .directive('validname', function() {
    return {
      require: 'ngModel',
      link: function (scope, elem, attrs, ctrl) {
        ctrl.$parsers.unshift(function (viewValue) {
          ctrl.$setValidity('validname', true);

          if (typeof viewValue !== 'undefined' && viewValue.length > 0) {
            var match = viewValue.match('[^a-zA-Z0-9+_.-]') || [];

            if (viewValue === '.' || viewValue === '..') {
              ctrl.$setValidity('validname', false);
              scope.errortext = 'LV names may not be "." or ".."!';
            }
            else if (viewValue[0] === '-') {
              ctrl.$setValidity('validname', false);
              scope.errortext = 'LV names must not begin with a hyphen.';
            }
            else if (match.length > 0) {
              ctrl.$setValidity('validname', false);
              scope.errortext = 'The following characters are valid: ' +
              'a-z A-Z 0-9 + _ . -';
            }
            else if (viewValue.indexOf('snapshot') === 0 || viewValue.indexOf('pvmove') === 0) {
              ctrl.$setValidity('validname', false);
              scope.errortext = 'The volume name must not begin with "snapshot" or "pvmove".';
            }
            else if (viewValue.indexOf('_mlog') !== -1 || viewValue.indexOf('_mimage') !== -1) {
              ctrl.$setValidity('validname', false);
              scope.errortext = 'The volume name must not contain "_mlog" or "_mimage".';
            }
          }

          return viewValue;
        });
      }
    };
  })
  .directive('uniquename', function(VolumeService, $timeout) {
    return {
      restrict: 'A',
      require: 'ngModel',
      link: function(scope, elem, attrs, ctrl) {
        var stop_timeout;

        return scope.$watch(function () {
          return ctrl.$modelValue;
        }, function (modelValue) {
          ctrl.$setValidity('uniquename', true);
          $timeout.cancel(stop_timeout);

          if (modelValue !== '' && typeof modelValue !== 'undefined') {
            stop_timeout = $timeout(function () {
              VolumeService.query({'name': modelValue})
                .$promise
                .then(function (res) {
                  return ctrl.$setValidity('uniquename', res.length === 0);
                })
                .catch(function (error) {
                  console.log('An error occurred', error);
                });
            }, 300);
          }
        });
      }
    };
  });