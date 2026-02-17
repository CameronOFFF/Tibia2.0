# Tibia HP Monitor (Windows)

Aplicativo em Python para monitorar **HP/MP por imagem da tela** da janela do Tibia e disparar **alertas + envio de teclas** com base em regras.

> **Importante:** este projeto **não usa leitura de memória, DLL, nem injeção**. Apenas captura da janela, análise visual (OpenCV), UI e automação de teclas.

## Requisitos

- Windows 10/11
- Python 3.11+

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Como rodar

```bash
python main.py
```

## Fluxo de uso

1. Abra o Tibia e mantenha a interface no layout desejado.
2. No app, clique em **Atualizar** e selecione uma janela `Tibia - NOME_PERSONAGEM`.
3. Clique em **Calibrar ROIs** para definir HP e MP com seleção por retângulo.
4. (Opcional) Ajuste manualmente `x,y,w,h` das ROIs na seção manual.
5. Ajuste regras de **Rings/Amulets** e **Healing** (threshold e tecla).
6. Clique em **Iniciar**.

## Calibração de ROIs

- **Modo visual**: botão **Calibrar ROIs**, selecionar primeiro HP e depois MP.
- **Modo manual**: campos `HP ROI x,y,w,h` e `MP ROI x,y,w,h`.

As coordenadas são **relativas ao canto superior esquerdo da janela do Tibia**.

## Ajuste de HSV

No `config.json` você pode ajustar as faixas de cor:

- `hp_hsv_lower`, `hp_hsv_upper`
- `hp_hsv_lower2`, `hp_hsv_upper2` (opcional, útil para vermelho que cruza o hue 0/180)
- `hp_hsv_lower3`, `hp_hsv_upper3` (opcional, fallback adicional, ex.: verde)
- `mp_hsv_lower`, `mp_hsv_upper`

O `config.json` de exemplo já vem preparado para o layout com barra de HP **vermelha** e MP **azul** no topo da tela.

Para leitura correta, deixe a ROI o mais justa possível na área interna da barra (evite bordas/metade de outros elementos), pois bordas coloridas podem causar falso 100%.

Dica: se a % ficar instável, refine os ranges HSV e reduza ruído com:

- `smoothing.mode`: `ema` ou `median`
- `ema_alpha` (EMA) ou `median_window` (mediana)

## Regras e cooldown

Cada regra possui:

- `metric`: `HP` ou `MP`
- `threshold`: dispara quando `<= threshold`
- `action_name`: nome da ação (ring, amulet, potion etc.)
- `key`: tecla enviada (`F1..F12`, `1..5` por padrão)
- `cooldown_seconds`: intervalo mínimo entre disparos da mesma regra
- `enabled`: ativa/desativa

## Logs e alertas

- Log em console e arquivo (`alerts.log_file` no config).
- Toast simples na UI.
- Beep do Windows (pode desligar com `alerts.sound_enabled = false`).

## Tratamento de erros incluído

- Sem janela selecionada/encontrada.
- Janela minimizada (monitoramento pausado).
- ROI inválida.
- Erros de captura e análise visual.

## Estrutura

- `main.py` - bootstrap
- `ui.py` - interface tkinter
- `window_capture.py` - descoberta da janela e captura
- `bar_reader.py` - leitura de HP/MP por HSV
- `rules_engine.py` - regras, cooldown e envio de teclas
- `config.json` - configuração principal
- `requirements.txt`
