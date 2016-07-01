var controllers = angular.module('app.controllers.IndexController', []);

controllers.controller('IndexController', function($scope, $http) {
    $scope.alerts = [];

    $scope.closeAlert = function(index) {
       $scope.alerts.splice(index, 1);
    };

    $scope.refresh = function() {
      $http.get('/api/records/latest')
          .success(function(data) {
              $scope.records = data.records;
              for (var i = 0; i < $scope.records.length; i++) {
                $scope.records[i].header = 'panel-' + getHeaderForValue($scope.records[i].value);
              }
          })
          .error(function(err, status) {
              console.log(err, status);
          });
    };
  $scope.refresh();

  function getHeaderForValue(val) {
    if (val > 920) {
      return 'primary';
    } else if (val > 800 || val < 300) {
      return 'danger';
    } else if (val > 600) {
      return 'success';
    } else {
      return 'warning';
    }
  }
});
