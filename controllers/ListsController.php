<?php

declare(strict_types=1);

namespace Controllers;

use Models\WatchList;

class ListsController extends BaseController
{
    public function index(): void
    {
        $this->requireAuth();
        $type = $_GET['type'] ?? 'hunted';
        $model = new WatchList($this->database->connection());
        $items = $model->all($type);
        $editItem = null;

        if (isset($_GET['edit'])) {
            $editItem = $model->find($type, (int) $_GET['edit']);
        }

        $this->render('lists/index', compact('items', 'type', 'editItem'));
    }

    public function save(): void
    {
        $user = $this->requireRole(['OWNER', 'ADMIN']);
        check_csrf();
        $type = $_POST['type'] ?? 'hunted';
        $model = new WatchList($this->database->connection());

        if (!empty($_POST['id'])) {
            $model->update($type, (int) $_POST['id'], $_POST);
            $this->log->add($user['id'], 'list_update', 'Atualizou item da lista: ' . $type);
        } else {
            $payload = $_POST;
            $payload['added_by'] = $user['username'];
            $model->create($type, $payload);
            $this->log->add($user['id'], 'list_create', 'Adicionou item na lista: ' . $type);
        }

        redirect('lists/index&type=' . $type);
    }

    public function delete(): void
    {
        $user = $this->requireRole(['OWNER', 'ADMIN']);
        check_csrf();
        $type = $_POST['type'] ?? 'hunted';
        $id = (int) ($_POST['id'] ?? 0);

        $model = new WatchList($this->database->connection());
        $model->delete($type, $id);

        $this->log->add($user['id'], 'list_delete', 'Removeu item da lista: ' . $type);
        redirect('lists/index&type=' . $type);
    }
}
