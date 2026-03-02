<?php

declare(strict_types=1);

namespace App\Models;

use App\Core\Model;

final class User extends Model
{
    public function create(string $username, string $email, string $password): int
    {
        $stmt = $this->db->prepare('INSERT INTO users (username, email, password_hash) VALUES (:u,:e,:p)');
        $stmt->execute([
            ':u' => $username,
            ':e' => $email,
            ':p' => password_hash($password, PASSWORD_DEFAULT),
        ]);

        return (int) $this->db->lastInsertId();
    }

    public function findByEmail(string $email): ?array
    {
        $stmt = $this->db->prepare('SELECT * FROM users WHERE email = :email LIMIT 1');
        $stmt->execute([':email' => $email]);
        return $stmt->fetch() ?: null;
    }

    public function rankingsByPoints(): array
    {
        return $this->db->query('SELECT u.id,u.username,COALESCE(SUM(v.points),0) as points FROM users u LEFT JOIN villages v ON v.user_id=u.id GROUP BY u.id ORDER BY points DESC LIMIT 100')->fetchAll();
    }

    public function rankingsByWins(): array
    {
        return $this->db->query('SELECT u.id,u.username,COUNT(a.id) as wins FROM users u LEFT JOIN attacks a ON a.attacker_user_id=u.id AND a.status="resolved" AND a.winner_user_id=u.id GROUP BY u.id ORDER BY wins DESC LIMIT 100')->fetchAll();
    }
}
