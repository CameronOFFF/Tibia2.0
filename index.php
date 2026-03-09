<?php

declare(strict_types=1);

session_start();

define('BASE_PATH', __DIR__);

autoloadRegister();

require_once BASE_PATH . '/config/helpers.php';

$database = new Config\Database(require BASE_PATH . '/config/config.php');
$appConfig = $database->getConfig();

$router = new Config\Router($database, $appConfig);
$router->dispatch($_GET['route'] ?? 'dashboard/index');

function autoloadRegister(): void
{
    spl_autoload_register(static function (string $class): void {
        $prefixes = [
            'Config\\' => BASE_PATH . '/config/',
            'Controllers\\' => BASE_PATH . '/controllers/',
            'Models\\' => BASE_PATH . '/models/',
        ];

        foreach ($prefixes as $prefix => $baseDir) {
            if (str_starts_with($class, $prefix)) {
                $relativeClass = substr($class, strlen($prefix));
                $file = $baseDir . str_replace('\\', '/', $relativeClass) . '.php';
                if (is_file($file)) {
                    require_once $file;
                }
            }
        }
    });
}
