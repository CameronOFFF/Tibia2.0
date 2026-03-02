<?php

declare(strict_types=1);

function currentUserId(): ?int
{
    return $_SESSION['user_id'] ?? null;
}

function baseUrl(): string
{
    $configured = defined('BASE_URL') ? trim((string) BASE_URL) : '';
    if ($configured !== '') {
        return rtrim($configured, '/') . '/';
    }

    $scriptName = str_replace('\\', '/', $_SERVER['SCRIPT_NAME'] ?? '/index.php');
    $dir = rtrim(dirname($scriptName), '/');
    if ($dir === '' || $dir === '.') {
        return '/';
    }

    return $dir . '/';
}

function url(string $path = ''): string
{
    return baseUrl() . ltrim($path, '/');
}

function requireAuth(): void
{
    if (!currentUserId()) {
        header('Location: ' . url('login'));
        exit;
    }
}

function e(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES, 'UTF-8');
}
