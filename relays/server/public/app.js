angular.module('app', [
  'ngRoute',
  'app.controllers.RelaysController',
]).config(function($routeProvider) {
    $routeProvider.when('/', {
      templateUrl: 'partials/relays.html',
      controller: 'RelaysController'
    });
    $routeProvider.otherwise({redirectTo: '/'});
  });
