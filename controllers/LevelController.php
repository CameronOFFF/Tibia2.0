<?php

declare(strict_types=1);

namespace Controllers;

use Models\GuildMember;
use Models\LevelTracker;
use Models\TibiaScraper;

class LevelController extends BaseController
{
    private const AUTO_SYNC_INTERVAL_SECONDS = 300;

    public function index(): void
    {
        $this->requireAuth();
        $this->autoSyncIfNeeded();

        $tracker = new LevelTracker($this->database->connection());
        $rows = $tracker->all();

        $guild = new GuildMember($this->database->connection());
        $summary = [
            'total' => $guild->countAll(),
            'online' => $guild->countOnline(),
            'last_sync' => $guild->lastSyncAt(),
        ];

        $this->render('level/index', compact('rows', 'summary'));
    }

    private function autoSyncIfNeeded(): void
    {
        $guild = new GuildMember($this->database->connection());
        $lastSync = $guild->lastSyncAt();

        if ($lastSync && (time() - strtotime($lastSync)) < self::AUTO_SYNC_INTERVAL_SECONDS) {
            return;
        }

        $scraper = new TibiaScraper();
        $members = $scraper->fetchGuildMembers($this->config['app']['guild_url']);

        if (empty($members)) {
            return;
        }

        $guild->sync($members);
        $tracker = new LevelTracker($this->database->connection());
        $tracker->syncWeek($members);
    }
}
