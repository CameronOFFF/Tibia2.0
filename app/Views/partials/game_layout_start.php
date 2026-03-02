<?php require BASE_PATH . '/app/Views/partials/header.php'; ?>
<div class="topbar">
    <strong><?= e($village['name']) ?></strong>
    <span>Coordenadas: (<?= (int)$village['coord_x'] ?>|<?= (int)$village['coord_y'] ?>)</span>
    <span>Madeira: <?= (int)$village['wood'] ?></span>
    <span>Argila: <?= (int)$village['clay'] ?></span>
    <span>Ferro: <?= (int)$village['iron'] ?></span>
    <a href="<?= url('logout') ?>">Sair</a>
</div>
<div class="container">
    <aside>
        <a href="<?= url('dashboard') ?>">Aldeia</a>
        <a href="<?= url('barracks') ?>">Quartel</a>
        <a href="<?= url('map') ?>">Mapa</a>
        <a href="<?= url('reports') ?>">Relatórios</a>
        <a href="<?= url('tribes') ?>">Tribos</a>
        <a href="<?= url('rankings') ?>">Rankings</a>
    </aside>
    <main>
