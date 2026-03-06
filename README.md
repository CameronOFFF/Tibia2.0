# Tibia 2.0 (Estratégia Browser Game)

Projeto inicial completo inspirado em Tribal Wars, usando **PHP 8+, MySQL, MVC e PDO**.

## 1) Estrutura de pastas

```text
Tibia2.0/
├─ app/
│  ├─ Controllers/
│  ├─ Core/
│  ├─ Helpers/
│  ├─ Models/
│  ├─ Services/
│  └─ Views/
├─ assets/css/
├─ config/config.php
├─ database/schema.sql
├─ public/
│  ├─ .htaccess
│  └─ index.php
└─ .htaccess
```

## 2) Funcionalidades implementadas

- Cadastro/Login/Logout com `password_hash/password_verify` e sessão.
- Criação automática de aldeia inicial com coordenadas aleatórias.
- Recursos (madeira, argila, ferro) com produção offline por timestamp.
- Edifícios com nível, custo exponencial, tempo e fila de construção.
- Tropas com status/custos/tempo e fila de treinamento.
- Mapa 100x100 com aldeias e envio de ataque.
- Sistema de batalha automático com saque e relatórios no banco.
- Tribos (criar, entrar, ranking e chat interno).
- Rankings por pontos, tribos e vitórias em batalha.

## 3) Script SQL completo

Arquivo: `database/schema.sql`.

Inclui tabelas obrigatórias:

- `users`
- `villages`
- `buildings`
- `troops`
- `village_troops`
- `construction_queue`
- `training_queue`
- `attacks`
- `reports`
- `tribes`
- `tribe_members`

E também `tribe_chat` para chat interno.

## 4) Como rodar no XAMPP

1. Copie a pasta para `htdocs`:
   - `C:\xampp\htdocs\Tibia2.0`
2. Inicie Apache e MySQL no XAMPP Control Panel.
3. Crie o banco importando `database/schema.sql` pelo phpMyAdmin.
4. Ajuste `config/config.php` (host, banco, usuário, senha).
   - `BASE_URL` pode ficar vazio (`''`) para detectar automaticamente o subdiretório (ex.: `/tribal/public/`).
5. Acesse no navegador:
   - `http://localhost/Tibia2.0/public/`

## 5) Melhorias futuras sugeridas

- CSRF token e rate-limit para formulários críticos.
- Fila de tarefas via cron/worker para processar ataques em escala.
- Balanceamento avançado de combate por tipo de unidade.
- Sistema de mensagens privadas e diplomacia entre tribos.
- Multi-aldeias por jogador com conquista.
- Testes automatizados (PHPUnit) e integração CI.

## 6) Preparado para expansão

A arquitetura está separada por domínio (Controllers/Models/Services), facilitando adicionar:

- **Heróis**: tabela `heroes`, equipamentos e habilidades.
- **Eventos globais**: invasões, bônus de produção, temporadas.
- **Mundos**: servidor com configurações por mundo/velocidade.
- **Sistema premium**: fila extra, temas, QoL.

