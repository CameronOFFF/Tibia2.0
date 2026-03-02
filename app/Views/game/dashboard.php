<?php require BASE_PATH . '/app/Views/partials/game_layout_start.php'; ?>
<h2>Painel da Aldeia</h2>
<form method="post" action="<?= url('village/rename') ?>">
    <input name="name" value="<?= e($village['name']) ?>" required>
    <button>Renomear</button>
</form>
<h3>Edifícios</h3>
<table>
<tr><th>Edifício</th><th>Nível</th><th>Ação</th></tr>
<?php foreach ($buildings as $key => $building): ?>
<tr>
<td><?= e($key) ?></td>
<td><?= (int)$building['level'] ?></td>
<td>
<form method="post" action="<?= url('build') ?>">
<input type="hidden" name="building_key" value="<?= e($key) ?>">
<button>Melhorar</button>
</form>
</td>
</tr>
<?php endforeach; ?>
</table>
<h3>Fila de construção</h3>
<ul><?php foreach ($constructionQueue as $item): ?><li><?= e($item['building_key']) ?> até nível <?= (int)$item['target_level'] ?> (fim <?= e($item['finish_at']) ?>)</li><?php endforeach; ?></ul>
<?php require BASE_PATH . '/app/Views/partials/game_layout_end.php'; ?>
