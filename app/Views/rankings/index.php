<?php require BASE_PATH . '/app/Views/partials/game_layout_start.php'; ?>
<h2>Rankings</h2>
<div class="grid2">
<section><h3>Jogadores por pontos</h3><ol><?php foreach ($players as $row): ?><li><?= e($row['username']) ?> - <?= (int)$row['points'] ?></li><?php endforeach; ?></ol></section>
<section><h3>Tribos</h3><ol><?php foreach ($tribes as $row): ?><li>[<?= e($row['tag']) ?>] <?= e($row['name']) ?> - <?= (int)$row['points'] ?></li><?php endforeach; ?></ol></section>
<section><h3>Batalhas vencidas</h3><ol><?php foreach ($wins as $row): ?><li><?= e($row['username']) ?> - <?= (int)$row['wins'] ?></li><?php endforeach; ?></ol></section>
</div>
<?php require BASE_PATH . '/app/Views/partials/game_layout_end.php'; ?>
