<?php

declare(strict_types=1);

namespace Controllers;

class AuthController extends BaseController
{
    public function login(): void
    {
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            check_csrf();
            $username = trim($_POST['username'] ?? '');
            $password = $_POST['password'] ?? '';

            if ($this->auth->attempt($username, $password)) {
                $user = $this->auth->user();
                $this->log->add($user['id'], 'login', 'Login realizado com sucesso');
                redirect('dashboard/index');
            }

            $error = 'Usuário ou senha inválidos.';
            $this->render('auth/login', compact('error'));
            return;
        }

        $this->render('auth/login');
    }

    public function logout(): void
    {
        $user = $this->auth->user();
        if ($user) {
            $this->log->add($user['id'], 'logout', 'Logout realizado');
        }
        $this->auth->logout();
        redirect('auth/login');
    }
}
