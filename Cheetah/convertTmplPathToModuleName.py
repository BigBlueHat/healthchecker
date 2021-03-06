import os.path
import string

letters = None
try:
    letters = string.ascii_letters
except AttributeError:
    letters = string.letters

l = ['_'] * 256
for c in string.digits + letters:
    l[ord(c)] = c
_pathNameTransChars = ''.join(l)
del l, c

def convertTmplPathToModuleName(tmplPath,
                                _pathNameTransChars=_pathNameTransChars,
                                splitdrive=os.path.splitdrive,
                                ):
    try:
        moduleName = splitdrive(tmplPath)[1].translate(_pathNameTransChars)
    except (UnicodeError, TypeError):
        moduleName = unicode(splitdrive(tmplPath)[1]).translate(unicode(_pathNameTransChars))
    return moduleName