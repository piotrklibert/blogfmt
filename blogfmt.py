import re, sys, unicodedata
from codecs import open

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter


title_re        =  re.compile(r"## ?(.*?)\n\n", re.DOTALL)
para_re         =  re.compile(r"--para\. ?([^-#].*?)\n\n", re.DOTALL)
footnote_re     =  re.compile(r"\[\[(.+?)--.?przyp\..?\]\]", re.DOTALL)
code_re         =  re.compile(r"--kod=(.*?)\n(.*?)--/kod", re.DOTALL)
def_re          =  re.compile(r"--def\. ?([ ()\w]+) ?- ?(.*?)\n\n", re.DOTALL | re.U)
comment_re      =  re.compile(r"--comment\. ?([^-#].*?)\n\n", re.DOTALL)
inline_code_re  =  re.compile(r"`(.*?)`", re.DOTALL)
vline_re        =  re.compile(r"^={3,}$", re.MULTILINE)


def slugify(value):
    """ Stolen from Django. """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)


def read_text(fname):
    return open(fname, encoding="utf-8")\
            .read()\
            .replace("\r\n", "\n")


def replace_regex(text, regex, fun):
    """ Will fail for very long texts or very many substitutions (recursion).
    """
    match = regex.search(text)
    if match is None:
        return text

    start,end = match.span()
    return text[:start]+fun(match)+replace_regex(text[end:], regex, fun)


class footnote_replacer(object):
    """ Replaces encountered 'footnotes' with superscripted number and gathers
    bodies of this footnotes into a list - it is meant to be appended to the
    document after other processing is done.
    """
    def __init__(self, prefix):
        self.prefix     =  prefix
        self.count      =  0
        self.footnotes  =  []

    def __str__(self):
        ret = ["<ul class='footnotes'>"]
        for num, ftnote in enumerate(self.footnotes, start=1):
            ret.append("<li id='%s-%s'>%s</li>" % (self.prefix, num, ftnote))
        ret.append("</ul>")
        return "\n".join(ret)

    def __call__(self, match):
        self.count += 1
        self.footnotes.append(match.group(1))
        return "<sup><a href='#%s-%s'>[%s]</a></sup>" % (
            self.prefix, self.count, self.count
        )


def highlight_code(match):
    lang = match.group(1)
    h = highlight(
        match.group(2),
        get_lexer_by_name(lang.lower()),
        HtmlFormatter(linenos="table")
    )
    return "<div class='code'>%s</div>" % h



def main(input_fname):
    corpus = read_text(input_fname)

    # TODO: get the title from filename if not present in the file
    title       =  title_re.search(corpus)
    title_slug  =  slugify(title.group(1))

    corpus      =  corpus.replace(title.group(0), "")
    title       =  title.group(1)

    footnotes = footnote_replacer(title_slug)

    # replace all entities of different types, one by one, with their expanded
    # versions
    corpus = replace_regex(
        corpus, inline_code_re,
        lambda m: "<code>%s</code>" % m.group(1)
    )

    corpus = replace_regex(corpus, footnote_re, footnotes)

    corpus = replace_regex(
        corpus, code_re,
        highlight_code
    )

    corpus = replace_regex(
        corpus, vline_re,
        lambda m: "<hr />"
    )

    corpus = replace_regex(
        corpus, para_re,
        lambda m: "<p>%s</p>\n" % m.group(1)
    )

    corpus = replace_regex(
        corpus, def_re,
        lambda m: "<dl><dt>%s</dt><dd>%s</dd></dl>\n" % (m.group(1), m.group(2))
    )

    corpus = replace_regex(
        corpus, comment_re,
        lambda m: "<p class='comment'>%s</p>\n" % m.group(1)
    )

    if footnotes.footnotes:
        corpus += str(footnotes)

    print corpus


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError()
    main(sys.argv[1])
