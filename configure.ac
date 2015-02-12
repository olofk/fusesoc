AC_INIT([FuseSoC], [1.2-dev])

AM_INIT_AUTOMAKE([foreign])
AM_PATH_PYTHON([2.7])

AC_CONFIG_FILES([Makefile bin/Makefile])

AC_ARG_ENABLE([svn],
	[AS_HELP_STRING([--disable-svn],
		[disable providers using SVN])],
	[enable_svn=$enableval],
	[enable_svn=yes])

AS_IF([test "x$enable_svn" != "xno"], [
	AC_CHECK_PROG(HAVE_SVN, svn, yes, no)
	AS_IF([test "x$HAVE_SVN" = "xno"],
		AC_MSG_ERROR([Program svn not found. Install it or rerun with --disable-svn])
	)
])

AM_CONDITIONAL(HAVE_SVN, [test "x$enable_svn" = "xyes"])

AC_OUTPUT
