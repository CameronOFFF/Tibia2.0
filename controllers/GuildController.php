<?php

declare(strict_types=1);

namespace Controllers;

use Models\GuildMember;
use Models\LevelTracker;
use Models\TibiaScraper;

class GuildController extends BaseController
{
    private const AUTO_SYNC_INTERVAL_SECONDS = 300;

    public function index(): void
    {
        $this->requireAuth();
        $this->autoSyncIfNeeded();

        $model = new GuildMember($this->database->connection());
        $members = $model->all();
        $summary = [
            'total' => $model->countAll(),
            'online' => $model->countOnline(),
            'last_sync' => $model->lastSyncAt(),
        ];

        $this->render('guild/index', compact('members', 'summary'));
    }

    public function sync(): void
    {
        $user = $this->requireRole(['OWNER', 'ADMIN', 'LEADER']);

        $count = $this->runSync();

        $this->log->add($user['id'], 'guild_sync', 'Sincronização manual executada: ' . $count . ' membros');

        redirect('guild/index');
    }

    private function autoSyncIfNeeded(): void
    {
        $model = new GuildMember($this->database->connection());
        $lastSync = $model->lastSyncAt();

        if (!$lastSync || (time() - strtotime($lastSync)) >= self::AUTO_SYNC_INTERVAL_SECONDS) {
            $this->runSync();
        }
    }

    private function runSync(): int
    {
        $scraper = new TibiaScraper();
        $members = $scraper->fetchGuildMembers($this->config['app']['guild_url']);

        if (empty($members)) {
            return 0;
        }

        $memberModel = new GuildMember($this->database->connection());
        $memberModel->sync($members);

        $tracker = new LevelTracker($this->database->connection());
        $tracker->syncWeek($members);

        return count($members);
    }
}
