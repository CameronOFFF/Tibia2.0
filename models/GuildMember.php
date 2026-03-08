<?php

declare(strict_types=1);

namespace Models;

use PDO;

class GuildMember
{
    public function __construct(private PDO $pdo)
    {
    }

    public function sync(array $members): void
    {
        $stmt = $this->pdo->prepare('INSERT INTO guild_members (name, vocation, level, online_status, last_update) VALUES (:name, :vocation, :level, :online_status, NOW()) ON DUPLICATE KEY UPDATE vocation = VALUES(vocation), level = VALUES(level), online_status = VALUES(online_status), last_update = NOW()');

        foreach ($members as $member) {
            $stmt->execute($member);
        }
    }

    public function all(): array
    {
        return $this->pdo->query('SELECT * FROM guild_members ORDER BY level DESC')->fetchAll();
    }

    public function countOnline(): int
    {
        return (int) $this->pdo->query("SELECT COUNT(*) FROM guild_members WHERE online_status = 'online'")->fetchColumn();
    }

    public function countAll(): int
    {
        return (int) $this->pdo->query('SELECT COUNT(*) FROM guild_members')->fetchColumn();
    }
}
