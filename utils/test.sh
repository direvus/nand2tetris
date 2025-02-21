DLDIR="$(dirname $0)/../download"
VMT="$(dirname $0)/../projects/07/vm_translator.py"
CPU="$DLDIR/tools/CPUEmulator.sh"

$VMT "$DLDIR/projects/7/MemoryAccess/BasicTest/BasicTest.vm"
$VMT "$DLDIR/projects/7/MemoryAccess/PointerTest/PointerTest.vm"
$VMT "$DLDIR/projects/7/MemoryAccess/StaticTest/StaticTest.vm"
$VMT "$DLDIR/projects/7/StackArithmetic/SimpleAdd/SimpleAdd.vm"
$VMT "$DLDIR/projects/7/StackArithmetic/StackTest/StackTest.vm"

$CPU "$DLDIR/projects/7/MemoryAccess/BasicTest/BasicTest.tst"
$CPU "$DLDIR/projects/7/MemoryAccess/PointerTest/PointerTest.tst"
$CPU "$DLDIR/projects/7/MemoryAccess/StaticTest/StaticTest.tst"
$CPU "$DLDIR/projects/7/StackArithmetic/SimpleAdd/SimpleAdd.tst"
$CPU "$DLDIR/projects/7/StackArithmetic/StackTest/StackTest.tst"

VMT="$(dirname $0)/../projects/08/vm_translator.py"

$VMT "$DLDIR/projects/8/ProgramFlow/BasicLoop/BasicLoop.vm"
$VMT "$DLDIR/projects/8/ProgramFlow/FibonacciSeries/FibonacciSeries.vm"
$VMT "$DLDIR/projects/8/FunctionCalls/SimpleFunction/SimpleFunction.vm"

$CPU "$DLDIR/projects/8/ProgramFlow/BasicLoop/BasicLoop.tst"
$CPU "$DLDIR/projects/8/ProgramFlow/FibonacciSeries/FibonacciSeries.tst"
$CPU "$DLDIR/projects/8/FunctionCalls/SimpleFunction/SimpleFunction.tst"
