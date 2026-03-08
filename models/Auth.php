<?php

declare(strict_types=1);

namespace Models;

use PDO;

class Auth
{
    public function __construct(private readonly PDO $pdo)
    {
    }

    public function attempt(string $username, string $password): bool
    {
        $stmt = $this->pdo->prepare('SELECT * FROM users WHERE username = :username LIMIT 1');
        $stmt->execute(['username' => $username]);
        $user = $stmt->fetch();

        if (!$user || !password_verify($password, $user['password_hash'])) {
            return false;
        }

        $_SESSION['user'] = [
            'id' => (int) $user['id'],
            'username' => $user['username'],
            'role' => $user['role'],
        ];

        session_regenerate_id(true);

        return true;
    }

    public function logout(): void
    {
        $_SESSION = [];
        if (session_status() === PHP_SESSION_ACTIVE) {
            session_destroy();
        }
    }

    public function user(): ?array
    {
        return $_SESSION['user'] ?? null;
    }
}
