bin_SCRIPTS = orpsoc
EXTRA_DIST = orpsoc.in

do_substitution = sed -e 's,[@]pythondir[@],$(pythondir),g' \
	-e 's,[@]PACKAGE[@],$(PACKAGE),g' \
	-e 's,[@]VERSION[@],$(VERSION),g' \
	-e 's,[@]PYTHON[@],$(PYTHON),g'

orpsoc: orpsoc.in Makefile
	$(do_substitution) < $< > $@
	chmod +x $@
