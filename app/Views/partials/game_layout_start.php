<?php require BASE_PATH . '/app/Views/partials/header.php'; ?>
<div class="topbar">
    <strong><?= e($village['name']) ?></strong>
    <span>Coordenadas: (<?= (int)$village['coord_x'] ?>|<?= (int)$village['coord_y'] ?>)</span>
    <span>Madeira: <?= (int)$village['wood'] ?></span>
    <span>Argila: <?= (int)$village['clay'] ?></span>
    <span>Ferro: <?= (int)$village['iron'] ?></span>
    <a href="/logout">Sair</a>
</div>
<div class="container">
    <aside>
        <a href="/dashboard">Aldeia</a>
        <a href="/barracks">Quartel</a>
        <a href="/map">Mapa</a>
        <a href="/reports">Relatórios</a>
        <a href="/tribes">Tribos</a>
        <a href="/rankings">Rankings</a>
    </aside>
    <main>
