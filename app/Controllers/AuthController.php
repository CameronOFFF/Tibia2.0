<?php

declare(strict_types=1);

namespace App\Controllers;

use App\Core\Controller;
use App\Models\User;
use App\Models\Village;

final class AuthController extends Controller
{
    public function home(): void
    {
        if (currentUserId()) {
            $this->redirect('dashboard');
        }
        $this->view('auth/home');
    }

    public function showRegister(): void { $this->view('auth/register'); }
    public function showLogin(): void { $this->view('auth/login'); }

    public function register(): void
    {
        $userId = (new User())->create(trim($_POST['username']), trim($_POST['email']), $_POST['password']);
        (new Village())->createStarterVillage($userId, 'Aldeia Inicial');
        $_SESSION['user_id'] = $userId;
        $this->redirect('dashboard');
    }

    public function login(): void
    {
        $user = (new User())->findByEmail(trim($_POST['email']));
        if (!$user || !password_verify($_POST['password'], $user['password_hash'])) {
            $_SESSION['error'] = 'Credenciais inválidas';
            $this->redirect('login');
        }
        $_SESSION['user_id'] = (int)$user['id'];
        $this->redirect('dashboard');
    }

    public function logout(): void
    {
        session_destroy();
        $this->redirect('login');
    }
}
