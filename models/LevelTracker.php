<?php

declare(strict_types=1);

namespace Models;

use PDO;

class LevelTracker
{
    public function __construct(private readonly PDO $pdo)
    {
    }

    public function syncWeek(array $members): void
    {
        foreach ($members as $member) {
            $stmt = $this->pdo->prepare('INSERT INTO member_level_tracking (character_name, vocation, level_start_week, level_current, level_gain, week_start_date, updated_at) VALUES (:name, :vocation, :level, :level, 0, CURDATE(), NOW()) ON DUPLICATE KEY UPDATE level_current = VALUES(level_current), level_gain = VALUES(level_current) - level_start_week, vocation = VALUES(vocation), updated_at = NOW()');
            $stmt->execute([
                'name' => $member['name'],
                'vocation' => $member['vocation'],
                'level' => $member['level'],
            ]);
        }
    }

    public function all(): array
    {
        return $this->pdo->query('SELECT * FROM member_level_tracking ORDER BY level_gain DESC, level_current DESC')->fetchAll();
    }

    public function resetWeek(): void
    {
        $this->pdo->exec('UPDATE member_level_tracking SET level_start_week = level_current, level_gain = 0, week_start_date = CURDATE(), updated_at = NOW()');
    }

    public function upCount(): int
    {
        return (int) $this->pdo->query('SELECT COUNT(*) FROM member_level_tracking WHERE level_gain > 0')->fetchColumn();
    }
}
