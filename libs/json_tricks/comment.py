
from re import findall


def strip_comment_line_with_symbol(line, start):
	parts = line.split(start)
	counts = [len(findall(r'(?:^|[^"\\]|(?:\\\\|\\")+)(")', part)) for part in parts]
	total = 0
	for nr, count in enumerate(counts):
		total += count
		if total % 2 == 0:
			return start.join(parts[:nr+1]).rstrip()
	else:
		return line.rstrip()


def strip_comments(string, comment_symbols=frozenset(('#', '//'))):
	"""
	:param string: A string containing json with comments started by comment_symbols.
	:param comment_symbols: Iterable of symbols that start a line comment (default # or //).
	:return: The string with the comments removed.
	"""
	lines = string.splitlines()
	for k in range(len(lines)):
		for symbol in comment_symbols:
			lines[k] = strip_comment_line_with_symbol(lines[k], start=symbol)
	return '\n'.join(lines)


