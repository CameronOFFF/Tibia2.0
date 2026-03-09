<?php

declare(strict_types=1);

namespace Controllers;

use Models\Dashboard;
use Models\LevelTracker;

class DashboardController extends BaseController
{
    public function index(): void
    {
        $this->requireAuth();
        $dashboard = new Dashboard($this->database->connection());
        $tracker = new LevelTracker($this->database->connection());

        $stats = $dashboard->stats();
        $ups = $tracker->all();

        $alerts = array_filter([
            $stats['hunted_online'] > 0 ? "⚠️ Hunted online: {$stats['hunted_online']}" : null,
            $stats['enemy_guild_online'] > 0 ? "⚠️ Guild inimiga online: {$stats['enemy_guild_online']}" : null,
            $tracker->upCount() > 0 ? '✅ Há membros que uparam na semana.' : null,
        ]);

        $this->render('dashboard/index', compact('stats', 'ups', 'alerts'));
    }
}
