<?php

declare(strict_types=1);

namespace App\Models;

use App\Core\Model;

final class Attack extends Model
{
    public function send(int $attackerUser, int $fromVillage, int $toVillage, int $travelSeconds, array $units): void
    {
        $stmt = $this->db->prepare('INSERT INTO attacks(attacker_user_id,from_village_id,to_village_id,units_json,depart_at,arrival_at,status) VALUES (:u,:f,:t,:j,NOW(),DATE_ADD(NOW(), INTERVAL :s SECOND),"traveling")');
        $stmt->execute([':u'=>$attackerUser,':f'=>$fromVillage,':t'=>$toVillage,':j'=>json_encode($units, JSON_THROW_ON_ERROR),':s'=>$travelSeconds]);
    }

    public function processPending(): array
    {
        $rows = $this->db->query('SELECT * FROM attacks WHERE status="traveling" AND arrival_at<=NOW()')->fetchAll();
        $resolved = [];
        foreach ($rows as $row) {
            $this->db->prepare('UPDATE attacks SET status="arrived" WHERE id=:id')->execute([':id'=>$row['id']]);
            $resolved[] = $row;
        }
        return $resolved;
    }

    public function resolve(int $attackId, int $winnerUserId, int $lootWood, int $lootClay, int $lootIron): void
    {
        $stmt = $this->db->prepare('UPDATE attacks SET status="resolved",winner_user_id=:w,loot_wood=:lw,loot_clay=:lc,loot_iron=:li,resolved_at=NOW() WHERE id=:id');
        $stmt->execute([':w'=>$winnerUserId,':lw'=>$lootWood,':lc'=>$lootClay,':li'=>$lootIron,':id'=>$attackId]);
    }
}
