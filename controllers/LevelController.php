<?php

declare(strict_types=1);

namespace Controllers;

use Models\LevelTracker;

class LevelController extends BaseController
{
    public function index(): void
    {
        $this->requireAuth();
        $tracker = new LevelTracker($this->database->connection());
        $rows = $tracker->all();
        $this->render('level/index', compact('rows'));
    }
}
