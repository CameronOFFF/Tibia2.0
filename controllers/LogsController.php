<?php

declare(strict_types=1);

namespace Controllers;

class LogsController extends BaseController
{
    public function index(): void
    {
        $this->requireRole(['OWNER', 'ADMIN', 'LEADER']);
        $logs = $this->log->latest(200);
        $this->render('logs/index', compact('logs'));
    }
}
