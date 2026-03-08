<?php

declare(strict_types=1);

namespace Config;

class Router
{
    public function __construct(private Database $database, private array $config)
    {
    }

    public function dispatch(string $route): void
    {
        [$controllerName, $methodName] = array_pad(explode('/', $route), 2, 'index');
        $controllerClass = 'Controllers\\' . ucfirst($controllerName) . 'Controller';

        if (!class_exists($controllerClass)) {
            http_response_code(404);
            exit('Controller não encontrado.');
        }

        $controller = new $controllerClass($this->database, $this->config);

        if (!method_exists($controller, $methodName)) {
            http_response_code(404);
            exit('Método não encontrado.');
        }

        $controller->{$methodName}();
    }
}
