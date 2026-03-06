<?php

declare(strict_types=1);

namespace App\Models;

use App\Core\Model;

final class Tribe extends Model
{
    public function create(int $ownerId, string $name, string $tag): void
    {
        $stmt = $this->db->prepare('INSERT INTO tribes(name,tag,owner_user_id) VALUES (:n,:t,:o)');
        $stmt->execute([':n'=>$name,':t'=>$tag,':o'=>$ownerId]);
        $tribeId = (int) $this->db->lastInsertId();
        $this->db->prepare('INSERT INTO tribe_members(tribe_id,user_id,role) VALUES (:tr,:u,"leader")')->execute([':tr'=>$tribeId,':u'=>$ownerId]);
    }

    public function join(int $tribeId, int $userId): void
    {
        $stmt = $this->db->prepare('INSERT IGNORE INTO tribe_members(tribe_id,user_id,role) VALUES (:t,:u,"member")');
        $stmt->execute([':t'=>$tribeId,':u'=>$userId]);
    }

    public function allWithPoints(): array
    {
        return $this->db->query('SELECT tr.id,tr.name,tr.tag,COUNT(tm.user_id) members,COALESCE(SUM(v.points),0) points FROM tribes tr LEFT JOIN tribe_members tm ON tm.tribe_id=tr.id LEFT JOIN villages v ON v.user_id=tm.user_id GROUP BY tr.id ORDER BY points DESC')->fetchAll();
    }

    public function myTribe(int $userId): ?array
    {
        $stmt = $this->db->prepare('SELECT tr.* FROM tribes tr INNER JOIN tribe_members tm ON tm.tribe_id=tr.id WHERE tm.user_id=:u LIMIT 1');
        $stmt->execute([':u' => $userId]);
        return $stmt->fetch() ?: null;
    }

    public function postChat(int $tribeId, int $userId, string $message): void
    {
        $stmt = $this->db->prepare('INSERT INTO tribe_chat(tribe_id,user_id,message) VALUES (:t,:u,:m)');
        $stmt->execute([':t'=>$tribeId,':u'=>$userId,':m'=>$message]);
    }

    public function chatMessages(int $tribeId): array
    {
        $stmt = $this->db->prepare('SELECT c.*,u.username FROM tribe_chat c INNER JOIN users u ON u.id=c.user_id WHERE c.tribe_id=:t ORDER BY c.id DESC LIMIT 50');
        $stmt->execute([':t'=>$tribeId]);
        return array_reverse($stmt->fetchAll());
    }
}
