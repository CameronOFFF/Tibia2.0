# Never Duality Control Panel (PHP + MySQL)

Painel web MVC simples para gerenciamento da guilda **Never Duality!**.

## Stack
- PHP 8+
- MySQL
- HTML5/CSS/JS
- Web scraping com `file_get_contents` + DOMDocument

## Estrutura
```
/config
/controllers
/models
/views
/assets/css
/assets/js
/cron
/exports
/database
index.php
```

## Setup local (XAMPP)
1. Crie banco e tabelas executando `database/schema.sql` no phpMyAdmin.
2. Ajuste `config/config.php`.
3. Sirva em `http://localhost/Tibia2.0`.
4. Login inicial:
   - usuário: `owner`
   - senha: `owner123`

## Cron interno
Agende no Windows Task Scheduler ou cron:
- A cada 5 min: `php /caminho/Tibia2.0/cron/update_guild.php`
- A cada 30 min: `php /caminho/Tibia2.0/cron/scan_characters.php`
- A cada 7 dias: `php /caminho/Tibia2.0/cron/weekly_reset.php`

## Excel
Se `PhpSpreadsheet` estiver instalado via Composer, exporta `.xlsx` nativo. Sem biblioteca, usa fallback CSV salvo com extensão `.xlsx`.
