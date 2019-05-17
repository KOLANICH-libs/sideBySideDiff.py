import typing
from math import log10, ceil
import difflib
from RichConsole import RichStr, groups, rsjoin


def getMaxWidth(column: typing.List[str]) -> int:
	return max(len(str(e)) for e in column)


def deletedStyle(l: str) -> RichStr:
	return groups.CrossedOut.crossedOut(groups.Fore.green(l))


StyleT = typing.Callable[[str], typing.Union[str, RichStr]]
StylePairT = typing.Tuple[StyleT, StyleT]

StringConverterT = typing.Callable[[typing.Any], str]

def dummy(x):
	return x

StyleDictT = typing.Dict[str, typing.Union[StyleT, StylePairT]]
defaultStyle = {
	"equal": (dummy, dummy),
	"replace": (groups.Fore.lightblueEx, groups.Fore.lightblueEx),
	"insert": (groups.Back.lightyellowEx, groups.Fore.lightgreenEx),
	"delete": (deletedStyle, groups.Back.lightredEx),
	"lineNo": groups.Fore.lightcyanEx
}

rangeOrSlice = typing.Union[slice, range]


def azip(a: typing.Any, ar: rangeOrSlice, b: typing.Any, br: rangeOrSlice, substitute: typing.Any = None) -> typing.Iterator[typing.Any]:
	#ar.stop = typing.cast(int, ar.stop)
	#ar.start = typing.cast(int, ar.start)
	#br.stop = typing.cast(int, br.stop)
	#br.start = typing.cast(int, br.start)

	al = ar.stop - ar.start
	bl = br.stop - br.start

	d = al - bl
	comm = min(al, bl)
	yield from zip(a[ar.start : ar.start + comm], range(ar.start, ar.start + comm), b[br.start : br.start + comm], range(br.start, br.start + comm))

	if d > 0:
		yield from zip(a[ar.start + comm : ar.stop], range(ar.start + comm, ar.stop), [substitute] * d, [None] * d)
	elif d < 0:
		yield from zip([substitute] * (-d), [None] * (-d), b[br.start + comm : br.stop], range(br.start + comm, br.stop))


def genPadding(l: int, padder: str = " ") -> str:
	return padder * l


LineNumberT = typing.Union[str, int]


def genNum(n: LineNumberT, numWidth: int) -> str:
	r = str(n)
	return genPadding(numWidth - len(r), "0") + r


def generateRichStrLineDiff(al: str, aln: LineNumberT, bl: str, bln: LineNumberT, opStyle: StylePairT, lineNoStyle: StyleT, maxW: typing.Tuple[int, int], numWidth: int, strConverter: StringConverterT) -> RichStr:
	if al is None:
		al = ""
	if bl is None:
		bl = ""
	al = strConverter(al)
	bl = strConverter(bl)

	if aln is None:
		aln = genPadding(numWidth)

	if bln is None:
		bln = genPadding(numWidth)

	return rsjoin(" ", (
		lineNoStyle(genNum(aln, numWidth)),
		opStyle[0](al),
		genPadding(maxW[0] - len(al)),
		lineNoStyle(genNum(bln, numWidth)),
		opStyle[1](bl)
	))


OpcodeT = typing.Tuple[str, int, int, int, int]

def sideBySideDiff(a: typing.List[str], b: typing.List[str], *, style: typing.Optional[StyleDictT] = None, strConverter: typing.Optional[StringConverterT] = None, names: typing.Optional[typing.Tuple[str, str]] = None, matcherClass: typing.Optional[typing.Type[difflib.SequenceMatcher]]=None, opcodes: typing.Optional[typing.Iterable[OpcodeT]]=None) -> typing.Iterator[RichStr]:
	style_ = type(defaultStyle)(defaultStyle)
	if style is not None:
		style_.update(style)
	if strConverter is None:
		strConverter = str

	lns = style_["lineNo"]


	if opcodes is None:
		if matcherClass is None:
			matcherClass = difflib.SequenceMatcher
		m = matcherClass(None, a, b)
		opcodes = m.get_opcodes()

	maxW = (getMaxWidth(a), getMaxWidth(b))
	numMaxWidth = ceil(log10(max(len(a), len(b))))

	if names is not None:
		maxW = typing.cast(typing.Tuple[int, int], tuple(max(szs) for szs in zip(maxW, (len(n) for n in names))))
		secondHeaderPadding = 1 + numMaxWidth + maxW[0]  # space between first line and its number  # padding
		yield " ".join((genPadding(numMaxWidth), names[0], genPadding(secondHeaderPadding - len(names[0])), names[1]))

	for oc, aS, aE, bS, bE in opcodes:
		opStyle = style_[oc]
		if oc == "equal":
			for al, aln, bl, bln in zip(a[aS:aE], range(aS, aE), b[bS:bE], range(bS, bE)):
				yield generateRichStrLineDiff(al, aln, bl, bln, opStyle, lns, maxW, numMaxWidth, strConverter)

		elif oc == "replace":
			for al, aln, bl, bln in azip(a, range(aS, aE), b, range(bS, bE), None):
				yield generateRichStrLineDiff(al, aln, bl, bln, opStyle, lns, maxW, numMaxWidth, strConverter)
		elif oc == "insert":
			for bl, bln in zip(b[bS:bE], range(bS, bE)):
				yield generateRichStrLineDiff(genPadding(maxW[0]), genPadding(numMaxWidth), bl, bln, opStyle, lns, maxW, numMaxWidth, strConverter)
		elif oc == "delete":
			for al, aln in zip(a[aS:aE], range(aS, aE)):
				yield generateRichStrLineDiff(al, aln, genPadding(maxW[1]), genPadding(numMaxWidth), opStyle, lns, maxW, numMaxWidth, strConverter)


if __name__ == "__main__":
	from pathlib import Path
	import sys
	with Path(sys.argv[1]).open("rt", encoding="utf-8") as f0:
		with Path(sys.argv[2]).open("rt", encoding="utf-8") as f1:
			for l in sideBySideDiff(f0.read().splitlines(), f1.read().splitlines()):
				print(l)
