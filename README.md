# Macho Never Duality - By: Nerd Din

Aplicativo Windows em Python para monitorar HP/MP do Tibia, com foco em **leitura por memória** (com fallback por imagem das barras), alertas configuráveis e envio de tecla quando regras disparam.

## Recursos

- Detecção de janelas com título `Tibia - NOME_PERSONAGEM`.
- Captura apenas da área da janela do jogo.
- Leitura de HP/MP atual por múltiplos endereços de memória.
- Cálculo correto de percentual usando:
  - **valor atual da memória** (HP/MP atual)
  - **HP Máxima/MP Máxima** definidas na UI/config
- Debug de memória no console/log para validar leituras em tempo real.
- Fallback opcional por análise de barra (HSV + ROI), útil para calibração.
- Regras/macros de alerta (Rings/Amulets e Healing), com:
  - condição (`<=`)
  - threshold
  - som
  - cooldown por regra
  - envio de tecla para janela do Tibia
- UI com progress bars, status (`OK/Atenção/Crítico`), FPS, lista de macros e botões para **Adicionar Macro** / **Deletar Selecionado**.
- Log em console e arquivo.

## Instalação

> Requer Windows + Python 3.11+

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuração

Edite `config.json`:

- `max_hp` e `max_mp`: valores máximos do personagem.
- `hp_addresses` e `mp_addresses`: lista de endereços (hex) para leitura atual.
- `debug_memory`: mostra debug com candidatos de memória e valor escolhido.
- `hp_bar_roi` e `mp_bar_roi`: coordenadas relativas à janela do Tibia (`x,y,w,h`).
- `*_hsv_lower` e `*_hsv_upper`: ajuste de cor para fallback por imagem.
- `rules`: regras de alerta e tecla.

## Calibrar ROI

1. Selecione janela Tibia.
2. Clique **Iniciar**.
3. Clique **Calibrar ROIs**.
4. Arraste o retângulo na imagem e confirme com ENTER.
5. Escolha se a ROI é de HP (Sim) ou MP (Não).
6. Salve configuração.

Também é possível editar manualmente os valores no `config.json`.

## Criar/remover macros

- **Adicionar Macro**: define nome, tipo (HP/MP), percentual, tecla (F1..F12 etc.), mensagem, cooldown e som.
- **Deletar Selecionado**: remove o macro destacado na lista.
- Clique **Salvar config** para persistir os macros no `config.json`.

## Rodar

```bash
python main.py
```

## Observações

- Se a janela estiver minimizada, o monitor pausa automaticamente.
- Se leitura de memória falhar para todos os endereços, o app tenta leitura por imagem da barra.
- Foi corrigido o erro do `mss` em thread (`'_thread._local' has no attribute 'srcdc'`) criando capturador por thread.
- `pywin32` e leitura de memória dependem de permissões do processo.
