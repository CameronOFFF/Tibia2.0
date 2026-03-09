<?php

declare(strict_types=1);

namespace Models;

use PDO;

class Dashboard
{
    public function __construct(private PDO $pdo)
    {
    }

    public function stats(): array
    {
        return [
            'guild_members' => (int) $this->pdo->query('SELECT COUNT(*) FROM guild_members')->fetchColumn(),
            'hunted_total' => (int) $this->pdo->query('SELECT COUNT(*) FROM hunted_list')->fetchColumn(),
            'hunted_online' => (int) $this->pdo->query("SELECT COUNT(*) FROM character_scans cs JOIN hunted_list hl ON hl.character_name = cs.name WHERE cs.status = 'online'")->fetchColumn(),
            'enemy_guild_online' => (int) $this->pdo->query("SELECT COUNT(*) FROM character_scans cs JOIN guild_watch gw ON gw.guild_name = cs.guild_name WHERE cs.status = 'online'")->fetchColumn(),
            'friends_online' => (int) $this->pdo->query("SELECT COUNT(*) FROM character_scans cs JOIN friend_list fl ON fl.character_name = cs.name WHERE cs.status = 'online'")->fetchColumn(),
            'neutrals_online' => (int) $this->pdo->query("SELECT COUNT(*) FROM character_scans cs JOIN neutral_list nl ON nl.character_name = cs.name WHERE cs.status = 'online'")->fetchColumn(),
            'players_online_now' => (int) $this->pdo->query("SELECT COUNT(*) FROM guild_members WHERE online_status='online'")->fetchColumn(),
        ];
    }
}
