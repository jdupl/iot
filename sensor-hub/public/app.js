angular.module('app', [
  'ngRoute',
  'angularMoment',
  'app.controllers.IndexController',
]).config(function($routeProvider, ChartJsProvider) {
    $routeProvider.when('/', {
      templateUrl: 'partials/index.html',
      controller: 'IndexController'
    });
    $routeProvider.otherwise({redirectTo: '/'});
  });
