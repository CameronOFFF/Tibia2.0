<?php require BASE_PATH . '/app/Views/partials/header.php'; ?>
<form class="auth-box" method="post" action="/register">
    <h2>Cadastro</h2>
    <input name="username" placeholder="Usuário" required>
    <input name="email" type="email" placeholder="E-mail" required>
    <input name="password" type="password" placeholder="Senha" required>
    <button type="submit">Criar Conta</button>
</form>
<?php require BASE_PATH . '/app/Views/partials/footer.php'; ?>
