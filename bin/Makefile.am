bin_SCRIPTS = fusesoc
CLEANFILES = $(bin_SCRIPTS)
EXTRA_DIST = fusesoc.in

do_substitution = sed -e 's,[@]pythondir[@],$(pythondir),g' \
	-e 's,[@]PACKAGE[@],$(PACKAGE),g' \
	-e 's,[@]VERSION[@],$(VERSION),g' \
	-e 's,[@]PYTHON[@],$(PYTHON),g'

fusesoc: fusesoc.in Makefile
	$(do_substitution) < $< > $@
	chmod +x $@
