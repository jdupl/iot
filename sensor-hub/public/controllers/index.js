var controllers = angular.module('app.controllers.IndexController', ['ui.bootstrap']);

controllers.controller('IndexController', function($scope, $http, $interval) {
    $scope.alerts = [];
    $scope.visibility = [];
    $scope.options = {};

    function genOptsHygro (uuid) {
        $scope.options[uuid] = {
          margin: {top: 18},
          series: [
            {
              axis: "y",
              dataset: uuid,
              key: "y",
              label: "Humidity",
              color: "#1f77b4",
              type: ['line', 'dot'],
              id: 'Humidity ' + uuid
            }
          ],
          axes: {x: {key: "x", type: "date"}}
        };
    }

    function genOptsPhoto (uuid) {
        $scope.options[uuid] = {
          margin: {top: 18},
          series: [
            {
              axis: "y",
              dataset: uuid,
              key: "y",
              label: "Brightness",
              color: "#1f77b4",
              type: ['line', 'dot'],
              id: 'Brightness ' + uuid
            }
          ],
          axes: {x: {key: "x", type: "date"}}
        };
    }

    function genOptsDht11 (uuid) {
        $scope.options[uuid] = {
          margin: {top: 18},
          series: [
            {
              axis: "y",
              dataset: uuid,
              key: "temperature",
              label: "Temperature",
              color: "#c33a0f",
              type: ['line', 'dot'],
              id: 'DHT11 temp ' + uuid
          },
            {
              axis: "y2",
              dataset: uuid,
              key: "rel_humidity",
              label: "Relative humidity",
              color: "#1f77b4",
              type: ['line', 'dot'],
              id: 'DHT11 humidity ' + uuid
            }
          ],
          axes: {x: {key: "x", type: "date"}}
        };
    }

    $scope.isExpired = function(dataset, maxSec) {
        if (!dataset) {
            return false;
        }
        var last = dataset[dataset.length -1];
        return Date.now()- last.x > maxSec * 1000
    }
    $scope.expiredSince = function (dataset) {
        return dataset[dataset.length -1].x;
    }

    $scope.closeAlert = function(index) {
       $scope.alerts.splice(index, 1);
    };

    $scope.refresh = function() {
      $http.get('/api/records/latest')
        .success(function(data) {
          $scope.records = data.latest;

          // Get 48h history for chart
          var since = Math.floor(new Date().getTime() / 1000) - (3600 * 48);
          $http.get('/api/records/' + since)
            .success(function(data) {
              $scope.lastUpdate = Date.now();
              $scope.data_history = data.history;

              for (var t in $scope.data_history) {
                for (var v in $scope.data_history[t]) {
                  if ($scope.data_history[t].hasOwnProperty(v)) {
                    for (var i = 0; i < $scope.data_history[t][v].length; i++) {
                      $scope.data_history[t][v][i].x = new Date($scope.data_history[t][v][i].x * 1000)
                    }
                  }
                }
              }

              for (var i = 0; i < $scope.records.soil_humidity.length; i++) {
                $scope.records.soil_humidity[i].header = 'panel-' + getHeaderForValue($scope.records.soil_humidity[i].value);
                var uuid = $scope.records.soil_humidity[i].sensor_uuid;
                if (!$scope.options.hasOwnProperty(uuid)) {
                    genOptsHygro(uuid);
                }
              }
              for (var i = 0; i < $scope.records.dht11.length; i++) {
                var uuid = $scope.records.dht11[i].sensor_uuid
                if (!$scope.options.hasOwnProperty(uuid)) {
                    genOptsDht11(uuid);
                }
              }
              for (var i = 0; i < $scope.records.photocell.length; i++) {
                var uuid = $scope.records.photocell[i].sensor_uuid
                if (!$scope.options.hasOwnProperty(uuid)) {
                    genOptsPhoto(uuid);
                }
              }
            })
            .error(function(err, status) {
                console.log(err, status);
            });
        })
        .error(function(err, status) {
            console.log(err, status);
        });

    };
    $scope.serverLinkOK = function () {
      return Date.now() - $scope.lastUpdate < 30000;
    }

    $scope.refresh();
    $scope.intervalPromise = $interval(function() {
      $scope.refresh();
    }, 30000);
    $scope.$on('$destroy', function() {
      $interval.cancel($scope.intervalPromise);
    });

  function getHeaderForValue(val) {
    if (val > 1000 || val < 50) {
      return 'danger';
    } else if (val > 900 || val < 200) {
      return 'warning';
    } else {
      return 'success';
    }
  }
});
