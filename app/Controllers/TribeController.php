<?php

declare(strict_types=1);

namespace App\Controllers;

use App\Core\Controller;
use App\Models\Tribe;
use App\Models\Village;

final class TribeController extends Controller
{
    public function index(): void
    {
        requireAuth();
        $tribeModel = new Tribe();
        $village = (new Village())->getMainVillage((int) currentUserId());
        $myTribe = $tribeModel->myTribe((int)currentUserId());
        $this->view('tribes/index', [
            'village' => $village,
            'tribes' => $tribeModel->allWithPoints(),
            'myTribe' => $myTribe,
            'chat' => $myTribe ? $tribeModel->chatMessages((int)$myTribe['id']) : [],
        ]);
    }

    public function create(): void
    {
        requireAuth();
        (new Tribe())->create((int)currentUserId(), trim($_POST['name']), strtoupper(trim($_POST['tag'])));
        $this->redirect('tribes');
    }

    public function join(): void
    {
        requireAuth();
        (new Tribe())->join((int)$_POST['tribe_id'], (int)currentUserId());
        $this->redirect('tribes');
    }

    public function chat(): void
    {
        requireAuth();
        $tribeModel = new Tribe();
        $myTribe = $tribeModel->myTribe((int)currentUserId());
        if ($myTribe && trim($_POST['message']) !== '') {
            $tribeModel->postChat((int)$myTribe['id'], (int)currentUserId(), trim($_POST['message']));
        }
        $this->redirect('tribes');
    }
}
