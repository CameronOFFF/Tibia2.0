<h1>Dashboard da Guilda</h1>
<div class="cards">
  <article class="card"><h3>Membros da guilda</h3><p><?= (int) $stats['guild_members'] ?></p></article>
  <article class="card"><h3>Hunted monitorados</h3><p><?= (int) $stats['hunted_total'] ?></p></article>
  <article class="card"><h3>Hunted online</h3><p><?= (int) $stats['hunted_online'] ?></p></article>
  <article class="card"><h3>Guild inimiga online</h3><p><?= (int) $stats['enemy_guild_online'] ?></p></article>
  <article class="card"><h3>Friends online</h3><p><?= (int) $stats['friends_online'] ?></p></article>
  <article class="card"><h3>Neutrals online</h3><p><?= (int) $stats['neutrals_online'] ?></p></article>
  <article class="card"><h3>Players online agora</h3><p><?= (int) $stats['players_online_now'] ?></p></article>
</div>

<section class="panel">
  <h2>Alertas</h2>
  <?php if (empty($alerts)): ?><p>Sem alertas no momento.</p><?php endif; ?>
  <?php foreach ($alerts as $alert): ?><p class="alert"><?= e($alert) ?></p><?php endforeach; ?>
</section>

<section class="panel">
  <h2>Top level ups semanais</h2>
  <table>
    <tr><th>Nome</th><th>Level Atual</th><th>Level Up</th></tr>
    <?php foreach (array_slice($ups, 0, 10) as $up): ?>
      <tr><td><?= e($up['character_name']) ?></td><td><?= (int) $up['level_current'] ?></td><td>+<?= (int) $up['level_gain'] ?></td></tr>
    <?php endforeach; ?>
  </table>
</section>
