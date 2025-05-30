import bibtexparser
from bibtexparser import middlewares as mw
from main import html_template, get_file_content

def get_refs():
    refbibs = get_file_content("refs.bib")
    library = bibtexparser.parse_string(refbibs,
    append_middleware=[
        # transforms {\"o} -> ö, removes curly braces, etc.
        mw.LatexDecodingMiddleware(),
        # transforms apr -> 4 etc.
        mw.MonthIntMiddleware(True),
        # turns author field with multiple authors into a list
        mw.SeparateCoAuthors(),
        # splits author names into {first, von, last, jr}
        mw.SplitNameParts(),
    ],)
    if len(library.failed_blocks) > 0:
        print("Some blocks failed to parse. Check the entries of `library.failed_blocks`.")
    else:
        return library






class References:
    def __init__(self):
        self.refhtml = html_template("articles/research/references.html")
        self.bibhtml = html_template("articles/research/bibrefs.html")

    def add_identifier(self,RefList):
        self.refhtml.replace_text(RefList.identifier,RefList.thelist)
        self.bibhtml.replace_text(RefList.identifier,RefList.theref)

class ReferenceList:
    def __init__(self, name):
        self.name = name
        self.identifier = self.name.upper()
        self.thelist = ""
        self.theref = ""
        self.lib = get_refs()
        self.library = self.lib.entries_dict

    def cite(self,tag):
        self.thelist = self.thelist + "<li id = \"pub" + tag + "\">\n\t" + self.get_bib_format(tag) + "\n</li>\n"
        self.theref = self.theref + self.get_bibref_format(tag)

    def get_bibref_format(self,tag):
        return "<pre id = \"" + tag + "\">\n" + self.library[tag].raw + "\n</pre>\n\n"

    def get_bib_format(self,tag):
        if tag not in self.library: raise ValueError('bib entry not in refs.bib!!')
        entry = self.library[tag].fields_dict
        if not self.check_entry(tag): raise ValueError('bib entry: ' + tag + 'incorrect item in refs.bib!!')
        htmlformat = self.authorlist(entry) + "(" + entry['year'].value + "). \"" + entry['title'].value + ".\" " + self.pubwhere(entry) + self.checknote(entry) +  self.pdf_and_bibtex(tag)
        return htmlformat

    def check_entry(self,tag):
        flag = False
        if self.identifier == 'JOURNAL' and self.library[tag].entry_type == 'article': flag = True
        elif self.identifier == 'CONFERENCE' and self.library[tag].entry_type == 'inproceedings': flag = True
        elif self.identifier == 'ABSTRACT' and self.library[tag].entry_type == 'inproceedings': flag = True
        elif self.identifier == 'BOOKCHAP' and self.library[tag].entry_type == 'incollection': flag = True
        elif self.identifier == 'TECHNOTE' and self.library[tag].entry_type == 'techreport': flag = True
        return flag

    def pubwhere(self, item):
        wherepubbed = ""
        if self.identifier == 'JOURNAL':
            if 'volume' in item:
                volnm = ", vol. " + item['volume'].value
                if 'number' in item: volnm = volnm + ", no. "  + item['number'].value
            else: volnm = ""
            wherepubbed = "<i>" + item['journal'].value + "</i>" + volnm
        elif self.identifier == 'CONFERENCE' or self.identifier == 'ABSTRACT':
            wherepubbed = "In <i>" + item['booktitle'].value + "</i>"
        elif self.identifier == 'BOOKCHAP':
            wherepubbed = "In <i>" + item['series'].value + "</i>, (" + item['booktitle'].value + "). " + item['publisher'].value
        elif self.identifier == 'TECHNOTE':
            wherepubbed = item['type'].value + ". " + item['institution'].value
        if 'pages' in item and self.identifier != 'TECHNOTE':
            wherepubbed = wherepubbed + ", pp. " + item['pages'].value + ". "
        else:
            wherepubbed = wherepubbed + ". "
        return wherepubbed

    def authorlist(self, item):
        auth = item['author']
        N = len(auth.value)
        string = ""
        for i in range(N):
            Ninitials = len(auth.value[i].first)
            for j in range(Ninitials):
                string = string + auth.value[i].first[j][0] + "."
            if len(auth.value[i].von) != 0:
                string = string + " " + auth.value[i].von[0]
            string = string + " " + auth.value[i].last[0]
            if i < N - 2:
                string = string + ", "
            elif i == N - 2:
                string = string + ", and "
            else:
                string = string + " "
        return string

    def checknote(self,item):
        if 'note' in item:
            return "<b>" + item['note'].value + "</b>. "
        else: return ""

    def pdf_and_bibtex(self, tag):
        item = self.library[tag].fields_dict
        linkstr = "("
        if 'doi' in item: linkstr = linkstr + "<a href=\"" + item['doi'].value + "\" target=\"_blank\">pdf</a>, "
        elif 'url' in item: linkstr = linkstr + "<a href=\"" + item['url'].value + "\" target=\"_blank\">pdf</a>, "
        else: linkstr = linkstr + "pdf available on request, "
        linkstr = linkstr + "<a href=\"content/references.html#" + tag + "\" target=\"_blank\">bibtex</a>)"
        return linkstr


if __name__ == '__main__':
    htmlfiles = References()

    J = ReferenceList('JOURNAL')
    J.cite('verhoek2024behavddrep')
    J.cite('markovskyVerhoek2024mpum')
    J.cite('verhoek2024dd_dissipativity')
    J.cite('verhoek2023dpcjournal')
    J.cite('verhoek2024-J-statefeedback')
    J.cite('verhoek2023incremental')
    htmlfiles.add_identifier(J)

    C = ReferenceList('CONFERENCE')
    C.cite('hoekstra2025augmentation')
    C.cite('verhoek2024decoupling')
    C.cite('huijgevoort2024DDSTL')
    C.cite('spin2024unified')
    C.cite('verhoek2023generalnonlinear')
    C.cite('verhoek2023experiment')
    C.cite('verhoek2023stablelearning')
    C.cite('ai4gncpaper')
    C.cite('verhoek2022lpvsubnet')
    C.cite('deLange2022lpv')
    C.cite('verhoek2021dpc')
    C.cite('verhoek2021fundamentallemma')
    htmlfiles.add_identifier(C)

    B = ReferenceList('BOOKCHAP')
    B.cite('verhoek2024encyclo')
    htmlfiles.add_identifier(B)

    T = ReferenceList('TECHNOTE')
    T.cite('verhoek2024kernelnote')
    T.cite('verhoek2023technoteFL')
    T.cite('verhoek2022technotedecomp')
    htmlfiles.add_identifier(T)

    A = ReferenceList('ABSTRACT')
    A.cite('verhoek2025sssc')
    A.cite('blux2024')
    A.cite('blux2024a')
    A.cite('blux2024b')
    A.cite('blux2023')
    A.cite('blux2022')
    A.cite('blux2021')
    A.cite('blux2020')
    htmlfiles.add_identifier(A)

    htmlfiles.refhtml.save_contents('articles/research','publications.html')
    htmlfiles.bibhtml.save_contents('./../SD-research/content', 'references.html')




