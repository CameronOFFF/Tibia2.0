<?php

declare(strict_types=1);

session_start();

define('BASE_PATH', dirname(__DIR__));

require BASE_PATH . '/app/Core/Autoloader.php';
require BASE_PATH . '/config/config.php';
require BASE_PATH . '/app/Helpers/functions.php';

$app = new App\Core\App();
$app->run();
