OBJECTS := $(filter-out capi1.html,$(patsubst %.txt,%.html,$(wildcard *.txt)))

all: $(OBJECTS)

capi.html: capi1.txt

capi1.txt: ../fusesoc/section.py
	PYTHONPATH=.. python $< > $@

%.html: %.txt
	asciidoc $<

clean:
	rm -f $(OBJECTS) capi1.txt
