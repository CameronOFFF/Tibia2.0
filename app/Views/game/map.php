<?php require BASE_PATH . '/app/Views/partials/game_layout_start.php'; ?>
<h2>Mapa Mundial (100x100)</h2>
<table>
<tr><th>Aldeia</th><th>Dono</th><th>Coord</th><th>Pontos</th><th>Ataque</th></tr>
<?php foreach ($villages as $item): ?>
<tr>
<td><?= e($item['name']) ?></td><td><?= e($item['username']) ?></td><td>(<?= (int)$item['coord_x'] ?>|<?= (int)$item['coord_y'] ?>)</td><td><?= (int)$item['points'] ?></td>
<td>
<?php if ((int)$item['id'] !== (int)$village['id']): ?>
<form method="post" action="<?= url('attack') ?>">
<input type="hidden" name="target_village_id" value="<?= (int)$item['id'] ?>">
<input type="number" name="spear" min="1" value="1">
<button>Enviar ataque</button>
</form>
<?php endif; ?>
</td>
</tr>
<?php endforeach; ?>
</table>
<?php require BASE_PATH . '/app/Views/partials/game_layout_end.php'; ?>
