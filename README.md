# Tibia Macro (PyTibia-style)

Projeto de macro para Tibia com foco em:

- detectar janela do client no padrão `Tibia - NOME_PERSONAGEM`;
- ativar a janela automaticamente;
- enviar teclas em sequência (macro);
- repetir por número de ciclos, por tempo ou indefinidamente.

> ⚠️ Este projeto é para automação local de teclado/janela em ambiente Windows. Use por sua conta e risco, respeitando os termos do jogo e legislação local.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuração (`macros.json`)

Cada macro possui:

- `name`: nome do macro;
- `window_title_prefix`: prefixo da janela (por padrão `Tibia - `);
- `character_name`: nome exato do personagem (opcional, mas recomendado);
- `actions`: lista de teclas;
- `repeat`: quantas vezes repetir (`0` = infinito);
- `interval_ms`: pausa entre ciclos;
- `run_for_seconds`: opcional, limita o tempo total.

Ação (`actions`):

- `key`: tecla (`f1`, `f2`, `1`, `space`, etc.);
- `hold_ms`: quanto tempo manter pressionada (opcional);
- `delay_ms`: atraso após a ação.

## Uso

Listar janelas detectadas:

```bash
python macro_tibia.py --list-windows
```

Executar um macro específico:

```bash
python macro_tibia.py --macro heal
```

Executar todos os macros:

```bash
python macro_tibia.py --run-all
```

Simular sem enviar teclas:

```bash
python macro_tibia.py --macro heal --dry-run
```

## Observações

- O macro procura janelas com título iniciando por `Tibia - `.
- Se `character_name` estiver definido, ele exige título exato: `Tibia - NOME_PERSONAGEM`.
- Em Linux/macOS a detecção/envio de teclas pode falhar dependendo do ambiente gráfico.
