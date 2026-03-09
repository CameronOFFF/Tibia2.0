<?php

declare(strict_types=1);

namespace Models;

use PDO;

class WatchList
{
    private array $tables = [
        'hunted' => 'hunted_list',
        'friend' => 'friend_list',
        'neutral' => 'neutral_list',
        'ally' => 'ally_list',
        'guild' => 'guild_watch',
    ];

    public function __construct(private PDO $pdo)
    {
    }

    public function all(string $type): array
    {
        $table = $this->table($type);
        return $this->pdo->query("SELECT * FROM {$table} ORDER BY id DESC")->fetchAll();
    }

    public function find(string $type, int $id): ?array
    {
        $table = $this->table($type);
        $stmt = $this->pdo->prepare("SELECT * FROM {$table} WHERE id = :id");
        $stmt->execute(['id' => $id]);
        $row = $stmt->fetch();

        return $row ?: null;
    }

    public function create(string $type, array $data): void
    {
        if ($type === 'guild') {
            $stmt = $this->pdo->prepare('INSERT INTO guild_watch (guild_name, world, notes, added_by, created_at) VALUES (:name, :world, :notes, :added_by, NOW())');
            $stmt->execute([
                'name' => $data['guild_name'] ?? '',
                'world' => $data['world'] ?? '',
                'notes' => $data['notes'] ?? '',
                'added_by' => $data['added_by'],
            ]);
            return;
        }

        $table = $this->table($type);
        $stmt = $this->pdo->prepare("INSERT INTO {$table} (character_name, guild, reason, notes, added_by, created_at) VALUES (:name, :guild, :reason, :notes, :added_by, NOW())");
        $stmt->execute([
            'name' => $data['character_name'] ?? '',
            'guild' => $data['guild'] ?? '',
            'reason' => $data['reason'] ?? '',
            'notes' => $data['notes'] ?? '',
            'added_by' => $data['added_by'],
        ]);
    }

    public function update(string $type, int $id, array $data): void
    {
        if ($type === 'guild') {
            $stmt = $this->pdo->prepare('UPDATE guild_watch SET guild_name = :name, world = :world, notes = :notes WHERE id = :id');
            $stmt->execute([
                'id' => $id,
                'name' => $data['guild_name'] ?? '',
                'world' => $data['world'] ?? '',
                'notes' => $data['notes'] ?? '',
            ]);
            return;
        }

        $table = $this->table($type);
        $stmt = $this->pdo->prepare("UPDATE {$table} SET character_name = :name, guild = :guild, reason = :reason, notes = :notes WHERE id = :id");
        $stmt->execute([
            'id' => $id,
            'name' => $data['character_name'] ?? '',
            'guild' => $data['guild'] ?? '',
            'reason' => $data['reason'] ?? '',
            'notes' => $data['notes'] ?? '',
        ]);
    }

    public function delete(string $type, int $id): void
    {
        $table = $this->table($type);
        $stmt = $this->pdo->prepare("DELETE FROM {$table} WHERE id = :id");
        $stmt->execute(['id' => $id]);
    }

    private function table(string $type): string
    {
        if (!isset($this->tables[$type])) {
            throw new \InvalidArgumentException('Tipo de lista inválido');
        }

        return $this->tables[$type];
    }
}
