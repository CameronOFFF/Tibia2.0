<section class="hero" data-auto-refresh="300">
  <div>
    <h1>Guild Members</h1>
    <p class="muted">Atualização automática a cada 5 minutos. Última sincronização: <strong><?= e($summary['last_sync'] ?? 'nunca') ?></strong></p>
  </div>
  <div class="hero-actions">
    <span class="pill success">Auto-sync ativo</span>
    <a class="btn" href="index.php?route=guild/sync">Sincronizar agora</a>
  </div>
</section>

<section class="cards compact">
  <article class="card stat"><h3>Total de membros</h3><p><?= (int) ($summary['total'] ?? 0) ?></p></article>
  <article class="card stat"><h3>Online agora</h3><p><?= (int) ($summary['online'] ?? 0) ?></p></article>
  <article class="card stat"><h3>Offline agora</h3><p><?= max(0, (int) ($summary['total'] ?? 0) - (int) ($summary['online'] ?? 0)) ?></p></article>
</section>

<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Nome</th><th>Vocação</th><th>Level</th><th>Status</th><th>Atualizado</th></tr>
    </thead>
    <tbody>
      <?php foreach ($members as $member): ?>
        <tr>
          <td><?= e($member['name']) ?></td>
          <td><?= e($member['vocation']) ?></td>
          <td><strong><?= (int) $member['level'] ?></strong></td>
          <td>
            <span class="pill <?= $member['online_status'] === 'online' ? 'success' : 'danger' ?>">
              <?= e($member['online_status']) ?>
            </span>
          </td>
          <td><?= e($member['last_update']) ?></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>
