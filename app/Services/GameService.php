<?php

declare(strict_types=1);

namespace App\Services;

use App\Models\Village;

final class GameService
{
    private array $baseProduction = ['wood' => 30, 'clay' => 30, 'iron' => 30];

    public function updateOfflineResources(array $village, array $buildings, Village $villageModel): array
    {
        $last = strtotime($village['last_resource_update']);
        $now = time();
        $elapsed = max(0, $now - $last);
        if ($elapsed === 0) {
            return $village;
        }

        $hours = $elapsed / 3600;
        $warehouse = 1000 * (int) (1.25 ** ($buildings['warehouse']['level'] ?? 1));

        foreach (['wood' => 'wood', 'clay' => 'clay', 'iron' => 'iron'] as $resource => $buildingKey) {
            $level = max(1, (int) ($buildings[$buildingKey]['level'] ?? 1));
            $rate = $this->baseProduction[$resource] * (1 + $level * 0.35);
            $village[$resource] = (int) min($warehouse, $village[$resource] + ($rate * $hours));
        }

        $villageModel->addResources((int)$village['id'], $village);
        $village['storage_limit'] = $warehouse;
        return $village;
    }

    public function buildingCost(int $level): array
    {
        return [
            'wood' => (int) round(60 * (1.6 ** ($level - 1))),
            'clay' => (int) round(50 * (1.55 ** ($level - 1))),
            'iron' => (int) round(40 * (1.5 ** ($level - 1))),
            'time' => (int) round(120 * (1.35 ** ($level - 1))),
        ];
    }

    public function canPay(array $village, array $cost): bool
    {
        return $village['wood'] >= $cost['wood'] && $village['clay'] >= $cost['clay'] && $village['iron'] >= $cost['iron'];
    }

    public function troopTravelSeconds(array $from, array $to, int $speed): int
    {
        $distance = sqrt((($from['coord_x'] - $to['coord_x']) ** 2) + (($from['coord_y'] - $to['coord_y']) ** 2));
        return max(60, (int) round($distance * $speed * 60));
    }
}
