<?php require BASE_PATH . '/app/Views/partials/game_layout_start.php'; ?>
<h2>Tribos</h2>
<form method="post" action="<?= url('tribes/create') ?>" class="card">
<input name="name" placeholder="Nome da Tribo" required>
<input name="tag" maxlength="5" placeholder="TAG" required>
<button>Criar tribo</button>
</form>
<table><tr><th>Tribo</th><th>Membros</th><th>Pontos</th><th></th></tr>
<?php foreach ($tribes as $tribe): ?>
<tr><td>[<?= e($tribe['tag']) ?>] <?= e($tribe['name']) ?></td><td><?= (int)$tribe['members'] ?></td><td><?= (int)$tribe['points'] ?></td>
<td><form method="post" action="<?= url('tribes/join') ?>"><input type="hidden" name="tribe_id" value="<?= (int)$tribe['id'] ?>"><button>Entrar</button></form></td></tr>
<?php endforeach; ?>
</table>
<?php if ($myTribe): ?>
<h3>Chat interno - <?= e($myTribe['name']) ?></h3>
<div class="chat-box"><?php foreach ($chat as $m): ?><p><strong><?= e($m['username']) ?>:</strong> <?= e($m['message']) ?></p><?php endforeach; ?></div>
<form method="post" action="<?= url('tribes/chat') ?>"><input name="message" placeholder="Mensagem" required><button>Enviar</button></form>
<?php endif; ?>
<?php require BASE_PATH . '/app/Views/partials/game_layout_end.php'; ?>
