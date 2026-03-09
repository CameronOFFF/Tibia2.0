<section class="panel login-panel">
  <h1>Login - Never Duality</h1>
  <?php if (!empty($error)): ?><p class="alert danger"><?= e($error) ?></p><?php endif; ?>
  <form method="post" action="index.php?route=auth/login">
    <input type="hidden" name="csrf_token" value="<?= e(csrf_token()) ?>">
    <label>Usuário
      <input type="text" name="username" required>
    </label>
    <label>Senha
      <input type="password" name="password" required>
    </label>
    <button type="submit">Entrar</button>
  </form>
</section>
