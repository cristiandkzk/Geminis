#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Renderiza el paper a HTML conservando el diseno.

El HTML se habia quedado ~30% atras del markdown porque se mantenian a mano por
separado. Este script hace del .md la unica fuente de verdad: el HTML se
regenera y no se edita nunca a mano.

    python render.py        ingles     -> Geminis-paper.html
    python render.py es     castellano -> Geminis-paper.es.html

La traduccion conserva la estructura del original, asi que lo unico que cambia
por idioma vive en PERFILES: los nombres de archivo, el masthead y las palabras
con las que el render reconoce secciones (resumen, invariantes, fronteras,
resuelto). El markdown no lleva ninguna marca de idioma.

Assets que el script consume y que SI se editan a mano:
    estilo.css                    la hoja de estilos (se embebe en <style>)
    figure-commutation.html       el <figure> con el SVG de §3
    figure-commutation.es.html    la misma figura con los rotulos en castellano

En el markdown, `<!-- FIGURA: archivo.html -->` reemplaza al bloque de codigo
que le sigue y al parrafo posterior (que en el HTML es el epigrafe). El perfil
le agrega su sufijo al nombre declarado y cae al declarado si esa variante no
existe.

El HTML de salida es formato Artifact: sin <!doctype>, <html>, <head> ni <body>.
"""

import html
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).parent
CSS = RAIZ / "estilo.css"

PERFILES = {
    "en": {
        "fuente": "Geminis Paper.md",
        "salida": "Geminis-paper.html",
        "sufijo_figura": "",
        "titulo": "Deterministic Succession",
        "kicker": "Protocol · concept",
        "resumen": "Abstract",
        "invariantes": "design invariants",
        "fronteras": "declared boundaries",
        "resuelto": "solved",
        "etiqueta_resuelto": "Solved",
    },
    "es": {
        "fuente": "Geminis Paper.es.md",
        "salida": "Geminis-paper.es.html",
        "sufijo_figura": ".es",
        "titulo": "Sucesión Determinista",
        "kicker": "Protocolo · concepto",
        "resumen": "Resumen",
        "invariantes": "invariantes",
        "fronteras": "fronteras",
        "resuelto": "resuelto",
        "etiqueta_resuelto": "Resuelto",
    },
}

PERFIL = PERFILES["en"]

# `**English** · [Español](x.es.md)` y su reverso: va en el repo, no en el paper
SELECTOR_IDIOMA = re.compile(
    r"^(?:\*\*English\*\*|\[English\]\([^)]*\))\s*·\s*"
    r"(?:\*\*Español\*\*|\[Español\]\([^)]*\))\s*$"
)


def figura(nombre):
    """Variante de idioma de una figura; el archivo declarado es el respaldo."""
    declarado = Path(nombre)
    variante = RAIZ / f"{declarado.stem}{PERFIL['sufijo_figura']}{declarado.suffix}"
    return variante if variante.exists() else RAIZ / nombre


# ---------- inline ----------

def inline(t):
    """Marcado inline. Escapa HTML primero para no romper con < y &."""
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t, flags=re.S)
    t = re.sub(r"(?<![\*\w])\*([^\*]+?)\*(?!\*)", r"<em>\1</em>", t, flags=re.S)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    return t.replace("\n", " ").strip()


def lider(t):
    """Parte `**Titulo.** resto` en (titulo, resto). Devuelve None si no aplica."""
    m = re.match(r"\*\*(.+?)\*\*\s*(.*)$", t, flags=re.S)
    if not m:
        return None
    return m.group(1).strip(), m.group(2).strip()


# ---------- bloques ----------

def partir_bloques(texto):
    """Corta el markdown en bloques separados por linea en blanco, respetando fences."""
    bloques, buf, en_fence = [], [], False
    for linea in texto.split("\n"):
        if linea.startswith("```"):
            en_fence = not en_fence
            buf.append(linea)
            if not en_fence:
                bloques.append("\n".join(buf))
                buf = []
            continue
        if en_fence:
            buf.append(linea)
            continue
        if linea.strip() == "":
            if buf:
                bloques.append("\n".join(buf))
                buf = []
        else:
            buf.append(linea)
    if buf:
        bloques.append("\n".join(buf))
    return bloques


def render_tabla(bloque):
    filas = [l for l in bloque.split("\n") if l.strip().startswith("|")]
    if len(filas) < 2:
        return ""
    def celdas(l):
        return [c.strip() for c in l.strip().strip("|").split("|")]
    cab = celdas(filas[0])
    cuerpo = [celdas(l) for l in filas[2:]]
    out = ['<div class="tablewrap">', "<table>", "<thead><tr>"]
    out += [f"<th>{inline(c)}</th>" for c in cab]
    out += ["</tr></thead>", "<tbody>"]
    for fila in cuerpo:
        out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in fila) + "</tr>")
    out += ["</tbody>", "</table>", "</div>"]
    return "\n".join(out)


def render_cita(bloque):
    """Blockquote -> .resuelto si empieza con 'Resuelto', si no .callout."""
    cuerpo = "\n".join(re.sub(r"^>\s?", "", l) for l in bloque.split("\n"))
    partes = [p.strip() for p in cuerpo.split("\n\n") if p.strip()]
    if not partes:
        return ""
    enc = lider(partes[0])
    if enc and enc[0].lower().startswith(PERFIL["resuelto"]):
        # formato: **Resuelto:** *nombre del problema*. cuerpo...
        # el lider puede traer una aclaracion extra ("Resuelto, y queda registrado porque...")
        resto = enc[1]
        m = re.match(r"\*(.+?)\*\.?\s*(.*)$", resto, flags=re.S)
        nombre, resto = (m.group(1).strip(), m.group(2).strip()) if m else ("", resto)
        aparte = re.sub(rf"^{PERFIL['resuelto']}:?", "", enc[0], flags=re.I).strip(" ,.:")
        etiqueta = PERFIL["etiqueta_resuelto"]
        etiqueta = f"{etiqueta} · {nombre}" if nombre else etiqueta
        cls, hcls = "resuelto", "rh"
        cuerpo = (f"<em>({inline(aparte)})</em> " if aparte else "") + inline(resto)
        primero = f'<p><span class="{hcls}">{inline(etiqueta)}</span>{cuerpo}</p>'
    else:
        cls, hcls = "callout", "ch"
        if enc:
            primero = f'<p><span class="{hcls}">{inline(enc[0].rstrip("."))}</span>{inline(enc[1])}</p>'
        else:
            primero = f"<p>{inline(partes[0])}</p>"
    extra = "".join(f"<p>{inline(p)}</p>" for p in partes[1:])
    return f'<div class="{cls}">{primero}{extra}</div>'


def render_lista(bloque):
    ordenada = bool(re.match(r"^\s*\d+\.", bloque.split("\n")[0]))
    items, actual = [], []
    for linea in bloque.split("\n"):
        if re.match(r"^\s*([-*]|\d+\.)\s+", linea):
            if actual:
                items.append(" ".join(actual))
            actual = [re.sub(r"^\s*([-*]|\d+\.)\s+", "", linea)]
        else:
            actual.append(linea.strip())
    if actual:
        items.append(" ".join(actual))
    tag = "ol" if ordenada else "ul"
    cuerpo = "".join(f"<li>{inline(i)}</li>" for i in items)
    return f"<{tag}>{cuerpo}</{tag}>"


# ---------- documento ----------

def render(md):
    bloques = partir_bloques(md)
    out, seccion_abierta, n_seccion = [], False, 0
    contexto = ""          # nombre de la seccion en curso
    invariantes = []       # acumulador para <ol class="invariants">
    saltar = 0

    def cerrar_invariantes():
        if not invariantes:
            return
        out.append('<ol class="invariants">')
        for item in invariantes:
            cuerpo = "".join(f"<p>{p}</p>" for p in item)
            out.append(f'<li><div class="inv-body">{cuerpo}</div></li>')
        out.append("</ol>")
        invariantes.clear()

    for idx, b in enumerate(bloques):
        if saltar:
            saltar -= 1
            continue
        s = b.strip()
        if not s or s == "---":
            continue

        # figura declarada: reemplaza el fence siguiente y el parrafo posterior
        m = re.match(r"<!--\s*FIGURA:\s*(\S+)\s*-->", s)
        if m:
            archivo = figura(m.group(1))
            if archivo.exists():
                out.append(archivo.read_text(encoding="utf-8").strip())
                saltar = 2
            continue

        if s.startswith("<!--"):
            continue

        # titulo del documento -> masthead (se arma aparte)
        if s.startswith("# "):
            continue

        # la linea de idioma es navegacion del repo, no del documento
        if SELECTOR_IDIOMA.match(s):
            continue

        if s.startswith("## "):
            cerrar_invariantes()
            titulo = re.sub(r"^##\s*\d*\.?\s*", "", s).strip()
            contexto = titulo
            if titulo.lower() == PERFIL["resumen"].lower():
                continue
            if seccion_abierta:
                out.append("</section>")
            n_seccion += 1
            out.append("<section>")
            out.append(f'<span class="snum">§ {n_seccion:02d}</span>')
            out.append(f"<h2>{inline(titulo)}</h2>")
            seccion_abierta = True
            continue

        if s.startswith("### "):
            cerrar_invariantes()
            titulo = s[4:].strip()
            m2 = re.match(r"^(\d+\.\d+)\s+(.*)$", titulo)
            if m2:
                titulo = f"{m2.group(1)} · {m2.group(2)}"
            out.append(f"<h3>{inline(titulo)}</h3>")
            continue

        if s.startswith("```"):
            codigo = "\n".join(s.split("\n")[1:-1])
            out.append(f'<div class="formula">{html.escape(codigo)}</div>')
            continue

        if s.startswith(">"):
            cerrar_invariantes()
            out.append(render_cita(b))
            continue

        if s.startswith("|"):
            cerrar_invariantes()
            out.append(render_tabla(b))
            continue

        if re.match(r"^\s*([-*]|\d+\.)\s+", s):
            cerrar_invariantes()
            out.append(render_lista(b))
            continue

        # parrafos con lider en negrita: cambian de forma segun la seccion
        enc = lider(s)
        if enc:
            titulo, resto = enc

            # §4 invariantes: I1..I5 abren item, los parrafos sueltos lo continuan
            if contexto.lower().startswith(PERFIL["invariantes"]) and re.match(r"^I\d", titulo):
                invariantes.append([f"<strong>{inline(titulo)}</strong> {inline(resto)}"])
                continue

            # §11 tests. Pide el `·` a proposito: §12 abre parrafos con
            # `**Test N pasado**: ...`, que es prosa y no una ficha de test.
            if re.match(r"^Test\s+\d+\s*·", titulo):
                cerrar_invariantes()
                tid = titulo.rstrip(".")
                out.append(
                    f'<div class="test"><span class="test-id">{inline(tid)}</span>'
                    f"<p>{inline(resto)}</p></div>"
                )
                continue

            # §10 fronteras declaradas
            if contexto.lower().startswith(PERFIL["fronteras"]):
                cerrar_invariantes()
                out.append(
                    f'<div class="frontera"><p><span class="fh">{inline(titulo)}</span>'
                    f" {inline(resto)}</p></div>"
                )
                continue

        # parrafo comun; si venimos de una invariante, se le pega
        if invariantes:
            invariantes[-1].append(inline(s))
            continue
        out.append(f"<p>{inline(s)}</p>")

    cerrar_invariantes()
    if seccion_abierta:
        out.append("</section>")
    return "\n".join(out)


def main():
    global PERFIL
    idioma = sys.argv[1] if len(sys.argv) > 1 else "en"
    if idioma not in PERFILES:
        print(f"idioma desconocido: {idioma} (hay {', '.join(PERFILES)})")
        return 1
    PERFIL = PERFILES[idioma]
    fuente = RAIZ / PERFIL["fuente"]
    salida = RAIZ / PERFIL["salida"]

    md = fuente.read_text(encoding="utf-8")

    # masthead: h1 + el parrafo en negrita que le sigue
    h1 = re.search(r"^#\s+(.+)$", md, re.M).group(1).strip()
    # el .+ tiene que ser perezoso: con re.S, uno goloso se come el documento
    # entero y agarra el ultimo parrafo en negrita en vez del subtitulo. Y entre
    # el titulo y la bajada va la linea de idioma, que hay que saltear.
    standfirst = re.search(
        r"^#\s+.+?\n\n(?:[^\n]*Español[^\n]*\n\n)?\*\*(.+?)\*\*", md, re.S | re.M
    ).group(1)

    # abstract: los parrafos de la seccion de resumen
    resumen = re.search(
        rf"^## {PERFIL['resumen']}\s*\n(.*?)(?=\n---|\n## )", md, re.S | re.M
    ).group(1)
    abstract = "".join(
        f"<p>{inline(p.strip())}</p>"
        for p in resumen.strip().split("\n\n")
        if p.strip()
    )

    cuerpo = render(md)

    partes = [
        f"<title>{html.escape(PERFIL['titulo'])}</title>",
        "<style>",
        CSS.read_text(encoding="utf-8").strip(),
        "</style>",
        "",
        '<div class="wrap">',
        "",
        '<header class="masthead">',
        f'  <p class="kicker">{inline(PERFIL["kicker"])}</p>',
        f"  <h1>{inline(h1)}</h1>",
        f'  <p class="standfirst">{inline(standfirst)}</p>',
        "</header>",
        "",
        f'<div class="abstract">{abstract}</div>',
        "",
        cuerpo,
        "",
        "</div>",
        "",
    ]
    salida.write_text("\n".join(partes), encoding="utf-8")

    palabras = len(re.sub(r"<[^>]+>", " ", "\n".join(partes)).split())
    print(f"escrito {salida.name}: {salida.stat().st_size} bytes, ~{palabras} palabras")


if __name__ == "__main__":
    sys.exit(main())
