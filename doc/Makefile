OBJECTS := $(filter-out capi1.html,$(patsubst %.adoc,%.html,$(wildcard *.adoc)))
OBJECTS += capi1.html
all: $(OBJECTS)

#capi.html: capi1.adoc

capi1.adoc: ../fusesoc/section.py capi1.adoc.footer
	PYTHONPATH=.. python $< > $@
	cat capi1.adoc.footer >> $@

%.html: %.adoc
	asciidoc $<

clean:
	rm -f $(OBJECTS) capi1.adoc
