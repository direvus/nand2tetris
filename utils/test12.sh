#!/bin/sh
DIR="$(dirname "$0")"
DLDIR="${DIR}/../download"
DLPROJ="${DLDIR}/projects/12"
SRCDIR="${DIR}/../projects/12"

VME="$DLDIR/tools/VMEmulator.sh"
COMP="$DLDIR/tools/JackCompiler.sh"

PKG="MathTest"
BUILDDIR="${DIR}/../build/project12/$PKG"
OUTDIR="${DIR}/../out/project12/$PKG"
echo ""
echo "$PKG"
mkdir -p "$OUTDIR" "$BUILDDIR"
cp -v "${SRCDIR}/Math.jack" "${BUILDDIR}/"
cp -av "${DLPROJ}/${PKG}"/* "${BUILDDIR}/"
$COMP "$BUILDDIR" && \
    $VME "${BUILDDIR}/${PKG}.tst" && \
    printf "\e[32m[OK]\e[0m\n" || printf "\e[31m[FAIL]\e[0m\n"
