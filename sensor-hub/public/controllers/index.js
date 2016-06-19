var controllers = angular.module('app.controllers.IndexController', []);

controllers.controller('IndexController', function($scope, $http) {
    $scope.alerts = [];

    $scope.closeAlert = function(index) {
       $scope.alerts.splice(index, 1);
    };

    $scope.refresh = function() {
      $http.get('/api/records/lastest')
          .success(function(data) {
              $scope.records = data.plannings;
          })
          .error(function(err, status) {
              console.log(err, status);
          });
    };
  $scope.refresh();
});
