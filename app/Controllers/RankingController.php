<?php

declare(strict_types=1);

namespace App\Controllers;

use App\Core\Controller;
use App\Models\Tribe;
use App\Models\User;
use App\Models\Village;

final class RankingController extends Controller
{
    public function index(): void
    {
        requireAuth();
        $this->view('rankings/index', [
            'village' => (new Village())->getMainVillage((int)currentUserId()),
            'players' => (new User())->rankingsByPoints(),
            'tribes' => (new Tribe())->allWithPoints(),
            'wins' => (new User())->rankingsByWins(),
        ]);
    }
}
