#
# round.py
#
# By Ross Ridge
# Public Domain
#
# Python 3 port by the mymc-py project (MIT licensed).  See NOTICE.
# Original (Python 2) code: https://sourceforge.net/p/mymc-opl/code/
#

# Simple rounding functions.
#

_SCCS_ID = "@(#) mysc round.py 1.3 07/04/17 02:10:27\n"

def div_round_up(a, b):
	return (a + b - 1) // b

def round_up(a, b):
	return (a + b - 1) // b * b

def round_down(a, b):
	return a // b * b
