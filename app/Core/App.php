<?php

declare(strict_types=1);

namespace App\Core;

use App\Controllers\AuthController;
use App\Controllers\GameController;
use App\Controllers\TribeController;
use App\Controllers\RankingController;

final class App
{
    public function run(): void
    {
        $requestPath = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?? '/';
        $scriptName = str_replace('\\', '/', $_SERVER['SCRIPT_NAME'] ?? '/index.php');
        $basePath = rtrim(dirname($scriptName), '/');

        if ($basePath !== '' && $basePath !== '.' && str_starts_with($requestPath, $basePath)) {
            $requestPath = substr($requestPath, strlen($basePath)) ?: '/';
        }

        $path = trim($requestPath, '/');
        $method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

        $routes = [
            'GET' => [
                '' => [AuthController::class, 'home'],
                'register' => [AuthController::class, 'showRegister'],
                'login' => [AuthController::class, 'showLogin'],
                'logout' => [AuthController::class, 'logout'],
                'dashboard' => [GameController::class, 'dashboard'],
                'village' => [GameController::class, 'village'],
                'map' => [GameController::class, 'map'],
                'barracks' => [GameController::class, 'barracks'],
                'reports' => [GameController::class, 'reports'],
                'tribes' => [TribeController::class, 'index'],
                'rankings' => [RankingController::class, 'index'],
            ],
            'POST' => [
                'register' => [AuthController::class, 'register'],
                'login' => [AuthController::class, 'login'],
                'village/rename' => [GameController::class, 'renameVillage'],
                'build' => [GameController::class, 'build'],
                'train' => [GameController::class, 'train'],
                'attack' => [GameController::class, 'attack'],
                'tribes/create' => [TribeController::class, 'create'],
                'tribes/join' => [TribeController::class, 'join'],
                'tribes/chat' => [TribeController::class, 'chat'],
            ],
        ];

        if (!isset($routes[$method][$path])) {
            http_response_code(404);
            echo 'Página não encontrada';
            return;
        }

        [$controllerClass, $action] = $routes[$method][$path];
        (new $controllerClass())->$action();
    }
}
