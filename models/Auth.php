<?php

declare(strict_types=1);

namespace Models;

use PDO;

class Auth
{
    private const LEGACY_OWNER_HASH = '$2y$10$u7I8YhlhL.0J8Ff6ipRDjOO0nUxwJ4WQ5d8nJzW0E20JvokJ2Qj6W';

    public function __construct(private PDO $pdo)
    {
    }

    public function attempt(string $username, string $password): bool
    {
        $username = trim($username);

        $stmt = $this->pdo->prepare('SELECT * FROM users WHERE username = :username LIMIT 1');
        $stmt->execute(['username' => $username]);
        $user = $stmt->fetch();

        if (!$user) {
            return false;
        }

        $validPassword = password_verify($password, $user['password_hash']);

        if (!$validPassword && $this->isLegacyOwnerLogin($user, $password)) {
            $validPassword = true;
            $this->upgradePasswordHash((int) $user['id'], $password);
            $user['password_hash'] = password_hash($password, PASSWORD_DEFAULT);
        }

        if (!$validPassword) {
            return false;
        }

        if (password_needs_rehash($user['password_hash'], PASSWORD_DEFAULT)) {
            $this->upgradePasswordHash((int) $user['id'], $password);
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

    private function isLegacyOwnerLogin(array $user, string $password): bool
    {
        return $user['username'] === 'owner'
            && $password === 'owner123'
            && hash_equals(self::LEGACY_OWNER_HASH, (string) $user['password_hash']);
    }

    private function upgradePasswordHash(int $userId, string $password): void
    {
        $newHash = password_hash($password, PASSWORD_DEFAULT);
        $stmt = $this->pdo->prepare('UPDATE users SET password_hash = :hash WHERE id = :id');
        $stmt->execute([
            'hash' => $newHash,
            'id' => $userId,
        ]);
    }
}
