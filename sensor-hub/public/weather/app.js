angular.module('app', [
  'ngRoute',
  'angularMoment',
  'n3-line-chart',
  'app.controllers.IndexController',
]).config(function($routeProvider) {
    $routeProvider.when('/', {
      templateUrl: 'partials/index.html',
      controller: 'IndexController'
  });
    $routeProvider.otherwise({redirectTo: '/'});
  });
