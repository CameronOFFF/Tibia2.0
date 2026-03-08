<?php

declare(strict_types=1);

namespace Models;

use PDO;

class Log
{
    public function __construct(private readonly PDO $pdo)
    {
    }

    public function add(?int $userId, string $action, string $details = ''): void
    {
        $stmt = $this->pdo->prepare('INSERT INTO logs (user_id, action, details, created_at) VALUES (:user_id, :action, :details, NOW())');
        $stmt->execute([
            'user_id' => $userId,
            'action' => $action,
            'details' => $details,
        ]);
    }

    public function latest(int $limit = 100): array
    {
        $stmt = $this->pdo->prepare('SELECT l.*, u.username FROM logs l LEFT JOIN users u ON u.id = l.user_id ORDER BY l.id DESC LIMIT :limit');
        $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
        $stmt->execute();

        return $stmt->fetchAll();
    }
}
