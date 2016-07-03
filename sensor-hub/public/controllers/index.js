var controllers = angular.module('app.controllers.IndexController', ['chart.js', 'ui.bootstrap']);

controllers.controller('IndexController', function($scope, $http, $interval) {
    $scope.alerts = [];

    // $scope.series = ['Soil Humidity'];
    $scope.onClick = function (points, evt) {
      console.log(points, evt);
    };

    $scope.history = [];
    $scope.series = ['Series A'];

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
          // Get 48h history for chart
          var since = Math.floor(new Date().getTime() / 1000) - (3600 * 48);
          $http.get('/api/records/' + since)
            .success(function(data) {
              $scope.history = data.history;
            })
            .error(function(err, status) {
                console.log(err, status);
            });
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

  function getHeaderForValue(val) {
    if (val > 920) {
      return 'danger';
    } else if (val > 800 || val < 300) {
      return 'warning';
    } else if (val > 600) {
      return 'success';
    } else {
      return 'warning';
    }
  }
});
