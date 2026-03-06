<?php

declare(strict_types=1);

namespace App\Models;

use App\Core\Model;

final class Report extends Model
{
    public function create(int $userId, string $title, string $content): void
    {
        $stmt = $this->db->prepare('INSERT INTO reports(user_id,title,content) VALUES (:u,:t,:c)');
        $stmt->execute([':u'=>$userId,':t'=>$title,':c'=>$content]);
    }

    public function listByUser(int $userId): array
    {
        $stmt = $this->db->prepare('SELECT * FROM reports WHERE user_id=:u ORDER BY id DESC LIMIT 100');
        $stmt->execute([':u'=>$userId]);
        return $stmt->fetchAll();
    }
}
