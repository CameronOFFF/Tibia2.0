<?php

declare(strict_types=1);

namespace App\Models;

use App\Core\Model;

final class Troop extends Model
{
    public function listTypes(): array
    {
        return $this->db->query('SELECT * FROM troops ORDER BY id')->fetchAll();
    }

    public function villageTroops(int $villageId): array
    {
        $stmt = $this->db->prepare('SELECT t.*,vt.quantity FROM village_troops vt INNER JOIN troops t ON t.id=vt.troop_id WHERE vt.village_id=:id');
        $stmt->execute([':id' => $villageId]);
        return $stmt->fetchAll();
    }

    public function queueTraining(int $villageId, int $troopId, int $qty, int $seconds): void
    {
        $stmt = $this->db->prepare('INSERT INTO training_queue(village_id,troop_id,quantity,start_at,finish_at,status) VALUES (:v,:t,:q,NOW(),DATE_ADD(NOW(), INTERVAL :s SECOND),"running")');
        $stmt->execute([':v'=>$villageId,':t'=>$troopId,':q'=>$qty,':s'=>$seconds]);
    }

    public function processQueue(int $villageId): void
    {
        $stmt = $this->db->prepare('SELECT * FROM training_queue WHERE village_id=:id AND status="running" AND finish_at<=NOW()');
        $stmt->execute([':id' => $villageId]);
        foreach ($stmt->fetchAll() as $row) {
            $this->db->prepare('UPDATE village_troops SET quantity=quantity+:q WHERE village_id=:v AND troop_id=:t')
                ->execute([':q'=>$row['quantity'],':v'=>$villageId,':t'=>$row['troop_id']]);
            $this->db->prepare('UPDATE training_queue SET status="done" WHERE id=:id')->execute([':id' => $row['id']]);
        }
    }

    public function queueList(int $villageId): array
    {
        $stmt = $this->db->prepare('SELECT q.*, t.name FROM training_queue q INNER JOIN troops t ON t.id=q.troop_id WHERE q.village_id=:id AND q.status="running" ORDER BY q.finish_at ASC');
        $stmt->execute([':id'=>$villageId]);
        return $stmt->fetchAll();
    }
}
