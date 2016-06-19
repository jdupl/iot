angular.module('app', [
  'ngRoute',
  'app.controllers.IndexController',
]).config(function($routeProvider, $authProvider) {
    $routeProvider.when('/', {
      templateUrl: 'partials/index.html',
      controller: 'IndexController'
    });
  });
