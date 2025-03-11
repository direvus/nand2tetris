#!/bin/sh
DIR="$(dirname "$0")"
DLDIR="${DIR}/../download"
VMT="${DIR}/../projects/07/vm_translator.py"
CPU="$DLDIR/tools/CPUEmulator.sh"

echo "Project 7"
echo "---------"
$VMT "$DLDIR/projects/7/MemoryAccess/BasicTest/BasicTest.vm" && \
    $CPU "$DLDIR/projects/7/MemoryAccess/BasicTest/BasicTest.tst"

$VMT "$DLDIR/projects/7/MemoryAccess/PointerTest/PointerTest.vm" && \
    $CPU "$DLDIR/projects/7/MemoryAccess/PointerTest/PointerTest.tst"

$VMT "$DLDIR/projects/7/MemoryAccess/StaticTest/StaticTest.vm" && \
    $CPU "$DLDIR/projects/7/MemoryAccess/StaticTest/StaticTest.tst"

$VMT "$DLDIR/projects/7/StackArithmetic/SimpleAdd/SimpleAdd.vm" && \
    $CPU "$DLDIR/projects/7/StackArithmetic/SimpleAdd/SimpleAdd.tst"

$VMT "$DLDIR/projects/7/StackArithmetic/StackTest/StackTest.vm" && \
    $CPU "$DLDIR/projects/7/StackArithmetic/StackTest/StackTest.tst"

echo ""
echo "Project 8"
echo "---------"
VMT="${DIR}/../projects/08/vm_translator.py"

echo "Program Flow / Basic Loop: "
$VMT "$DLDIR/projects/8/ProgramFlow/BasicLoop/BasicLoop.vm" && \
    $CPU "$DLDIR/projects/8/ProgramFlow/BasicLoop/BasicLoop.tst" && \
    printf "\e[32m[OK]\e[0m\n" || printf "\e[31m[FAIL]\e[0m\n"

echo "Program Flow / Fibonacci Series: "
$VMT "$DLDIR/projects/8/ProgramFlow/FibonacciSeries/FibonacciSeries.vm" && \
    $CPU "$DLDIR/projects/8/ProgramFlow/FibonacciSeries/FibonacciSeries.tst" && \
    printf "\e[32m[OK]\e[0m\n" || printf "\e[31m[FAIL]\e[0m\n"

echo "Function Calls / Simple Function: "
$VMT "$DLDIR/projects/8/FunctionCalls/SimpleFunction/SimpleFunction.vm" && \
    $CPU "$DLDIR/projects/8/FunctionCalls/SimpleFunction/SimpleFunction.tst" && \
    printf "\e[32m[OK]\e[0m\n" || printf "\e[31m[FAIL]\e[0m\n"

echo "Function Calls / Nested Call: "
$VMT "$DLDIR/projects/8/FunctionCalls/NestedCall" && \
    $CPU "$DLDIR/projects/8/FunctionCalls/NestedCall/NestedCall.tst" && \
    printf "\e[32m[OK]\e[0m\n" || printf "\e[31m[FAIL]\e[0m\n"

echo "Function Calls / Fibonacci Element: "
$VMT "$DLDIR/projects/8/FunctionCalls/FibonacciElement" && \
    $CPU "$DLDIR/projects/8/FunctionCalls/FibonacciElement/FibonacciElement.tst" && \
    printf "\e[32m[OK]\e[0m\n" || printf "\e[31m[FAIL]\e[0m\n"

echo "Function Calls / Statics: "
$VMT "$DLDIR/projects/8/FunctionCalls/StaticsTest" && \
    $CPU "$DLDIR/projects/8/FunctionCalls/StaticsTest/StaticsTest.tst" && \
    printf "\e[32m[OK]\e[0m\n" || printf "\e[31m[FAIL]\e[0m\n"

echo ""
echo "Project 10"
echo "----------"

COMP="${DIR}/../projects/10/compiler.py"
CHECK="${DLDIR}/tools/TextComparer.sh"

echo "ArrayTest"
$COMP "$DLDIR/projects/10/ArrayTest/Main.jack" > out/Main.xml && \
    $CHECK "$DLDIR/projects/10/ArrayTest/Main.xml" out/Main.xml
    printf "\e[32m[OK]\e[0m\n" || printf "\e[31m[FAIL]\e[0m\n"

echo "Square"
$COMP "$DLDIR/projects/10/Square/Main.jack" > out/Main.xml && \
    $CHECK "$DLDIR/projects/10/Square/Main.xml" out/Main.xml
    printf "\e[32m[OK]\e[0m\n" || printf "\e[31m[FAIL]\e[0m\n"

$COMP "$DLDIR/projects/10/Square/Square.jack" > out/Square.xml && \
    $CHECK "$DLDIR/projects/10/Square/Square.xml" out/Square.xml
    printf "\e[32m[OK]\e[0m\n" || printf "\e[31m[FAIL]\e[0m\n"

$COMP "$DLDIR/projects/10/Square/SquareGame.jack" > out/SquareGame.xml && \
    $CHECK "$DLDIR/projects/10/Square/SquareGame.xml" out/SquareGame.xml
    printf "\e[32m[OK]\e[0m\n" || printf "\e[31m[FAIL]\e[0m\n"

echo ""
echo "Project 11"
echo "----------"

DLPROJ="${DLDIR}/projects/11"
COMP="${DIR}/../projects/11/JackCompiler.py"
CHECK="${DLDIR}/tools/TextComparer.sh"

PKG="Average"
OUTDIR="out/project11/$PKG"
echo "$PKG"
mkdir -p "$OUTDIR"
$COMP "$DLPROJ/$PKG" "$OUTDIR"

PKG="Square"
OUTDIR="out/project11/$PKG"
echo "$PKG"
mkdir -p "$OUTDIR"
$COMP "$DLPROJ/$PKG" "$OUTDIR"
