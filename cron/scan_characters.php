<?php

declare(strict_types=1);

require __DIR__ . '/bootstrap.php';

$scraper = new Models\TibiaScraper();
$scanModel = new Models\CharacterScan($pdo);
$log = new Models\Log($pdo);

$names = [];
foreach (['hunted_list', 'friend_list', 'neutral_list', 'ally_list'] as $table) {
    $rows = $pdo->query("SELECT character_name FROM {$table}")->fetchAll();
    foreach ($rows as $row) {
        $names[] = $row['character_name'];
    }
}

$rows = $pdo->query('SELECT name AS character_name FROM guild_members')->fetchAll();
foreach ($rows as $row) {
    $names[] = $row['character_name'];
}

$names = array_unique(array_filter(array_map('trim', $names)));
$count = 0;

foreach ($names as $name) {
    $url = sprintf($config['app']['character_url'], urlencode($name));
    $character = $scraper->fetchCharacter($url);
    if ($character) {
        $scanModel->save($character);
        $count++;
    }
}

$log->add(null, 'cron_character_scan', 'Scanner executado: ' . $count . ' personagens');
echo 'Character scan done: ' . $count . PHP_EOL;
