<?php

declare(strict_types=1);

return [
    'db' => [
        'host' => '127.0.0.1',
        'port' => 3306,
        'name' => 'never_duality',
        'user' => 'root',
        'pass' => '',
        'charset' => 'utf8mb4',
    ],
    'app' => [
        'name' => 'Never Duality Control Panel',
        'base_url' => 'http://localhost/Tibia2.0',
        'guild_url' => 'https://paulistinhaot.com/?subtopic=guilds&guild=Never+Duality+Dominium&action=show',
        'character_url' => 'https://paulistinhaot.com/?subtopic=characters&name=%s',
        'timezone' => 'America/Sao_Paulo',
    ],
    'security' => [
        'session_regenerate' => true,
    ],
];
