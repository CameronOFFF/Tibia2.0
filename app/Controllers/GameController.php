<?php

declare(strict_types=1);

namespace App\Controllers;

use App\Core\Controller;
use App\Models\Attack;
use App\Models\Building;
use App\Models\Report;
use App\Models\Troop;
use App\Models\Village;
use App\Services\GameService;

final class GameController extends Controller
{
    private Village $villageModel;
    private Building $buildingModel;
    private Troop $troopModel;
    private Attack $attackModel;
    private Report $reportModel;
    private GameService $service;

    public function __construct()
    {
        $this->villageModel = new Village();
        $this->buildingModel = new Building();
        $this->troopModel = new Troop();
        $this->attackModel = new Attack();
        $this->reportModel = new Report();
        $this->service = new GameService();
    }

    private function loadVillageState(): array
    {
        requireAuth();
        $village = $this->villageModel->getMainVillage((int) currentUserId());
        $this->buildingModel->processQueue((int)$village['id']);
        $this->troopModel->processQueue((int)$village['id']);
        $buildings = $this->buildingModel->getVillageBuildings((int)$village['id']);
        $village = $this->service->updateOfflineResources($village, $buildings, $this->villageModel);
        $this->villageModel->updatePoints((int)$village['id']);
        $this->processAttacks();
        return [$village, $buildings];
    }

    private function processAttacks(): void
    {
        foreach ($this->attackModel->processPending() as $attack) {
            $attacker = $this->villageModel->getById((int)$attack['from_village_id']);
            $defender = $this->villageModel->getById((int)$attack['to_village_id']);
            if (!$attacker || !$defender) { continue; }
            $attPower = array_sum((array) json_decode($attack['units_json'], true));
            $defPower = max(1, (int) floor($defender['points'] / 50));
            $winner = $attPower > $defPower ? (int)$attack['attacker_user_id'] : (int)$defender['user_id'];
            $loot = $attPower > $defPower ? ['wood'=>min(200,$defender['wood']),'clay'=>min(200,$defender['clay']),'iron'=>min(200,$defender['iron'])] : ['wood'=>0,'clay'=>0,'iron'=>0];

            if ($loot['wood'] > 0) {
                $this->villageModel->addResources((int)$defender['id'], ['wood'=>$defender['wood']-$loot['wood'],'clay'=>$defender['clay']-$loot['clay'],'iron'=>$defender['iron']-$loot['iron']]);
                $this->villageModel->addResources((int)$attacker['id'], ['wood'=>$attacker['wood']+$loot['wood'],'clay'=>$attacker['clay']+$loot['clay'],'iron'=>$attacker['iron']+$loot['iron']]);
            }
            $this->attackModel->resolve((int)$attack['id'], $winner, $loot['wood'], $loot['clay'], $loot['iron']);
            $title = 'Relatório de Batalha #' . $attack['id'];
            $content = sprintf('Ataque de %s(%d|%d) para %s(%d|%d). Vencedor UserID %d. Saque W/C/I: %d/%d/%d.', $attacker['name'],$attacker['coord_x'],$attacker['coord_y'],$defender['name'],$defender['coord_x'],$defender['coord_y'],$winner,$loot['wood'],$loot['clay'],$loot['iron']);
            $this->reportModel->create((int)$attack['attacker_user_id'], $title, $content);
            $this->reportModel->create((int)$defender['user_id'], $title, $content);
        }
    }

    public function dashboard(): void
    {
        [$village, $buildings] = $this->loadVillageState();
        $this->view('game/dashboard', [
            'village' => $village,
            'buildings' => $buildings,
            'constructionQueue' => $this->buildingModel->currentQueue((int)$village['id']),
        ]);
    }

    public function village(): void { $this->dashboard(); }

    public function map(): void
    {
        [$village] = $this->loadVillageState();
        $this->view('game/map', ['village'=>$village, 'villages'=>$this->villageModel->allForMap()]);
    }

    public function barracks(): void
    {
        [$village] = $this->loadVillageState();
        $this->view('game/barracks', [
            'village' => $village,
            'troops' => $this->troopModel->listTypes(),
            'owned' => $this->troopModel->villageTroops((int)$village['id']),
            'queue' => $this->troopModel->queueList((int)$village['id']),
        ]);
    }

    public function reports(): void
    {
        [$village] = $this->loadVillageState();
        $this->view('game/reports', ['village'=>$village, 'reports'=>$this->reportModel->listByUser((int)currentUserId())]);
    }

    public function renameVillage(): void
    {
        [$village] = $this->loadVillageState();
        $this->villageModel->rename((int)$village['id'], (int)currentUserId(), trim($_POST['name']));
        $this->redirect('dashboard');
    }

    public function build(): void
    {
        [$village, $buildings] = $this->loadVillageState();
        $key = $_POST['building_key'];
        $nextLevel = ((int)$buildings[$key]['level']) + 1;
        $cost = $this->service->buildingCost($nextLevel);
        if ($this->service->canPay($village, $cost)) {
            $this->villageModel->addResources((int)$village['id'], ['wood'=>$village['wood']-$cost['wood'],'clay'=>$village['clay']-$cost['clay'],'iron'=>$village['iron']-$cost['iron']]);
            $this->buildingModel->queueBuild((int)$village['id'], $key, $nextLevel, $cost['time'], $cost);
        }
        $this->redirect('dashboard');
    }

    public function train(): void
    {
        [$village] = $this->loadVillageState();
        $troopId = (int)$_POST['troop_id'];
        $qty = max(1, (int)$_POST['qty']);
        foreach ($this->troopModel->listTypes() as $troop) {
            if ((int)$troop['id'] === $troopId) {
                $cost = ['wood'=>$troop['cost_wood']*$qty,'clay'=>$troop['cost_clay']*$qty,'iron'=>$troop['cost_iron']*$qty];
                if ($this->service->canPay($village, $cost)) {
                    $this->villageModel->addResources((int)$village['id'], ['wood'=>$village['wood']-$cost['wood'],'clay'=>$village['clay']-$cost['clay'],'iron'=>$village['iron']-$cost['iron']]);
                    $this->troopModel->queueTraining((int)$village['id'], $troopId, $qty, (int)$troop['train_time'] * $qty);
                }
                break;
            }
        }
        $this->redirect('barracks');
    }

    public function attack(): void
    {
        [$village] = $this->loadVillageState();
        $toVillage = $this->villageModel->getById((int)$_POST['target_village_id']);
        if ($toVillage && (int)$toVillage['id'] !== (int)$village['id']) {
            $speed = 18;
            $travel = $this->service->troopTravelSeconds($village, $toVillage, $speed);
            $units = ['spear' => max(1, (int)($_POST['spear'] ?? 1))];
            $this->attackModel->send((int)currentUserId(), (int)$village['id'], (int)$toVillage['id'], $travel, $units);
        }
        $this->redirect('map');
    }
}
