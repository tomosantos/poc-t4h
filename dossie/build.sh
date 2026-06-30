#!/usr/bin/env bash
# Monta o dossiê (concatena seções) e gera o PDF via pandoc + xelatex (TinyTeX).
set -e
cd "$(dirname "$0")"
export PATH="$APPDATA/TinyTeX/bin/windows:$PATH"
PANDOC="C:/Users/welli/anaconda3/Lib/site-packages/pypandoc/files/pandoc.exe"
OUT="Dossie-Wellinton-Oliveira-Santos.pdf"

# Ordem das seções
# Concatena com linha em branco entre cada seção (markdown exige blank line
# antes de um heading; senão o sumário/TOC fica inconsistente).
> dossie.md
for sec in 00-frontmatter 01-introducao 02-metodologia 03-tecnicas \
           04-resultados 05-conclusao 06-viabilidade 07-referencias; do
  cat "secoes/$sec.md" >> dossie.md
  printf '\n\n' >> dossie.md
done

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
