<?php

declare(strict_types=1);

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

define('BASE_PATH', dirname(__DIR__));

spl_autoload_register(static function (string $class): void {
    $prefixes = [
        'Config\\' => BASE_PATH . '/config/',
        'Models\\' => BASE_PATH . '/models/',
    ];

    foreach ($prefixes as $prefix => $dir) {
        if (str_starts_with($class, $prefix)) {
            $file = $dir . str_replace('\\', '/', substr($class, strlen($prefix))) . '.php';
            if (is_file($file)) {
                require_once $file;
            }
        }
    }
});

$config = require BASE_PATH . '/config/config.php';
$database = new Config\Database($config);
$pdo = $database->connection();
