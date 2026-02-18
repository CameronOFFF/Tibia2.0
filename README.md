# Tibia Macro (tela única)

Agora o projeto abre **uma interface única** com tudo junto:

- detectar cliente `Tibia - NOME_PERSONAGEM`;
- selecionar e executar macro;
- editar tecla do macro e salvar;
- definir % de vida/mana para potion e salvar;
- iniciar/parar monitor de potion;
- envio manual de teclas;
- log em tempo real.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uso

### Interface única (recomendado)

```bash
python macro_tibia.py
```

ou

```bash
python macro_tibia.py --gui
```

### O que você pediu (na mesma tela)

1. **Editar tecla do macro e salvar**
   - Selecione o macro.
   - Em **Editar tecla do macro (e salvar)** altere:
     - tecla da 1ª ação,
     - `hold_ms`, `delay_ms`, `repeat`, `interval_ms`.
   - Clique em **Salvar macro** (grava no `macros.json`).

2. **Definir % de vida e mana para potion**
   - No bloco **Potion por % de vida e mana** configure:
     - vida limite (`hp_threshold`),
     - mana limite (`mana_threshold`),
     - tecla da potion de vida,
     - tecla da potion de mana,
     - cooldown em ms.
   - Clique em **Salvar potion settings**.
   - Clique em **Iniciar monitor potion** para começar.

> Importante: o campo “Vida atual %” e “Mana atual %” é manual nesta versão (você atualiza os valores pela interface). O monitor usa esses valores para decidir quando enviar as teclas.

## Configuração (`macros.json`)

- `macros`: lista de macros.
- `potion_settings`: configuração global de potion.

Exemplo:

```json
{
  "macros": [{ "name": "heal", "actions": [{ "key": "f1" }] }],
  "potion_settings": {
    "hp_threshold": 50,
    "mana_threshold": 40,
    "hp_key": "f4",
    "mana_key": "f5",
    "cooldown_ms": 300
  }
}
```

## CLI opcional

```bash
python macro_tibia.py --list-windows
python macro_tibia.py --macro heal
python macro_tibia.py --run-all
python macro_tibia.py --macro heal --dry-run
```

## Observações

- O app procura janela iniciando com `Tibia - `.
- Se você escolher uma janela detectada, ela sobrescreve o `character_name` do macro na execução.
- Em Linux/macOS pode haver limitações de automação conforme o ambiente gráfico.
