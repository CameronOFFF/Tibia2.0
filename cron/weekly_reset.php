<?php

declare(strict_types=1);

require __DIR__ . '/bootstrap.php';

$tracker = new Models\LevelTracker($pdo);
$exporter = new Models\ReportExporter();
$log = new Models\Log($pdo);

$rows = $tracker->all();
$filename = $exporter->exportWeekly($rows, BASE_PATH . '/exports');
$tracker->resetWeek();
$log->add(null, 'cron_weekly_reset', 'Export e reset semanal executado: ' . $filename);

echo 'Weekly reset done: ' . $filename . PHP_EOL;
