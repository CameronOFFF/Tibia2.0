<?php $user = $_SESSION['user'] ?? null; ?>
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title><?= e($app['name']) ?></title>
  <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
<div class="app">
  <?php if ($user): ?>
  <aside class="sidebar">
    <h2>Never Duality!</h2>
    <nav>
      <a href="index.php?route=dashboard/index">Dashboard</a>
      <a href="index.php?route=guild/index">Guild Members</a>
      <a href="index.php?route=level/index">Level Tracker</a>
      <a href="index.php?route=lists/index&type=hunted">Hunted List</a>
      <a href="index.php?route=lists/index&type=friend">Friend List</a>
      <a href="index.php?route=lists/index&type=neutral">Neutral List</a>
      <a href="index.php?route=lists/index&type=ally">Ally List</a>
      <a href="index.php?route=lists/index&type=guild">Guild Watch</a>
      <a href="index.php?route=reports/index">Relatórios</a>
      <a href="index.php?route=logs/index">Logs</a>
      <a href="index.php?route=settings/index">Configurações</a>
      <a href="index.php?route=auth/logout">Logout</a>
    </nav>
  </aside>
  <?php endif; ?>
  <main class="content">
