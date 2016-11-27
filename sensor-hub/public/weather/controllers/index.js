var controllers = angular.module('app.controllers.IndexController', ['ui.bootstrap']);

controllers.controller('IndexController', function($scope, $http, $interval) {
    $scope.alerts = [];
    $scope.visibility = [];
    $scope.options = {};

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
    $scope.createOptions= function(bmpUUID, dht11UUID, rainUUID) {
      $scope.options['combined'] = {
        margin: {top: 18},
        series: [
          {
            axis: "y",
            dataset: 'bmp',
            key: "temperature",
            label: "Temperature",
            color: "#c33a0f",
            type: ['line', 'dot'],
            id: 'BMP temp'
          },
          {
            axis: "y2",
            dataset: 'dht11',
            key: "rel_humidity",
            label: "Relative humidity",
            color: "#1f77b4",
            type: ['line', 'dot'],
            id: 'DHT11 humidity '
          }
        ],
        axes: {x: {key: "x", type: "date"}}
      };

      $scope.options['bmp_pressure'] = {
        margin: {top: 18},
        series: [
          {
            axis: "y",
            dataset: 'bmp',
            key: "pressure_kpa",
            label: "Pressure kPa",
            color: "#c33a0f",
            type: ['line', 'dot'],
            id: 'BMP pressure'
          }
        ],
        axes: {x: {key: "x", type: "date"}}
      };
      $scope.options['dht11_rel_humidity'] = {
        margin: {top: 18},
        series: [
          {
            axis: "y",
            dataset: 'dht11',
            key: "rel_humidity",
            label: "Relative humidity",
            color: "#1f77b4",
            type: ['line', 'dot'],
            id: 'DHT11 humidity '
          }
        ],
        axes: {x: {key: "x", type: "date"}}
      };
      $scope.options['rain'] = {
        margin: {top: 18},
        series: [
          {
            axis: "y",
            dataset: 'rain',
            key: "value",
            label: "Rain detector",
            color: "#1f77b4",
            type: ['line', 'dot'],
            id: 'Rain '
          }
        ],
        axes: {x: {key: "x", type: "date"}}
      };
    };


    $scope.refresh = function() {
      $http.get('/api/records/latest')
        .success(function(data) {
          $scope.records = data.latest;
          var bmpUUID = $scope.records['bmp'][0]['sensor_uuid'];
          var dht11UUID = $scope.records['dht11'][0]['sensor_uuid'];
          var rainUUID = $scope.records['rain'][0]['sensor_uuid'];
          $scope.createOptions(bmpUUID, dht11UUID, rainUUID);

          // Get 48h history for chart
          var since = Math.floor(new Date().getTime() / 1000) - (3600 * 48);
          $http.get('/api/records/' + since)
            .success(function(data) {
              $scope.lastUpdate = Date.now();
              $scope.data_history = data.history;
              for (var i = 0; i < $scope.data_history['bmp'].length; i++) {
                $scope.data_history['bmp'][i].x = new Date($scope.data_history['bmp'][i].x * 1000)
              }
              for (var i = 0; i < $scope.data_history['rain'].length; i++) {
                $scope.data_history['rain'][i].x = new Date($scope.data_history['rain'][i].x * 1000)
              }

              for (var t in $scope.data_history) {
                for (var v in $scope.data_history[t]) {
                  if ($scope.data_history[t].hasOwnProperty(v)) {
                    for (var i = 0; i < $scope.data_history[t][v].length; i++) {
                      $scope.data_history[t][v][i].x = new Date($scope.data_history[t][v][i].x * 1000)
                    }
                  }
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
});
