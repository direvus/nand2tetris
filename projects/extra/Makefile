HWSIM=HardwareSimulator.sh
COMPARE=TextComparer.sh
COMPILE=JackCompiler.sh
hdlfiles=$(wildcard *.hdl)
outfiles=$(patsubst %.hdl,%.out,$(hdlfiles))


.PHONY: simulate test


simulate: $(outfiles)


%.out: %.tst %.hdl %.cmp
	$(HWSIM) $<
