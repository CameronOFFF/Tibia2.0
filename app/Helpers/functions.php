<?php

declare(strict_types=1);

function currentUserId(): ?int
{
    return $_SESSION['user_id'] ?? null;
}

function requireAuth(): void
{
    if (!currentUserId()) {
        header('Location: ' . BASE_URL . 'login');
        exit;
    }
}

function e(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES, 'UTF-8');
}
