bin_SCRIPTS = out/fusesoc
CLEANFILES = $(bin_SCRIPTS)

do_substitution = sed -e 's,[@]pythondir[@],$(pythondir),g' \
	-e 's,[@]PACKAGE[@],$(PACKAGE),g' \
	-e 's,[@]VERSION[@],$(VERSION),g' \
	-e 's,[@]PYTHON[@],$(PYTHON),g'

$(bin_SCRIPTS): bin/fusesoc Makefile
	$(MKDIR_P) out
	$(do_substitution) < $< > $@
	chmod +x $@

fusesoc_PYTHON =        \
 fusesoc/__init__.py           \
 fusesoc/config.py             \
 fusesoc/core.py               \
 fusesoc/coremanager.py        \
 fusesoc/edatool.py             \
 fusesoc/fusesocconfigparser.py \
 fusesoc/plusargs.py           \
 fusesoc/section.py            \
 fusesoc/system.py             \
 fusesoc/utils.py

fusesocdir = $(pkgpythondir)

provider_PYTHON =      \
 fusesoc/provider/__init__.py  \
 fusesoc/provider/git.py       \
 fusesoc/provider/github.py    \
 fusesoc/provider/url.py
if HAVE_SVN
 provider_PYTHON += fusesoc/provider/opencores.py
endif

providerdir = $(fusesocdir)/provider

simulator_PYTHON =      \
 fusesoc/simulator/__init__.py  \
 fusesoc/simulator/icarus.py    \
 fusesoc/simulator/isim.py      \
 fusesoc/simulator/xsim.py      \
 fusesoc/simulator/modelsim.py  \
 fusesoc/simulator/simulator.py \
 fusesoc/simulator/verilator.py

simulatordir = $(fusesocdir)/simulator


build_PYTHON =      \
 fusesoc/build/__init__.py  \
 fusesoc/build/backend.py    \
 fusesoc/build/ise.py        \
 fusesoc/build/quartus.py    \
 fusesoc/build/vivado.py

builddir = $(fusesocdir)/build

ipyxact_PYTHON =                \
 fusesoc/ipyxact/__init__.py    \
 fusesoc/ipyxact/ipxact_yaml.py \
 fusesoc/ipyxact/ipyxact.py

ipyxactdir = $(fusesocdir)/ipyxact

EXTRA_DIST = INSTALL bin doc

dist-hook:
	make -C $(distdir)/doc clean all
	rm `find $(distdir)/doc -name '*.txt'`
	rm $(distdir)/doc/Makefile
