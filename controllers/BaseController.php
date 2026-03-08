<?php

declare(strict_types=1);

namespace Controllers;

use Config\Database;
use Models\Auth;
use Models\Log;

abstract class BaseController
{
    protected Auth $auth;
    protected Log $log;

    public function __construct(protected readonly Database $database, protected readonly array $config)
    {
        $pdo = $this->database->connection();
        $this->auth = new Auth($pdo);
        $this->log = new Log($pdo);
    }

    protected function render(string $view, array $data = []): void
    {
        extract($data, EXTR_SKIP);
        $app = $this->config['app'];
        require BASE_PATH . '/views/layouts/header.php';
        require BASE_PATH . '/views/' . $view . '.php';
        require BASE_PATH . '/views/layouts/footer.php';
    }

    protected function requireAuth(): array
    {
        $user = $this->auth->user();
        if (!$user) {
            redirect('auth/login');
        }

        return $user;
    }

    protected function requireRole(array $roles): array
    {
        $user = $this->requireAuth();
        if (!in_array($user['role'], $roles, true)) {
            http_response_code(403);
            exit('Acesso negado.');
        }

        return $user;
    }
}
