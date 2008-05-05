#!/usr/bin/python

# moin2media - convert a MoinMoin wiki to MediaWiki 1.5 import format

# Copyright 2006 Free Standards Group, Inc.
# Author: Jeff Licquia <licquia@freestandards.org>
# Author: Mike McGrath <mmcgrath@redhat.com>
# Permission granted to release under GPL

# Altered 2008 by Ignacio Vazquez-Abrams <ivazquez@fedoraproject.org>

import sys
import os
import re
import elementtree.ElementTree as etree
import mx.DateTime
import cgi
import codecs

def _table_xlat(data):
    in_table = False
    has_class = False
    result = []
    #sys.stderr.write("Data: %s" % data)
    for line in data.splitlines(True):
        if line.strip(':').strip().startswith(u"||"):
            # Gut the html stuff until we figure out what to do with it
            #line = re.sub(r'<([a-zA-Z\/][^>])*>', '\1|', line)
            if not in_table:
                if line.strip().startswith(u"||<tableclass"):
                    #result.append(u"{{message/notice")
                    #tableclass = re.sub(r'.*<([a-zA-Z\/][^>]*)>.*', r'\1', line.split('>')[0] + '>')
                    tableclass = re.sub(r'.*<([a-zA-Z\/][^>]*)>(.*)', r'\1 | \2', line).replace('tableclass="', 'Template:').replace(' ', '/', 1).replace('"', '', 1)
                    result.append(u"{{ %s" % tableclass)
                    has_class = True
                elif line.strip().startswith(u"||<tablestyle"):
                    tablestyle = re.sub(r'.*<([a-zA-Z\/][^>]*)>.*', r'\1', line.split('>')[0] + '>')
                    tablestyle = tablestyle.replace('tablestyle', 'style')
                    result.append(u"{| %s" % tablestyle)
                else:
                    result.append(u"{| border=\"1\"")
                in_table = True
            newline = line[1:]
            while newline[-1] in (u"|", u" "):
                newline = newline[:-1]

            #newline = re.sub('\<tableclass.*"\>', '', newline)
            #newline = re.sub('\<tablestyle.*"\>', '', newline)
            newline = newline.rstrip().rstrip('||').rstrip()
            #newline = re.sub(r'.*<([a-zA-Z\/][^>]*)>.*', r'\1 |', newline)
            #newline = re.sub(r'<([a-zA-Z\/][^>]*)>', r'\1 |', newline)
            newline = re.sub(r'<tablestyle[=a-zA-Z\/][^>]*>', r'', newline)
            # Ugh nasty
            if newline.find('rowstyle') != -1:
                newline = re.sub(r'<([a-zA-Z\/][^>]*)>', r'\1 \n|', newline)
                newline = newline.replace('|rowstyle', 'style')
                newline = newline.replace('| rowstyle', 'style')
                result.append(u"\n|- %s" % newline)
            else:
                newline = newline.replace('<style', 'style')
                newline = newline.replace('">', '" |')
                newline = newline.replace('" >', '" |')
                newline = newline.replace("'>", "' |")
                newline = newline.replace("' >", "' |")
                if not has_class:
                    result.append(u"\n|-")
                    result.append("\n" + newline)
        else:
            if in_table:
                if has_class:
                    result.append(u"\n}}\n")
                else:
                    result.append(u"\n|}\n")
                in_table = False
                has_class=False
            result.append(line)

    return u''.join(result)

def _escape(line):
    return (line, {})
#    line = line.replace(u">", u"&gt;")
#    line = line.replace(u"<", u"&lt;")
#    line = re.sub(ur'&(?![a-z]+;)', u"&amp;", line)

def _fix_comments(line):
    if line.startswith(u"##"):
        line = u"<!--%s-->\n" % line[2:]

    return (line, {})

def _fix_redirect(line):
    if line.startswith(u"#redirect"):
        line = u"#REDIRECT %s" % line.split(" ")[2:]
    return(line, {})

def _find_meta(line):
    try:
        if line.startswith(u"#"):
            (name, value) = line[1:].split(u" ", 1)
            return (u"", { name: value })
    except:
        pass

    return (line, {})

def _studlycaps(line):
#    line = re.sub(ur'\b(?<!\!)([A-Z][a-z]+?[A-Z][A-Za-z0-9]*)', 
#                  ur'[[\1]]', line)
    return (line, {})

def _fix_anchors(line):
    
    if line.find('[[Anchor') != -1 or line.find('[[ Anchor') != -1:
        line = line.replace('[[', '{{')
        line = line.replace(')]]', '}}')
        line = line.replace(') ]]', '}}')
        line = line.replace('(', '|')
#    if line.find('<<Anchor(') != -1:
#        line = re.subn(ur'\<\<Anchor\(', '{{Anchor|', line, 1)[0]
#        line = re.subn(ur'\)\>\>', '}}', line, 1)[0]
    return (line, {})

def _fix_bullets(line):
    if re.match(ur'^\s+\*', line):
        while line[0].isspace():
            line = line[1:]

    return (line, {})

def _fix_numlists(line):
    if re.match(ur'^\s+1\.', line):
        while line[0].isspace():
            line = line[1:]
        line = u"# %s" % line[2:]

    return (line, {})

def _fix_admonition(line):
#    while line.find(ur'[[Admonition') != -1:
#        line = re.subn(ur'\[\[Admonition', '<<Admonition', line, 1)[0]
#        line = re.subn(ur'\]\]', '>>', line, 1)[0]
    return (line, {})

def _fix_get_val(line):
    if line.find('Category:') != -1:
        return (line, {})
    split_line = line.split(']]')
    e = []
    for s in split_line:
        if s.find('[[GetVal') != -1:
            s = s.replace('[[GetVal', '{{Template:',1)
            s = s.replace(',', '/', 1)
            s = s.replace('(', '', 1)
            s = s.replace(')', '', 1)
            s = s.strip() + '}}\n'
        e.append(s)
    line = ' '.join(e)

    return (line, {})

def _fix_include(line):
    if line.find('[[Include') != -1:
        line = line.replace('[[Include(', '{{:')
        line = line.replace(')]]', '}}')
    return (line, {})

def _fix_pre(line):
    if line.find('{{{') != -1 and line.find('}}}') != -1:
        line = re.sub(r'\{\{\{', "<code>", line)
        line = re.sub(r'\}\}\}', "</code>", line)
    else:
        line = re.sub(r'\{\{\{', "<pre>", line)
        line = re.sub(r'\}\}\}', "</pre>", line)
    return (line, {})

#def _fix_big_links(line):
#    line = re.sub(ur'\[:([^:]+):([^]]+)]', ur'[\1|\2]', line)
#    return (line, {})

def _fix_code_blocks(line):
    while line.find('`') != -1:
        line = re.subn(ur'`', '<code>', line, 1)[0]
        line = re.subn(ur'`', '</code>', line, 1)[0]
    return (line, {})

def _unspace_text(line):
    if len(line) > 0 and line[0] == " ":
        while len(line) > 0 and line[0] == " ":
            line = line[1:]
        line = ": " + line
    #line = u": %s" % line.lstrip(' ')

    return (line, {})

def _kill_link_prefixes(line):
    line = re.sub(ur'[A-Za-z]+\:\[\[', u"[[", line)
    return (line, {})

def _fix_line_breaks(line):
    line = line.replace('[[BR]]', '<BR>')
    return (line, {})

def _fix_categories(line):
    if line.startswith('Category'):
        line = line.replace('Category', '[[Category:')
        line = line.strip() + ']]'

        #line = line.replace('\n', ']]')

    return (line, {})

def _fix_headers(line):
    ''' This is Fedora specific '''
    line = line.replace('<h2>', '==')
    line = line.replace('</h2>', '==')
    line = line.replace('<H2>', '==')
    line = line.replace('</H2>', '==')
    return (line, {})

def _fix_links(line):
    if line.find('Category:') != -1:
        return (line, {})
    split_line = line.split(']')
#while f.find('[:') != -1:
    e = []
    for s in split_line:
#        sys.stderr.write("s before: %s\n" % s)
        if s.find('[:') != -1:
            s = s.replace('[:', '[[',1)
            tmp = s.split('[[')
            #sys.stderr.write("0: " + tmp[0])
            #sys.stderr.write("1: " + tmp[1])
            s = tmp[0] + '[[' + tmp[1].replace(':', '| ', 1)
            s = s.replace(']', ']]', 1)
            s = s + ']]'
        elif s.find('[') != -1:
            s = s + ']'
        #sys.stderr.write("s after: %s\n" % s)
        e.append(s)
    line = ' '.join(e)
#    line = re.sub(ur'\[\:(.*)\:(.*)\]', ur"[[\1 |\2]]", line)
#    line = re.sub(r'\[\[', "[[ ", line)
#    line = re.sub(r'\]\]', " ]]", line)
    return (line, {})

def _remove_toc(line):
    line = line.replace('[[TableOfContents]]', '')
    line = line.replace('[[ TableOfContents ]]', '')
    return (line, {})

def _fix_attachments(line, page_name):
    result = []
    if line.find('attachment:') != -1:
        dest = page_name.replace('(2f)', '_') + '_'
        skipFirst=1
        for l in line.split('attachment:'):
            if skipFirst==1:
                result.append(l)
                skipFirst=0
                continue
            l = "[[Image:%s%s" % (dest, l)
            l = re.subn(ur'([A-Za-z0-9:_\.\-]*)([A-Za-z0-9])', ur'\1\2]]', l, 1)[0]
            result.append(l)
        line = ''.join(result)
        # crazy hack, fix triples (they happen from linked moin images)
        line = line.replace('[[[', '[[')
        line = line.replace(']]]', ']]')
    return (line)


chain = [ _remove_toc, _fix_line_breaks, _fix_categories, _fix_headers, _fix_anchors, 
          _fix_include, _fix_get_val, _fix_links, _escape,
          _fix_redirect, _fix_comments, _find_meta, _studlycaps, _fix_bullets,
          _fix_numlists, _unspace_text, _kill_link_prefixes, _fix_code_blocks,
          _fix_pre, _fix_admonition ]

class MoinWiki(object):
    def __init__(self, wiki_path):
        if not os.path.isdir(wiki_path):
            raise RuntimeError(u"%s: incorrect path to wiki" %
                wiki_path)
        if not os.path.exists(u"%s/pages/FrontPage/current" %
            wiki_path):
            raise RuntimeError(u"%s: path does not appear to be a"
                u" MoinMoin wiki" % wiki_path)

        self.wiki_path = wiki_path

    def _check_valid_page(self, orig_page_name):
        if not os.path.exists(u"%s/pages/%s/current" 
                              % (self.wiki_path, orig_page_name)):
            raise RuntimeError(u"page %s does not exist in"
                u" wiki at %s" % (self.wiki_path, orig_page_name))

    def _translate_page_name(self, page_name):
        new_page_name = page_name
        if page_name.find(u"(") != -1:
            for match in re.finditer(ur'\((\w+)\)', page_name):
                hex = u"\"\\x%s\"" % match.group(1)
                if len(hex) > 6:
                    #hex = u"%s\\x%s" % (hex[:5], hex[5:])
                    hex = match.group(1).decode('hex').decode('utf-8')
                try:
                    newchar = eval(hex) # WTH? -iva
                except ValueError:
                    raise RuntimeError(u"invalid escaping of %s: %s" %
                        (page_name, hex))
                except SyntaxError:
                    newchar = hex
                try:
                    new_page_name = new_page_name.replace(match.group(0), newchar)
                except:
                    sys.stderr.write("Error2 - on page: %s\n" % page_name)

        return new_page_name

    def _chain_translate_file(self, f, page_name):
        result = []
        resultmeta = {}
        if page_name.find('MoinEditorBackup') != -1:
            return (result, resultmeta)
        for line in f:
            for chaincall in chain:
                (line, meta) = chaincall(line)
                resultmeta.update(meta)
            # fix_attachments is fedora specific and requites pagename
            line = _fix_attachments(line, page_name)
            result.append(line)

        result = _table_xlat(u''.join(result))

        return (result, resultmeta)

    def has_page(self, page_name):
        try:
            self._check_valid_page(page_name)
        except RuntimeError:
            return False

        return True

    def get_orig_page_names(self):
        for page in os.listdir(self.wiki_path + u"/pages"):
            try:
                self._check_valid_page(page)
            except RuntimeError:
                continue

            yield page

    def get_page(self, orig_page_name):
        self._check_valid_page(orig_page_name)
        page_name = self._translate_page_name(orig_page_name)

        results = { u"name": page_name,
                    u"orig-name": orig_page_name }

        page_path = u"%s/pages/%s" % (self.wiki_path, orig_page_name)
        revnum_file = codecs.open(u"%s/current" % page_path, 'r',
            'utf-8')
        revnum = revnum_file.read()
        revnum_file.close()
        revnum = revnum.rstrip(u'\n')

        while not os.path.exists(u"%s/revisions/%s" % (page_path, revnum)):
            revnum_len = len(revnum)
            #revnum = str(int(revnum) - 1)
            revnum = int(revnum) - 1
            revnum = u'%0*d' % (revnum_len, revnum)

        text_file = codecs.open(u"%s/revisions/%s" % (page_path,
            revnum), 'r', 'utf-8')
        (results[u"text"], results[u"meta"]) = \
            self._chain_translate_file(text_file, orig_page_name)
        #sys.stderr.write("page_path: %s\n" % orig_page_name)
        text_file.close()

        return results

    def get_pages(self):
        for page in self.get_orig_page_names():
            yield self.get_page(page)

class MWExport(object):
    def __init__(self, source):
        self.source_wiki = source

        self.etroot = etree.Element(u"mediawiki")
        self.etroot.set(u"xml:lang", u"en")
        self.etdoc = etree.ElementTree(self.etroot)

        self.timestr = mx.DateTime.ISO.strUTC(mx.DateTime.utc())
        self.timestr = self.timestr.replace(u" ", u"T")
        self.timestr = self.timestr.replace(u"+0000", u"Z")

    def _create_blank_page(self):
        mwpage = etree.Element(u"page")

        mwpagetitle = etree.SubElement(mwpage, u"title")

        mwrevision = etree.SubElement(mwpage, u"revision")
        mwrevtime = etree.SubElement(mwrevision, u"timestamp")
        mwrevtime.text = self.timestr

        mwcontrib = etree.SubElement(mwrevision, u"contributor")
        mwuser = etree.SubElement(mwcontrib, u"username")
        mwuser.text = u"ImportUser"

        mwcomment = etree.SubElement(mwrevision, u"comment")
        mwcomment.text = u"Imported from MoinMoin"

        mwtext = etree.SubElement(mwrevision, u"text")

        return mwpage

    def add_page(self, page):
        mwpage = self._create_blank_page()
        mwpage[0].text = page[u"name"]
        for subelem in mwpage[1]:
            if subelem.tag == u"text":
                subelem.text = page[u"text"]
        self.etroot.append(mwpage)

        talk_page_content = []

        if self.source_wiki.has_page(page[u"name"] + u"(2f)Comments"):
            comment_page = self.source_wiki.get_page(page[u"name"] + 
                                                     u"(2f)Comments")
            talk_page_content.append(comment_page[u"text"])

        if len(page[u"meta"]) > 0:
            talk_page_content.append(u"""

The following metadata was found in MoinMoin that could not be converted
to a useful value in MediaWiki:

""")
            for key, value in page[u"meta"].iteritems():
                talk_page_content.append(u"* %s: %s\n" % (key, value))

        if talk_page_content:
            mwpage = self._create_blank_page()
            mwpage[0].text = u"Talk:%s" % page[u"name"]
            for subelem in mwpage[1]:
                if subelem.tag == u"text":
                    subelem.text = u''.join(talk_page_content)
            self.etroot.append(mwpage)

    def add_pages(self):
        for page in self.source_wiki.get_pages():
            if not page[u"name"].endswith(u"(2f)Comments"):
                self.add_page(page)

    def write(self, f):
        self.etdoc.write(f)

def main():
    wiki_path = sys.argv[1]

    export = MWExport(MoinWiki(wiki_path))
    export.add_pages()
    out = codecs.EncodedFile(sys.stdout, 'utf-8')
    out.write(u"<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
    export.write(out)

if __name__ == "__main__":
    main()
