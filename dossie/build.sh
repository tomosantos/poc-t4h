#!/usr/bin/env bash
# Monta o dossiê (concatena seções) e gera o PDF via pandoc + xelatex (TinyTeX).
set -e
cd "$(dirname "$0")"
export PATH="$APPDATA/TinyTeX/bin/windows:$PATH"
PANDOC="C:/Users/welli/anaconda3/Lib/site-packages/pypandoc/files/pandoc.exe"
OUT="Dossie-Wellinton-Oliveira-Santos.pdf"

# Ordem das seções
cat \
  secoes/00-frontmatter.md \
  secoes/01-introducao.md \
  secoes/02-metodologia.md \
  secoes/03-tecnicas.md \
  secoes/04-resultados.md \
  secoes/05-conclusao.md \
  secoes/06-viabilidade.md \
  secoes/07-referencias.md \
  > dossie.md

# As figuras foram referenciadas como ../figuras/ (relativo a secoes/); como o
# dossie.md montado fica em dossie/, normaliza para figuras/ (cwd = dossie/).
sed -i 's#\.\./figuras/#figuras/#g' dossie.md

# As seções já trazem numeração manual nos títulos (## 2., ## 3., ...),
# por isso NÃO usamos --number-sections (evita numeração dupla). --toc gera o sumário.
"$PANDOC" dossie.md -o "$OUT" \
  --pdf-engine=xelatex \
  --toc --toc-depth=2 \
  -V mainfont="Times New Roman" \
  -V geometry:margin=2.5cm \
  -V fontsize=11pt \
  -V documentclass=article \
  -V linkcolor=blue -V colorlinks=true

echo "PDF gerado: dossie/$OUT"
