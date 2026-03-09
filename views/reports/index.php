<div class="title-row">
  <h1>Relatórios Semanais</h1>
  <a class="btn" href="index.php?route=reports/exportWeekly">Exportar Agora</a>
</div>
<ul>
  <?php foreach ($files as $file): $name = basename($file); ?>
    <li><a href="exports/<?= e($name) ?>" target="_blank"><?= e($name) ?></a></li>
  <?php endforeach; ?>
</ul>
