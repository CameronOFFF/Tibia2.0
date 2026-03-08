<?php

declare(strict_types=1);

namespace Models;

use PDO;

class CharacterScan
{
    public function __construct(private PDO $pdo)
    {
    }

    public function save(array $character): void
    {
        $stmt = $this->pdo->prepare('INSERT INTO character_scans (name, vocation, level, guild_name, status, scanned_at) VALUES (:name, :vocation, :level, :guild, :status, NOW()) ON DUPLICATE KEY UPDATE vocation = VALUES(vocation), level = VALUES(level), guild_name = VALUES(guild_name), status = VALUES(status), scanned_at = NOW()');
        $stmt->execute($character);
    }
}
