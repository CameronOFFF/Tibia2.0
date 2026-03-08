<h1>Level Tracker Semanal</h1>
<table>
  <tr><th>Nome</th><th>Vocação</th><th>Level Atual</th><th>Level Up na Semana</th><th>Início</th></tr>
  <?php foreach ($rows as $row): ?>
    <tr>
      <td><?= e($row['character_name']) ?></td>
      <td><?= e($row['vocation']) ?></td>
      <td><?= (int) $row['level_current'] ?></td>
      <td>+<?= (int) $row['level_gain'] ?></td>
      <td><?= e($row['week_start_date']) ?></td>
    </tr>
  <?php endforeach; ?>
</table>
