<?php

declare(strict_types=1);

namespace App\Models;

use App\Core\Model;

final class Village extends Model
{
    public function createStarterVillage(int $userId, string $name): int
    {
        $x = random_int(1, 100);
        $y = random_int(1, 100);
        $stmt = $this->db->prepare('INSERT INTO villages (user_id,name,coord_x,coord_y,last_resource_update) VALUES (:uid,:name,:x,:y,NOW())');
        $stmt->execute([':uid' => $userId, ':name' => $name, ':x' => $x, ':y' => $y]);
        $villageId = (int) $this->db->lastInsertId();

        $this->db->prepare('INSERT INTO village_troops(village_id,troop_id,quantity) SELECT :vid,id,0 FROM troops')->execute([':vid' => $villageId]);
        $this->db->prepare('INSERT INTO buildings(village_id,building_key,level) VALUES (:v,"hq",1),( :v,"wood",1),(:v,"clay",1),(:v,"iron",1),(:v,"warehouse",1),(:v,"barracks",0),(:v,"wall",0)')->execute([':v' => $villageId]);

        return $villageId;
    }

    public function getMainVillage(int $userId): ?array
    {
        $stmt = $this->db->prepare('SELECT * FROM villages WHERE user_id=:uid ORDER BY id ASC LIMIT 1');
        $stmt->execute([':uid' => $userId]);
        return $stmt->fetch() ?: null;
    }

    public function rename(int $villageId, int $userId, string $name): void
    {
        $stmt = $this->db->prepare('UPDATE villages SET name=:name WHERE id=:id AND user_id=:uid');
        $stmt->execute([':name' => $name, ':id' => $villageId, ':uid' => $userId]);
    }

    public function getById(int $villageId): ?array
    {
        $stmt = $this->db->prepare('SELECT * FROM villages WHERE id=:id');
        $stmt->execute([':id' => $villageId]);
        return $stmt->fetch() ?: null;
    }

    public function allForMap(): array
    {
        return $this->db->query('SELECT v.id,v.name,v.coord_x,v.coord_y,v.points,u.username FROM villages v INNER JOIN users u ON u.id=v.user_id ORDER BY v.points DESC')->fetchAll();
    }

    public function addResources(int $villageId, array $resources): void
    {
        $stmt = $this->db->prepare('UPDATE villages SET wood=:w,clay=:c,iron=:i,last_resource_update=NOW() WHERE id=:id');
        $stmt->execute([':w'=>$resources['wood'],':c'=>$resources['clay'],':i'=>$resources['iron'],':id'=>$villageId]);
    }

    public function updatePoints(int $villageId): void
    {
        $stmt = $this->db->prepare('UPDATE villages v JOIN (SELECT village_id,SUM(level*100) points FROM buildings WHERE village_id=:id GROUP BY village_id) b ON b.village_id=v.id SET v.points=b.points WHERE v.id=:id');
        $stmt->execute([':id' => $villageId]);
    }
}
