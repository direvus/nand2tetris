DLDIR="$(dirname $0)/../download"
VMT="$(dirname $0)/../projects/07/vm_translator.py"
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
VMT="$(dirname $0)/../projects/08/vm_translator.py"

echo "Program Flow / Basic Loop: "
$VMT "$DLDIR/projects/8/ProgramFlow/BasicLoop/BasicLoop.vm" && \
    $CPU "$DLDIR/projects/8/ProgramFlow/BasicLoop/BasicLoop.tst" && \
    echo -e "\e[32m[OK]\e[0m" || echo -e "\e[31m[FAIL]\e[0m"
echo ""

echo "Program Flow / Fibonacci Series: "
$VMT "$DLDIR/projects/8/ProgramFlow/FibonacciSeries/FibonacciSeries.vm" && \
    $CPU "$DLDIR/projects/8/ProgramFlow/FibonacciSeries/FibonacciSeries.tst" && \
    echo -e "\e[32m[OK]\e[0m" || echo -e "\e[31m[FAIL]\e[0m"
echo ""

echo "Function Calls / Simple Function: "
$VMT "$DLDIR/projects/8/FunctionCalls/SimpleFunction/SimpleFunction.vm" && \
    $CPU "$DLDIR/projects/8/FunctionCalls/SimpleFunction/SimpleFunction.tst" && \
    echo -e "\e[32m[OK]\e[0m" || echo -e "\e[31m[FAIL]\e[0m"
echo ""

echo "Function Calls / Nested Call: "
$VMT "$DLDIR/projects/8/FunctionCalls/NestedCall" && \
    $CPU "$DLDIR/projects/8/FunctionCalls/NestedCall/NestedCall.tst" && \
    echo -e "\e[32m[OK]\e[0m" || echo -e "\e[31m[FAIL]\e[0m"
echo ""

echo "Function Calls / Fibonacci Element: "
$VMT "$DLDIR/projects/8/FunctionCalls/FibonacciElement" && \
    $CPU "$DLDIR/projects/8/FunctionCalls/FibonacciElement/FibonacciElement.tst" && \
    echo -e "\e[32m[OK]\e[0m" || echo -e "\e[31m[FAIL]\e[0m"
echo ""

echo "Function Calls / Statics: "
$VMT "$DLDIR/projects/8/FunctionCalls/StaticsTest" && \
    $CPU "$DLDIR/projects/8/FunctionCalls/StaticsTest/StaticsTest.tst" && \
    echo -e "\e[32m[OK]\e[0m" || echo -e "\e[31m[FAIL]\e[0m"
echo ""
