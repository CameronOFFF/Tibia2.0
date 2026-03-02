<?php require BASE_PATH . '/app/Views/partials/header.php'; ?>
<form class="auth-box" method="post" action="/login">
    <h2>Login</h2>
    <?php if (!empty($_SESSION['error'])): ?><p><?= e($_SESSION['error']); unset($_SESSION['error']); ?></p><?php endif; ?>
    <input name="email" type="email" placeholder="E-mail" required>
    <input name="password" type="password" placeholder="Senha" required>
    <button type="submit">Entrar</button>
</form>
<?php require BASE_PATH . '/app/Views/partials/footer.php'; ?>
