# Tibia Macro (tela única)

Corrigido o monitor de potion para detectar **automaticamente HP/Mana** por captura da barra na janela do Tibia.

## Como usar o monitor HP/Mana (funcionando)

1. Abra o cliente e selecione a janela `Tibia - NOME_PERSONAGEM` no app.
2. Em **4) Potion por % de vida e mana (detecção automática)**, configure:
   - `Vida limite %` e `Mana limite %`.
   - `Tecla HP` e `Tecla Mana`.
   - `Cooldown ms`.
   - `Região HP x,y,w,h` e `Região Mana x,y,w,h`.
3. Clique em **Salvar potion settings**.
4. Clique em **Iniciar monitor potion**.

Se a região estiver correta, os campos **HP detectado** e **Mana detectada** mudam em tempo real.
Quando HP/Mana ficam abaixo dos limites, o app envia as teclas configuradas.

## Sobre as regiões

As regiões são relativas ao canto superior esquerdo da janela do Tibia:

- formato: `x,y,w,h`
- exemplo incluído no `macros.json`:
  - `hp_region`: `168,41,111,8`
  - `mana_region`: `168,53,111,8`

> Esses valores podem variar conforme client/tema/resolução/interface. Se detectar errado, ajuste os números.

## Recursos da tela única

- Seleção/detecção de janela Tibia.
- Execução de macro selecionado/todos.
- Edição da tecla do macro e salvar.
- Monitor de potion com HP/Mana automático por barra.
- Envio manual de tecla.
- Log em tempo real.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Execução

```bash
python macro_tibia.py
```
