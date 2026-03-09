<?php
$labels = ['hunted' => 'Hunted', 'friend' => 'Friend', 'neutral' => 'Neutral', 'ally' => 'Ally', 'guild' => 'Guild Watch'];
$isGuild = $type === 'guild';
?>
<h1><?= e($labels[$type] ?? 'Lista') ?> List</h1>
<section class="panel">
  <form method="post" action="index.php?route=lists/save" class="grid-form">
    <input type="hidden" name="csrf_token" value="<?= e(csrf_token()) ?>">
    <input type="hidden" name="type" value="<?= e($type) ?>">
    <input type="hidden" name="id" value="<?= (int) ($editItem['id'] ?? 0) ?>">

    <?php if ($isGuild): ?>
      <label>Guild <input type="text" name="guild_name" value="<?= e($editItem['guild_name'] ?? '') ?>" required></label>
      <label>World <input type="text" name="world" value="<?= e($editItem['world'] ?? '') ?>"></label>
    <?php else: ?>
      <label>Character <input type="text" name="character_name" value="<?= e($editItem['character_name'] ?? '') ?>" required></label>
      <label>Guild <input type="text" name="guild" value="<?= e($editItem['guild'] ?? '') ?>"></label>
      <label>Reason <input type="text" name="reason" value="<?= e($editItem['reason'] ?? '') ?>"></label>
    <?php endif; ?>

    <label>Observação <input type="text" name="notes" value="<?= e($editItem['notes'] ?? '') ?>"></label>
    <button type="submit"><?= $editItem ? 'Atualizar' : 'Adicionar' ?></button>
  </form>
</section>

<table>
  <tr>
    <th>Nome</th><th>Guild/World</th><th>Motivo</th><th>Obs</th><th>Data</th><th>Ações</th>
  </tr>
  <?php foreach ($items as $item): ?>
    <tr>
      <td><?= e($item['character_name'] ?? $item['guild_name']) ?></td>
      <td><?= e($item['guild'] ?? $item['world'] ?? '') ?></td>
      <td><?= e($item['reason'] ?? '-') ?></td>
      <td><?= e($item['notes'] ?? '') ?></td>
      <td><?= e($item['created_at'] ?? '-') ?></td>
      <td>
        <a class="btn-link" href="index.php?route=lists/index&type=<?= e($type) ?>&edit=<?= (int) $item['id'] ?>">Editar</a>
        <form method="post" action="index.php?route=lists/delete" class="inline-form">
          <input type="hidden" name="csrf_token" value="<?= e(csrf_token()) ?>">
          <input type="hidden" name="type" value="<?= e($type) ?>">
          <input type="hidden" name="id" value="<?= (int) $item['id'] ?>">
          <button type="submit" class="danger">Excluir</button>
        </form>
      </td>
    </tr>
  <?php endforeach; ?>
</table>
