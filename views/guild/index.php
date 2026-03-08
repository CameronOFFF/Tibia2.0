<div class="title-row">
  <h1>Guild Members</h1>
  <a class="btn" href="index.php?route=guild/sync">Sincronizar agora</a>
</div>
<table>
  <tr><th>Nome</th><th>Vocação</th><th>Level</th><th>Status</th><th>Atualizado</th></tr>
  <?php foreach ($members as $member): ?>
    <tr>
      <td><?= e($member['name']) ?></td>
      <td><?= e($member['vocation']) ?></td>
      <td><?= (int) $member['level'] ?></td>
      <td><?= e($member['online_status']) ?></td>
      <td><?= e($member['last_update']) ?></td>
    </tr>
  <?php endforeach; ?>
</table>
