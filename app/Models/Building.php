<?php

declare(strict_types=1);

namespace App\Models;

use App\Core\Model;

final class Building extends Model
{
    public function getVillageBuildings(int $villageId): array
    {
        $stmt = $this->db->prepare('SELECT * FROM buildings WHERE village_id=:id');
        $stmt->execute([':id' => $villageId]);
        $rows = $stmt->fetchAll();
        $result = [];
        foreach ($rows as $row) {
            $result[$row['building_key']] = $row;
        }
        return $result;
    }

    public function queueBuild(int $villageId, string $key, int $toLevel, int $seconds, array $cost): bool
    {
        $sql = 'INSERT INTO construction_queue (village_id,building_key,target_level,cost_wood,cost_clay,cost_iron,start_at,finish_at,status)
                VALUES (:v,:k,:l,:w,:c,:i,NOW(),DATE_ADD(NOW(), INTERVAL :s SECOND),"running")';
        return $this->db->prepare($sql)->execute([
            ':v'=>$villageId, ':k'=>$key, ':l'=>$toLevel, ':w'=>$cost['wood'], ':c'=>$cost['clay'], ':i'=>$cost['iron'], ':s'=>$seconds,
        ]);
    }

    public function processQueue(int $villageId): void
    {
        $stmt = $this->db->prepare('SELECT * FROM construction_queue WHERE village_id=:id AND status="running" AND finish_at<=NOW() ORDER BY id ASC');
        $stmt->execute([':id' => $villageId]);
        $done = $stmt->fetchAll();
        foreach ($done as $item) {
            $this->db->prepare('UPDATE buildings SET level=:lvl WHERE village_id=:vid AND building_key=:k')->execute([
                ':lvl' => $item['target_level'], ':vid' => $villageId, ':k' => $item['building_key'],
            ]);
            $this->db->prepare('UPDATE construction_queue SET status="done" WHERE id=:id')->execute([':id' => $item['id']]);
        }
    }

    public function currentQueue(int $villageId): array
    {
        $stmt = $this->db->prepare('SELECT * FROM construction_queue WHERE village_id=:id AND status="running" ORDER BY finish_at ASC');
        $stmt->execute([':id' => $villageId]);
        return $stmt->fetchAll();
    }
}
