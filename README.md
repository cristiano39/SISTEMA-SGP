# Sistema de consulta de usuários (AD SOE e outros sistemas)

Este projeto cria um utilitário para consultar usuários selecionados em uma planilha CSV e indicar se eles estão presentes no **AD SOE** e em outros sistemas.

## Requisitos

- Python 3.10+

## Executável

O projeto inclui um executável local chamado `sistema_usuarios`.

1. Dê permissão de execução (se necessário):

```bash
chmod +x sistema_usuarios
```

2. Execute normalmente:

```bash
./sistema_usuarios \
  --planilha dados_usuarios.csv \
  --usuarios "joao,maria,ana" \
  --coluna-usuario usuario \
  --sistemas "AD SOE,SAP,VPN"
```

> Internamente, o executável chama `python3 sistema_usuarios.py`.

## Como usar (script Python)

```bash
python sistema_usuarios.py \
  --planilha dados_usuarios.csv \
  --usuarios "joao,maria,ana" \
  --coluna-usuario usuario \
  --sistemas "AD SOE,SAP,VPN"
```

### Parâmetros

- `--planilha`: caminho do CSV com cabeçalho.
- `--usuarios`: lista de usuários separados por vírgula.
- `--arquivo-usuarios`: arquivo TXT com 1 usuário por linha (opcional).
- `--coluna-usuario`: nome da coluna do usuário (padrão: `usuario`).
- `--sistemas`: colunas dos sistemas a consultar (padrão: `AD SOE`).
- `--saida-json`: salva os dados filtrados em JSON.

## Exemplo de CSV

```csv
usuario,nome,AD SOE,SAP,VPN
joao,João Silva,sim,sim,nao
maria,Maria Souza,nao,sim,sim
ana,Ana Lima,1,0,
```

Valores aceitos para presença (SIM): `sim`, `1`, `true`, `ativo`, `ok`, `x`.

Valores aceitos para ausência (NÃO): `nao`, `não`, `0`, `false`, `inativo`, `-`.

Se não for possível inferir, o sistema mostra `N/I` (não informado).
