#!/usr/bin/env python3
"""Sistema de consulta de usuários em AD SOE e demais sistemas via planilha CSV.

Uso rápido:
  python sistema_usuarios.py --planilha usuarios.csv --usuarios joao,maria \
    --coluna-usuario usuario --sistemas "AD SOE,SAP,VPN"
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

TRUTHY_VALUES = {"1", "sim", "s", "true", "ativo", "ok", "x", "y", "yes"}


@dataclass
class UsuarioStatus:
    dados: dict[str, str]
    sistemas: dict[str, bool | None]


def normalizar_texto(valor: str) -> str:
    return valor.strip().casefold()


def interpretar_presenca(valor: str) -> bool | None:
    """Converte valor textual da planilha em presença booleana.

    Retorna:
      True  -> usuário presente no sistema
      False -> usuário ausente no sistema
      None  -> não foi possível inferir
    """
    bruto = valor.strip()
    if not bruto:
        return None

    txt = normalizar_texto(bruto)
    if txt in TRUTHY_VALUES:
        return True

    if txt in {"0", "nao", "não", "n", "false", "inativo", "-", "no"}:
        return False

    return None


def carregar_planilha_csv(caminho: Path) -> list[dict[str, str]]:
    with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        if not leitor.fieldnames:
            raise ValueError("A planilha não possui cabeçalho.")

        linhas: list[dict[str, str]] = []
        for linha in leitor:
            linha_limpa = {chave.strip(): (valor or "").strip() for chave, valor in linha.items()}
            linhas.append(linha_limpa)
        return linhas


def filtrar_usuarios(
    registros: Iterable[dict[str, str]],
    coluna_usuario: str,
    usuarios_alvo: set[str],
    sistemas: list[str],
) -> dict[str, UsuarioStatus]:
    resposta: dict[str, UsuarioStatus] = {}

    for registro in registros:
        valor_usuario = registro.get(coluna_usuario, "")
        if not valor_usuario:
            continue

        chave_usuario = normalizar_texto(valor_usuario)
        if chave_usuario not in usuarios_alvo:
            continue

        status_sistemas: dict[str, bool | None] = {}
        for sistema in sistemas:
            if sistema in registro:
                status_sistemas[sistema] = interpretar_presenca(registro[sistema])
            else:
                status_sistemas[sistema] = None

        resposta[chave_usuario] = UsuarioStatus(dados=registro, sistemas=status_sistemas)

    return resposta


def formatar_tabela(resultado: dict[str, UsuarioStatus], sistemas: list[str]) -> str:
    if not resultado:
        return "Nenhum usuário encontrado com os filtros informados."

    colunas = ["Usuário"] + sistemas
    larguras = [len(c) for c in colunas]
    linhas: list[list[str]] = []

    for usuario, status in sorted(resultado.items()):
        linha = [status.dados.get("nome", usuario)]
        for sistema in sistemas:
            valor = status.sistemas.get(sistema)
            if valor is True:
                linha.append("SIM")
            elif valor is False:
                linha.append("NÃO")
            else:
                linha.append("N/I")
        linhas.append(linha)
        larguras = [max(larguras[i], len(linha[i])) for i in range(len(colunas))]

    separador = " | "
    cabecalho = separador.join(colunas[i].ljust(larguras[i]) for i in range(len(colunas)))
    divisoria = "-+-".join("-" * larguras[i] for i in range(len(colunas)))

    corpo = [separador.join(linha[i].ljust(larguras[i]) for i in range(len(colunas))) for linha in linhas]
    return "\n".join([cabecalho, divisoria, *corpo])


def ler_usuarios_alvo(valor: str | None, arquivo: Path | None) -> set[str]:
    usuarios: set[str] = set()

    if valor:
        for item in valor.split(","):
            if item.strip():
                usuarios.add(normalizar_texto(item))

    if arquivo:
        with arquivo.open("r", encoding="utf-8") as f:
            for linha in f:
                if linha.strip():
                    usuarios.add(normalizar_texto(linha))

    if not usuarios:
        raise ValueError("Informe ao menos um usuário via --usuarios ou --arquivo-usuarios.")

    return usuarios


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consulta status de usuários no AD SOE e demais sistemas de uma planilha CSV.",
    )
    parser.add_argument("--planilha", required=True, type=Path, help="Caminho da planilha CSV")
    parser.add_argument(
        "--usuarios",
        help="Lista de usuários separada por vírgula (ex: joao,maria,ana)",
    )
    parser.add_argument(
        "--arquivo-usuarios",
        type=Path,
        help="Arquivo TXT com um usuário por linha",
    )
    parser.add_argument(
        "--coluna-usuario",
        default="usuario",
        help="Nome da coluna identificadora do usuário na planilha (padrão: usuario)",
    )
    parser.add_argument(
        "--sistemas",
        default="AD SOE",
        help='Colunas de sistemas separadas por vírgula (ex: "AD SOE,SAP,VPN")',
    )
    parser.add_argument(
        "--saida-json",
        type=Path,
        help="Se informado, grava o resultado completo em JSON nesse caminho",
    )

    args = parser.parse_args()

    sistemas = [s.strip() for s in args.sistemas.split(",") if s.strip()]
    usuarios_alvo = ler_usuarios_alvo(args.usuarios, args.arquivo_usuarios)

    registros = carregar_planilha_csv(args.planilha)
    resultado = filtrar_usuarios(registros, args.coluna_usuario, usuarios_alvo, sistemas)

    print(formatar_tabela(resultado, sistemas))

    if args.saida_json:
        serializavel = {
            usuario: {
                "dados": status.dados,
                "sistemas": status.sistemas,
            }
            for usuario, status in resultado.items()
        }
        args.saida_json.write_text(
            json.dumps(serializavel, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
