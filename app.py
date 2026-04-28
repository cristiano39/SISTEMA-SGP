from __future__ import annotations

import io
from dataclasses import dataclass

import dash
from dash import Dash, Input, Output, State, dcc, html, dash_table
import pandas as pd
import plotly.express as px


@dataclass(frozen=True)
class DatasetColumns:
    tipo: str = "tipo"
    municipio: str = "municipio"
    entidade: str = "entidade"
    categoria: str = "categoria"
    data: str = "data"
    mes: str = "mes"
    ano: str = "ano"
    kg: str = "kg"
    quantidade: str = "quantidade"


COLS = DatasetColumns()


app: Dash = dash.Dash(__name__)
app.title = "SGP - Pesquisa de Dados"


def _normalizar(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {c: c.strip().lower() for c in df.columns}
    df = df.rename(columns=rename_map)

    if COLS.data in df.columns:
        df[COLS.data] = pd.to_datetime(df[COLS.data], errors="coerce")
        df[COLS.mes] = df[COLS.data].dt.month
        df[COLS.ano] = df[COLS.data].dt.year

    for col in (COLS.mes, COLS.ano):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    for col in (COLS.kg, COLS.quantidade):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in (COLS.tipo, COLS.municipio, COLS.entidade, COLS.categoria):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df


def _parse_upload(contents: str, filename: str) -> pd.DataFrame:
    content_type, content_string = contents.split(",")
    decoded = io.BytesIO(io.BytesIO(base64_decode(content_string)).getvalue())

    if filename.lower().endswith(".csv"):
        df = pd.read_csv(decoded)
    else:
        df = pd.read_excel(decoded)

    return _normalizar(df)


def base64_decode(encoded: str) -> bytes:
    import base64

    return base64.b64decode(encoded)


def _options(series: pd.Series) -> list[dict[str, str]]:
    vals = sorted(v for v in series.dropna().unique() if str(v).strip())
    return [{"label": str(v), "value": str(v)} for v in vals]


app.layout = html.Div(
    style={"maxWidth": "1200px", "margin": "0 auto", "padding": "24px"},
    children=[
        html.H2("Dashboard de Pesquisa de Dados - SGP"),
        html.P(
            "Faça upload da planilha (.xlsx, .xls ou .csv) para consultar dados "
            "de Doações e Descaracterizações separadamente."
        ),
        dcc.Upload(
            id="upload-data",
            children=html.Div(["Arraste ou ", html.A("selecione um arquivo")]),
            style={
                "width": "100%",
                "height": "70px",
                "lineHeight": "70px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "8px",
                "textAlign": "center",
                "marginBottom": "16px",
            },
            multiple=False,
        ),
        dcc.Store(id="dataset-store"),
        html.Div(id="upload-status", style={"marginBottom": "16px"}),
        dcc.Tabs(
            id="main-tabs",
            value="tab-doacoes",
            children=[
                dcc.Tab(label="Doações", value="tab-doacoes"),
                dcc.Tab(label="Descaracterizações", value="tab-descarac"),
            ],
        ),
        html.Div(id="tab-content", style={"marginTop": "16px"}),
    ],
)


def _build_filters(df: pd.DataFrame, prefix: str) -> html.Div:
    return html.Div(
        style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": "12px"},
        children=[
            dcc.Dropdown(
                id=f"{prefix}-municipio",
                options=_options(df[COLS.municipio]) if COLS.municipio in df.columns else [],
                placeholder="Município",
                multi=True,
            ),
            dcc.Dropdown(
                id=f"{prefix}-entidade",
                options=_options(df[COLS.entidade]) if COLS.entidade in df.columns else [],
                placeholder="Entidade",
                multi=True,
            ),
            dcc.Dropdown(
                id=f"{prefix}-ano",
                options=[
                    {"label": str(v), "value": int(v)}
                    for v in sorted(df[COLS.ano].dropna().unique())
                ]
                if COLS.ano in df.columns
                else [],
                placeholder="Ano",
                multi=True,
            ),
            dcc.Dropdown(
                id=f"{prefix}-mes",
                options=[
                    {"label": str(v), "value": int(v)}
                    for v in sorted(df[COLS.mes].dropna().unique())
                ]
                if COLS.mes in df.columns
                else [],
                placeholder="Mês",
                multi=True,
            ),
        ],
    )


def _filter_df(
    df: pd.DataFrame,
    municipios: list[str] | None,
    entidades: list[str] | None,
    anos: list[int] | None,
    meses: list[int] | None,
) -> pd.DataFrame:
    out = df.copy()
    if municipios and COLS.municipio in out.columns:
        out = out[out[COLS.municipio].isin(municipios)]
    if entidades and COLS.entidade in out.columns:
        out = out[out[COLS.entidade].isin(entidades)]
    if anos and COLS.ano in out.columns:
        out = out[out[COLS.ano].isin(anos)]
    if meses and COLS.mes in out.columns:
        out = out[out[COLS.mes].isin(meses)]
    return out


@app.callback(
    Output("dataset-store", "data"),
    Output("upload-status", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True,
)
def upload_dataset(contents: str, filename: str):
    if not contents or not filename:
        return dash.no_update, dash.no_update

    try:
        df = _parse_upload(contents, filename)
        return df.to_json(date_format="iso", orient="split"), html.Div(
            [
                html.B("Arquivo carregado com sucesso."),
                html.Span(f" Linhas: {len(df)} | Colunas: {len(df.columns)}"),
            ]
        )
    except Exception as exc:  # pylint: disable=broad-except
        return None, html.Div(f"Erro ao carregar arquivo: {exc}", style={"color": "red"})


@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "value"),
    Input("dataset-store", "data"),
)
def render_tab(tab: str, data: str | None):
    if not data:
        return html.Div("Envie uma planilha para habilitar os painéis.")

    df = pd.read_json(data, orient="split")

    if tab == "tab-doacoes":
        doacoes = df[df[COLS.tipo].str.lower() == "doacao"] if COLS.tipo in df.columns else df
        return html.Div(
            children=[
                html.H3("Doações - Municípios / Entidades / Categoria"),
                _build_filters(doacoes, "doacoes"),
                dcc.Graph(id="doacoes-grafico"),
                dash_table.DataTable(id="doacoes-tabela", page_size=12),
            ]
        )

    descarac = (
        df[df[COLS.tipo].str.lower() == "descaracterizacao"] if COLS.tipo in df.columns else df
    )
    return html.Div(
        children=[
            html.H3("Descaracterizações - KG por Mês/Ano"),
            _build_filters(descarac, "descarac"),
            dcc.Graph(id="descarac-grafico"),
            dash_table.DataTable(id="descarac-tabela", page_size=12),
        ]
    )


@app.callback(
    Output("doacoes-grafico", "figure"),
    Output("doacoes-tabela", "data"),
    Output("doacoes-tabela", "columns"),
    Input("doacoes-municipio", "value"),
    Input("doacoes-entidade", "value"),
    Input("doacoes-ano", "value"),
    Input("doacoes-mes", "value"),
    State("dataset-store", "data"),
    prevent_initial_call=True,
)
def atualizar_doacoes(municipios, entidades, anos, meses, data):
    df = pd.read_json(data, orient="split")
    if COLS.tipo in df.columns:
        df = df[df[COLS.tipo].str.lower() == "doacao"]

    filtrado = _filter_df(df, municipios, entidades, anos, meses)

    medida = COLS.quantidade if COLS.quantidade in filtrado.columns else COLS.kg
    if medida not in filtrado.columns:
        filtrado["contagem"] = 1
        medida = "contagem"

    by = [c for c in [COLS.municipio, COLS.entidade, COLS.categoria] if c in filtrado.columns]
    resumo = filtrado.groupby(by, dropna=False)[medida].sum().reset_index() if by else filtrado

    fig = px.bar(
        resumo,
        x=COLS.municipio if COLS.municipio in resumo.columns else resumo.columns[0],
        y=medida,
        color=COLS.entidade if COLS.entidade in resumo.columns else None,
        barmode="group",
        title="Distribuição de Doações",
    )

    return fig, resumo.to_dict("records"), [{"name": c, "id": c} for c in resumo.columns]


@app.callback(
    Output("descarac-grafico", "figure"),
    Output("descarac-tabela", "data"),
    Output("descarac-tabela", "columns"),
    Input("descarac-municipio", "value"),
    Input("descarac-entidade", "value"),
    Input("descarac-ano", "value"),
    Input("descarac-mes", "value"),
    State("dataset-store", "data"),
    prevent_initial_call=True,
)
def atualizar_descarac(municipios, entidades, anos, meses, data):
    df = pd.read_json(data, orient="split")
    if COLS.tipo in df.columns:
        df = df[df[COLS.tipo].str.lower() == "descaracterizacao"]

    filtrado = _filter_df(df, municipios, entidades, anos, meses)

    medida = COLS.kg if COLS.kg in filtrado.columns else COLS.quantidade
    if medida not in filtrado.columns:
        filtrado["contagem"] = 1
        medida = "contagem"

    by = [c for c in [COLS.ano, COLS.mes] if c in filtrado.columns]
    resumo = filtrado.groupby(by, dropna=False)[medida].sum().reset_index() if by else filtrado

    x_axis = COLS.mes if COLS.mes in resumo.columns else resumo.columns[0]
    fig = px.line(
        resumo,
        x=x_axis,
        y=medida,
        color=COLS.ano if COLS.ano in resumo.columns else None,
        markers=True,
        title="Descaracterizações em KG por Mês/Ano",
    )

    return fig, resumo.to_dict("records"), [{"name": c, "id": c} for c in resumo.columns]


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
