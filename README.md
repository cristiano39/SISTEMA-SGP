# SISTEMA-SGP - Dashboard de Pesquisa

Dashboard em Dash para consulta separada de:

- **Doações** por municípios, entidades e categorias.
- **Descaracterizações** em **KG por mês/ano**, com foco em dados de planilha.

## Estrutura esperada da planilha

As colunas são normalizadas para minúsculo automaticamente. As mais importantes:

- `tipo` (ex.: `doacao`, `descaracterizacao`)
- `municipio`
- `entidade`
- `categoria`
- `data` (ou `mes` e `ano`)
- `kg`
- `quantidade`

## Executar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abra em: `http://localhost:8050`
