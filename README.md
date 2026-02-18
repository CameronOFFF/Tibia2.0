# Tibia Macro (tela única)

Agora o projeto abre **uma interface única** com todas as funções na mesma tela:

- detectar cliente `Tibia - NOME_PERSONAGEM`;
- escolher macro do `macros.json`;
- executar macro selecionado ou todos;
- parar execução;
- envio manual de tecla;
- log em tempo real.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuração (`macros.json`)

Campos de cada macro:

- `name`: nome do macro;
- `window_title_prefix`: prefixo da janela (normalmente `Tibia - `);
- `character_name`: nome do personagem;
- `actions`: sequência de teclas;
- `repeat`: repetições (`0` = infinito);
- `interval_ms`: pausa entre ciclos;
- `run_for_seconds`: limite total opcional.

Cada item em `actions`:

- `key`: tecla (`f1`, `f2`, `1`, `space`, etc.);
- `hold_ms`: tempo pressionando (opcional);
- `delay_ms`: atraso após ação.

## Uso

### Interface única (recomendado)

```bash
python macro_tibia.py
```

ou

```bash
python macro_tibia.py --gui
```

### CLI (opcional)

```bash
python macro_tibia.py --list-windows
python macro_tibia.py --macro heal
python macro_tibia.py --run-all
python macro_tibia.py --macro heal --dry-run
```

## Observações

- O app procura janela iniciando com `Tibia - `.
- Se você escolher uma janela detectada na interface, ela sobrescreve o `character_name` do macro na hora da execução.
- Em Linux/macOS pode haver limitações de automação conforme ambiente gráfico.
