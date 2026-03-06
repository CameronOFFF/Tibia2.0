<?php require BASE_PATH . '/app/Views/partials/game_layout_start.php'; ?>
<h2>Quartel</h2>
<table><tr><th>Unidade</th><th>Ataque</th><th>Defesa</th><th>Velocidade</th><th>Custo</th><th>Treinar</th></tr>
<?php foreach ($troops as $troop): ?>
<tr>
<td><?= e($troop['name']) ?></td><td><?= (int)$troop['attack'] ?></td><td><?= (int)$troop['defense'] ?></td><td><?= (int)$troop['speed'] ?></td>
<td><?= (int)$troop['cost_wood'] ?>/<?= (int)$troop['cost_clay'] ?>/<?= (int)$troop['cost_iron'] ?></td>
<td><form method="post" action="<?= url('train') ?>"><input type="hidden" name="troop_id" value="<?= (int)$troop['id'] ?>"><input name="qty" type="number" min="1" value="10"><button>Treinar</button></form></td>
</tr>
<?php endforeach; ?>
</table>
<h3>Tropas atuais</h3>
<ul><?php foreach ($owned as $row): ?><li><?= e($row['name']) ?>: <?= (int)$row['quantity'] ?></li><?php endforeach; ?></ul>
<h3>Fila de treino</h3>
<ul><?php foreach ($queue as $row): ?><li><?= e($row['name']) ?> x<?= (int)$row['quantity'] ?> (<?= e($row['finish_at']) ?>)</li><?php endforeach; ?></ul>
<?php require BASE_PATH . '/app/Views/partials/game_layout_end.php'; ?>
