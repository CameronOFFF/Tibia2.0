<?php

declare(strict_types=1);

namespace Config;

use PDO;
use PDOException;

class Database
{
    private array $config;
    private ?PDO $connection = null;

    public function __construct(array $config)
    {
        $this->config = $config;
        date_default_timezone_set($config['app']['timezone'] ?? 'UTC');
    }

    public function connection(): PDO
    {
        if ($this->connection instanceof PDO) {
            return $this->connection;
        }

        $db = $this->config['db'];
        $dsn = sprintf('mysql:host=%s;port=%d;dbname=%s;charset=%s', $db['host'], $db['port'], $db['name'], $db['charset']);

        try {
            $this->connection = new PDO($dsn, $db['user'], $db['pass'], [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
            ]);
        } catch (PDOException $e) {
            http_response_code(500);
            exit('Erro de conexão com MySQL: ' . $e->getMessage());
        }

        return $this->connection;
    }

    public function getConfig(): array
    {
        return $this->config;
    }
}
