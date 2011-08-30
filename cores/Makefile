#TODO:
#Add rules for all cores
#Allow different repo paths and project names
ac97:
	@$(call opencores-get,ac97,ac97)
ethmac:
	@$(call opencores-get,ethmac,ethmac)
or1200:
	@$(call opencores-get,or1200,openrisc,or1200)

opencores-get = @echo Downloading $(1) from OpenCores && svn co http://opencores.org/ocsvn/$(2)/$(2)/trunk/$(3) $(1) --username openriscsvn --password openriscsvn -q
