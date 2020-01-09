open_project test_spyglass_0.prj

current_goal some/othergoal

# Parameters which are not used/defined in a given goal/methodology raise
# a WARNING, which fails the lint process. That's a bit over the top, we hence
# disable this warning.
waive -rule {checkCMD_unknown}

set rc [run_goal]
close_project -force

set errorCode [lindex $rc 0]
set errorMsg [lindex $rc 1]
if { $errorCode } {
  puts stderr "SpyGlass run failed: $errorMsg ($errorCode)"
}

# requires sg_shell to be called with -enable_pass_exit_codes, otherwise
# all non-fatal exit codes are mapped to 0
exit $errorCode
