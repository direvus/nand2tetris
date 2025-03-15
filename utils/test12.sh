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
    printf "\e[32m[OK]\e[0m\n" || printf "\e[31m[FAIL]\e[0m\n"

PKG="MemoryTest"
BUILDDIR="${DIR}/../build/project12/$PKG"
OUTDIR="${DIR}/../out/project12/$PKG"
echo ""
echo "$PKG"
mkdir -p "$OUTDIR" "$BUILDDIR"
cp -av "${DLPROJ}/${PKG}"/* "${BUILDDIR}/"
cp -v "${SRCDIR}/Memory.jack" "${BUILDDIR}/"
cp -v "${SRCDIR}/Memory.jack" "${BUILDDIR}/MemoryDiag/"
$COMP "$BUILDDIR" && \
    printf "\e[32m[OK]\e[0m\n" || printf "\e[31m[FAIL]\e[0m\n"
$COMP "$BUILDDIR/MemoryDiag" && \
    printf "\e[32m[OK]\e[0m\n" || printf "\e[31m[FAIL]\e[0m\n"

PKG="ScreenTest"
BUILDDIR="${DIR}/../build/project12/$PKG"
OUTDIR="${DIR}/../out/project12/$PKG"
echo ""
echo "$PKG"
mkdir -p "$OUTDIR" "$BUILDDIR"
cp -av "${DLPROJ}/${PKG}"/* "${BUILDDIR}/"
cp -v "${SRCDIR}/Screen.jack" "${BUILDDIR}/"
cp -v "${SRCDIR}/Math.jack" "${BUILDDIR}/"
$COMP "$BUILDDIR" && \
    printf "\e[32m[OK]\e[0m\n" || printf "\e[31m[FAIL]\e[0m\n"

PKG="OutputTest"
BUILDDIR="${DIR}/../build/project12/$PKG"
OUTDIR="${DIR}/../out/project12/$PKG"
echo ""
echo "$PKG"
mkdir -p "$OUTDIR" "$BUILDDIR"
cp -av "${DLPROJ}/${PKG}"/* "${BUILDDIR}/"
cp -v "${SRCDIR}/Output.jack" "${BUILDDIR}/"
$COMP "$BUILDDIR" && \
    printf "\e[32m[OK]\e[0m\n" || printf "\e[31m[FAIL]\e[0m\n"
