<?php

declare(strict_types=1);

namespace Controllers;

use Models\GuildMember;
use Models\LevelTracker;
use Models\TibiaScraper;

class GuildController extends BaseController
{
    public function index(): void
    {
        $this->requireAuth();
        $model = new GuildMember($this->database->connection());
        $members = $model->all();
        $this->render('guild/index', compact('members'));
    }

    public function sync(): void
    {
        $user = $this->requireRole(['OWNER', 'ADMIN', 'LEADER']);

        $scraper = new TibiaScraper();
        $members = $scraper->fetchGuildMembers($this->config['app']['guild_url']);

        $memberModel = new GuildMember($this->database->connection());
        $memberModel->sync($members);

        $tracker = new LevelTracker($this->database->connection());
        $tracker->syncWeek($members);

        $this->log->add($user['id'], 'guild_sync', 'Sincronização da guilda executada manualmente');

        redirect('guild/index');
    }
}
