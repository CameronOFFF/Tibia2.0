<?php

declare(strict_types=1);

namespace Controllers;

use Models\LevelTracker;
use Models\ReportExporter;

class ReportsController extends BaseController
{
    public function index(): void
    {
        $this->requireAuth();
        $files = glob(BASE_PATH . '/exports/*.xlsx') ?: [];
        rsort($files);
        $this->render('reports/index', compact('files'));
    }

    public function exportWeekly(): void
    {
        $user = $this->requireRole(['OWNER', 'ADMIN', 'LEADER']);

        $tracker = new LevelTracker($this->database->connection());
        $rows = $tracker->all();

        $exporter = new ReportExporter();
        $filename = $exporter->exportWeekly($rows, BASE_PATH . '/exports');

        $this->log->add($user['id'], 'export_weekly', 'Export semanal gerado: ' . $filename);
        redirect('reports/index');
    }
}
