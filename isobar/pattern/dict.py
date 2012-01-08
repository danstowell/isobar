import sys
import itertools

from isobar.pattern.core import *
from isobar.key import *
#from isobar.util import *
#from isobar.chord import *

class PDict(Pattern):
	"""Pattern: dict of patterns"""
	def __init__(self, dict = {}):
		self.d = dict

	def next(self):

		# support for pattern arguments
		d = self.value(self.d)

		#rv = Pattern.value(list[self.pos])
		rv = dict((k, Pattern.value(d[k])) for k in d)

		return rv


