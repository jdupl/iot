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
          })
          .error(function(err, status) {
              console.log(err, status);
          });
    };
  $scope.refresh();
});
