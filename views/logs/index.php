<h1>Logs do Sistema</h1>
<table>
  <tr><th>Data</th><th>Usuário</th><th>Ação</th><th>Detalhes</th></tr>
  <?php foreach ($logs as $log): ?>
    <tr>
      <td><?= e($log['created_at']) ?></td>
      <td><?= e($log['username'] ?? 'sistema') ?></td>
      <td><?= e($log['action']) ?></td>
      <td><?= e($log['details']) ?></td>
    </tr>
  <?php endforeach; ?>
</table>
