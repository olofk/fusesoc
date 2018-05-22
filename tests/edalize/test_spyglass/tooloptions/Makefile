NAME := test_spyglass_0

run-goals: run-goal-design_read run-goal-lint_lint_rtl run-goal-some_othergoal 
run-goal-design_read:
	sg_shell -enable_pass_exit_codes -tcl spyglass-run-design_read.tcl

run-goal-lint_lint_rtl:
	sg_shell -enable_pass_exit_codes -tcl spyglass-run-lint_lint_rtl.tcl

run-goal-some_othergoal:
	sg_shell -enable_pass_exit_codes -tcl spyglass-run-some_othergoal.tcl

run-gui:
	spyglass -project $(NAME).prj