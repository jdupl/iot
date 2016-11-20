angular.module('app', [
  'ngRoute',
  'angularMoment',
  'n3-line-chart',
  'app.controllers.IndexController',
  'app.controllers.RelaysController',
]).config(function($routeProvider) {
    $routeProvider.when('/', {
      templateUrl: 'partials/index.html',
      controller: 'IndexController'
    })
    .when('/relays', {
      templateUrl: 'partials/relays.html',
      controller: 'RelaysController'
    });
    $routeProvider.otherwise({redirectTo: '/'});
  });
