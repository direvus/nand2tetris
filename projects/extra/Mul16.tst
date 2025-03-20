load Mul16.hdl,
output-file Mul16.out,
compare-to Mul16.cmp,
output-list a%B1.16.1 b%B1.16.1 out%B1.16.1;

set a %B0000000000000000,
set b %B0000000000000000,
eval,
output;

set a %B0000000000000001,
set b %B0000000000000000,
eval,
output;

set a %B0000000000000000,
set b %B0000000000000001,
eval,
output;

set a %B0000000000000001,
set b %B0000000000000001,
eval,
output;

set a %B0000000000001101,
set b %B0000000000000011,
eval,
output;

set a %B1111111111111111,
set b %B0000000000000001,
eval,
output;

set a %B1111111111111111,
set b %B1111111111111111,
eval,
output;

set a %B1111110000011000,
set b %B0000000000000101,
eval,
output;
