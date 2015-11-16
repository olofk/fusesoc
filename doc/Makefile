OBJECTS := $(filter-out capi1.html,$(patsubst %.txt,%.html,$(wildcard *.txt)))

all: $(OBJECTS)

capi.html: capi1.txt

capi1.txt:
	PYTHONPATH=.. python ../fusesoc/section.py > $@

%.html: %.txt
	asciidoc $<

clean:
	rm -f $(OBJECTS) capi1.txt
