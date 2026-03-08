<?php

declare(strict_types=1);

require __DIR__ . '/bootstrap.php';

$scraper = new Models\TibiaScraper();
$memberModel = new Models\GuildMember($pdo);
$tracker = new Models\LevelTracker($pdo);
$log = new Models\Log($pdo);

$members = $scraper->fetchGuildMembers($config['app']['guild_url']);
$memberModel->sync($members);
$tracker->syncWeek($members);
$log->add(null, 'cron_guild_update', 'Atualização de membros executada');

echo 'Guild update done: ' . count($members) . PHP_EOL;
