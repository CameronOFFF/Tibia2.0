<?php require BASE_PATH . '/app/Views/partials/game_layout_start.php'; ?>
<h2>Relatórios de Batalha</h2>
<?php foreach ($reports as $report): ?>
<article class="card"><h3><?= e($report['title']) ?></h3><small><?= e($report['created_at']) ?></small><p><?= e($report['content']) ?></p></article>
<?php endforeach; ?>
<?php require BASE_PATH . '/app/Views/partials/game_layout_end.php'; ?>
