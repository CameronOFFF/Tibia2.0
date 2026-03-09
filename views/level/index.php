<section class="hero" data-auto-refresh="300">
  <div>
    <h1>Level Tracker Semanal</h1>
    <p class="muted">Lista completa dos membros da guilda com evolução semanal. Última sincronização: <strong><?= e($summary['last_sync'] ?? 'nunca') ?></strong></p>
  </div>
  <div class="hero-actions">
    <span class="pill success">Atualização automática 5 min</span>
  </div>
</section>

<section class="cards compact">
  <article class="card stat"><h3>Membros no tracker</h3><p><?= count($rows) ?></p></article>
  <article class="card stat"><h3>Online agora</h3><p><?= (int) ($summary['online'] ?? 0) ?></p></article>
  <article class="card stat"><h3>Uparam na semana</h3><p><?= count(array_filter($rows, static fn($r) => (int)$r['level_gain'] > 0)) ?></p></article>
</section>

<div class="table-wrap">
  <table>
    <thead>
      <tr><th>Nome</th><th>Vocação</th><th>Start</th><th>Atual</th><th>+Níveis</th><th>% Evo</th></tr>
    </thead>
    <tbody>
      <?php foreach ($rows as $row):
        $start = max(1, (int) $row['level_start_week']);
        $current = (int) $row['level_current'];
        $gain = (int) $row['level_gain'];
        $percent = round(($gain / $start) * 100, 1);
      ?>
        <tr>
          <td><?= e($row['character_name']) ?></td>
          <td><?= e($row['vocation']) ?></td>
          <td><?= $start ?></td>
          <td><strong><?= $current ?></strong></td>
          <td><span class="gain <?= $gain > 0 ? 'positive' : '' ?>"><?= $gain > 0 ? '+' : '' ?><?= $gain ?></span></td>
          <td><?= $percent ?>%</td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>
