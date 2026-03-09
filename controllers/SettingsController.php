<?php

declare(strict_types=1);

namespace Controllers;

class SettingsController extends BaseController
{
    public function index(): void
    {
        $this->requireRole(['OWNER', 'ADMIN']);
        $this->render('settings/index');
    }
}
