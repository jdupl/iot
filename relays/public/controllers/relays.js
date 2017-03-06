var controllers = angular.module('app.controllers.RelaysController', ['ui.bootstrap']);

controllers.controller('RelaysController', function($scope, $http, $interval) {
    $scope.alerts = [];

    $scope.closeAlert = function(index) {
       $scope.alerts.splice(index, 1);
    };

    $scope.serverLinkOK = function () {
      return Date.now() - $scope.lastUpdate < 30000;
    };

    $scope.refresh = function() {
      $http.get('/api/relays')
        .success(function(data) {
          $scope.relays =[];
          $scope.relays = data.relays;
          $scope.lastUpdate = Date.now();
        })
        .error(function(err, status) {
            console.log(err, status);
        });
    };

    $scope.setRelay = function(pinNum, newState) {
      var req = {'state_str': newState};
      console.log(req);
      $http.post('/api/relays/' + pinNum, req, {headers: {'Content-Type': 'application/json'}})
        .success(function(data) {
          $scope.refresh();
        })
        .error(function(err, status) {
            console.log(err, status);
        });
    };

    $scope.refresh();
    $scope.intervalPromise = $interval(function() {
      $scope.refresh();
    }, 30000);
    $scope.$on('$destroy', function() {
      $interval.cancel($scope.intervalPromise);
    });
});
