"""Testing pydoc"""

import sys
import random
import itertools

from isobar.pattern.core import *
from isobar.key import *
from isobar.util import *
from isobar.chord import *

class PConst(Pattern):
	"""Pattern: Constant value"""

	def __init__(self, value):
		self.value = value

	def __str__(self):
		return "constant"

	def next(self):
		return self.value

class PSeq(Pattern):
	"""Pattern: Fixed sequence"""
	def __init__(self, list = [], repeats = sys.maxint):
		self.list = list
		self.repeats = repeats

		self.reset()

	def reset(self):
		self.rcount = 0
		self.pos = 0

	def next(self):
		if len(self.list) == 0 or self.rcount >= self.repeats:
			return None

		# support for pattern arguments
		list = self.value(self.list)
		repeats = self.value(self.repeats)

		rv = Pattern.value(list[self.pos])
		self.pos += 1
		if self.pos >= len(list):
			self.pos = 0
			self.rcount += 1

		return rv

class PSeries(Pattern):
	"""Pattern: Arithmetic series"""

	def __init__(self, start = 0, step = 1, length = sys.maxint):
		self.start = start
		self.value = start
		self.step = step
		self.length = length
		self.count = 0

	def reset(self):
		self.value = self.start 
		self.count = 0

		Pattern.reset(self)

	def next(self):
		if self.count >= self.length:
			return None
			# raise StopIteration
		n = self.value
		# XXX need a general-use way of writing this
		step = self.step.next() if isinstance(self.step, Pattern) else self.step
		self.value += step
		self.count += 1
		return n

class PLoop(Pattern):
	def __init__(self, pattern, count = sys.maxint):
		self.pattern = pattern
		self.values = []
		self.count = count
		self.pos = 0
		self.rpos = 1
		self.read_all = False

	def reset(self):
		self.pos = 0
		self.rpos = 1
		self.read_all = False
		self.values = []

		Pattern.reset(self)

	def next(self):
		if not self.read_all:
			rv = self.pattern.next()
			if rv is None:
				self.read_all = True
			else:
				self.values.append(rv)

		if self.read_all and self.pos >= len(self.values):
			if self.rpos >= self.count:
				return None
			else:
				self.rpos += 1
				self.pos = 0

		rv = self.values[self.pos]
		self.pos += 1
		return rv

class PPingPong(Pattern):
	""" plays a pattern back and forth N times """

	def __init__(self, pattern, count = sys.maxint):
		self.pattern = pattern
		self.count = count
		self.reset()

	def reset(self):
		self.pattern.reset()
		self.values = []
		self.pos = 0
		self.dir = 1
		self.rpos = 1
		self.read_all = False

	def next(self):
		if not self.read_all:
			rv = self.pattern.next()
			if rv is None:
				self.read_all = True
			else:
				self.values.append(rv)

		if self.read_all:
			if self.pos >= len(self.values):
				if self.rpos >= self.count:
					return None
				else:
					self.pos -= 2
					self.dir = -1
			elif self.pos == 0:
				self.rpos += 1
				self.dir = 1

		rv = self.values[self.pos]
		self.pos += self.dir
		return rv

# might also be nice to have a "repeats" param
# (in which case, PStutter could also be written as PCreep(p, 1, 1, n)
class PCreep(Pattern):
	def __init__(self, pattern, length = 4, creep = 1, count = 1):
		self.pattern = pattern
		self.length = length
		self.creep = creep
		self.count = count
		self.buffer = []
		self.pos = 0
		self.rcount = 1
		while len(self.buffer) < length:
			self.buffer.append(pattern.next())

	def next(self):
		pos = self.value(self.pos)
		length = self.value(self.length)
		creep = self.value(self.creep)
		count = self.value(self.count)
		while len(self.buffer) < length:
				self.buffer.append(self.pattern.next())
		while len(self.buffer) > length:
				self.buffer.pop(0)

		if self.pos >= len(self.buffer):
			if self.rcount >= count:
				for n in range(creep):
					self.buffer.pop(0)
					self.buffer.append(self.pattern.next())
				self.rcount = 1
			else:
				self.rcount += 1
			self.pos = 0

		self.pos += 1
		return self.buffer[self.pos - 1]

class PStutter(Pattern):
	def __init__(self, pattern, count = 2):   
		self.pattern = pattern
		self.count = count
		self.pos = count
		self.value = 0

	def next(self):
		if self.pos >= self.count:
			self.value = self.pattern.next()
			self.pos = 0
		self.pos += 1
		return self.value

class PWrap(Pattern):
	def __init__(self, pattern, min = 40, max = 80):
		self.pattern = pattern
		self.min = min
		self.max = max

	def next(self):
		value = self.pattern.next()
		while value < self.min:
			value += self.max - self.min
		while value > self.max:
			value -= self.max - self.min
		return value

class PPermut(Pattern):
	def __init__(self, input, count = 8):
		self.input = input
		self.count = count
		self.pos = sys.maxint
		self.permindex = sys.maxint
		self.permutations = []

	def reset(self):
		self.pos = sys.maxint
		self.permindex = sys.maxint
		self.permutations = []

		Pattern.reset(self)

	def next(self):
		if self.permindex > len(self.permutations):
			n = 0
			values = []
			while n < self.count:
				v = self.input.next()
				if v is None:
					break
				values.append(v)
				n += 1

			permiter = itertools.permutations(values)
			self.permutations = []
			for n in permiter:
				self.permutations.append(n)

			self.permindex = 0
			self.pos = 0
		elif self.pos >= len(self.permutations[0]):
			self.permindex = self.permindex + 1
			self.pos = 0
			
		rv = self.permutations[self.permindex][self.pos]
		self.pos += 1
		return rv

class PDegree(Pattern):
	def __init__(self, degree, scale = Scale.major):
		self.degree = degree
		self.scale = scale

	def next(self):
		degree = self.value(self.degree)
		scale = self.value(self.scale)
# print degree
#		print scale
		return scale[degree]


class PSubsequence(Pattern):
	def __init__(self, pattern, offset, length):
		self.pattern = pattern
		self.offset = offset
		self.length = length
		self.pos = 0
		self.values = []

	def reset(self):
		self.pos = 0

		Pattern.reset(self)

	def next(self):
		offset = self.value(self.offset)
		length = self.value(self.length)

		# print "length is %d, pos %d" % (length, self.pos)
		if self.pos >= length:
			return None

		while len(self.values) <= self.pos + offset:
			self.values.append(self.pattern.next())

		rv = self.values[offset + self.pos]
		self.pos += 1

		return rv

class PImpulse(Pattern):
	def __init__(self, period):
		self.period = period
		self.pos = period

	def reset(self):
		self.pos = 0
	
	def next(self):
		period = self.value(self.period)

		if self.pos >= period - 1:
			rv = 1
			self.pos = 0
		else:
			rv = 0
			self.pos += 1

		return rv

class PReset(Pattern):
	def __init__(self, pattern, trigger):
		self.value = 0
		self.pattern = pattern
		self.trigger = trigger

	def reset(self):
		self.value = 0

	def next(self):
		value = self.trigger.next()
		if value > 0 and self.value <= 0:
			self.pattern.reset()
			self.value = value
		elif value <= 0 and self.value > 0:
			self.value = value

		return self.pattern.next()
	
class PCounter(Pattern):
	def __init__(self, trigger):
		self.trigger = trigger
		self.value = 0
		self.count = 0

	def next(self):
		value = self.trigger.next()
		if value > 0 and self.value <= 0:
			self.count += 1
			self.value = value
		elif value <= 0 and self.value > 0:
			self.value = value

		return self.count

class PArp(Pattern):
	UP = 0
	DOWN = 1
	CONVERGE = 2
	DIVERGE = 2
	RANDOM = 3

	def __init__(self, chord = Chord.major, type = UP):
		self.chord = chord
		self.type = type
		self.pos = 0
		self.notes = self.chord.semitones()
		self.offsets = []

		if type == PArp.UP:
			self.offsets = range(len(self.notes))
		elif type == PArp.DOWN:
			self.offsets = list(reversed(range(len(self.notes))))
		elif type == PArp.CONVERGE:
			self.offsets = [ (n / 2) if (n % 2 == 0) else (0 - (n + 1) / 2) for n in xrange(len(self.notes)) ]
		elif type == PArp.DIVERGE:
			self.offsets = [ (n / 2) if (n % 2 == 0) else (0 - (n + 1) / 2) for n in xrange(len(self.notes)) ]
			self.offsets = list(reversed(self.offsets))
		elif type == PArp.RANDOM:
			self.offsets = range(len(self.notes))
			random.shuffle(self.offsets)

	def next(self):
		type = self.value(self.type)
		pos = self.value(self.pos)
		rv = None

		if pos < len(self.offsets):
			offset = self.offsets[pos]
			rv = self.notes[offset]
			self.pos = pos + 1

		return rv

