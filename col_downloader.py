#!/usr/bin/env python
# -*- coding: utf-8 -*-
## col_downloader.py
## A helpful tool to fetch data from website & generate mdx source file
##
## This program is a free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, version 3 of the License.
##
## You can get a copy of GNU General Public License along this program
## But you can always get it from http://www.gnu.org/licenses/gpl.txt
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.
import os
import re
import random
import string
import urllib
import fileinput
import requests
from os import path
from datetime import datetime
from multiprocessing import Pool
from collections import OrderedDict


MAX_PROCESS = 10
STEP = 8000
F_WORDLIST = 'wordlist.txt'
F_THESLIST = 'theslist.txt'


def fullpath(file, suffix='', base_dir=''):
    if base_dir:
        return ''.join([os.getcwd(), path.sep, base_dir, file, suffix])
    else:
        return ''.join([os.getcwd(), path.sep, file, suffix])


def readdata(file, base_dir=''):
    fp = fullpath(file, base_dir=base_dir)
    if not path.exists(fp):
        print("%s was not found under the same dir of this tool." % file)
    else:
        fr = open(fp, 'rU')
        try:
            return fr.read()
        finally:
            fr.close()
    return None


def dump(data, file, mod='w'):
    fname = fullpath(file)
    fw = open(fname, mod)
    try:
        fw.write(data)
    finally:
        fw.close()


def removefile(file):
    if path.exists(file):
        os.remove(file)


def info(l, s='word'):
    return '%d %ss' % (l, s) if l>1 else '%d %s' % (l, s)


def randomstr(digit):
    return ''.join(random.sample(string.ascii_lowercase, 1)+
        random.sample(string.ascii_lowercase+string.digits, digit-1))


def getpage(link, BASE_URL=''):
    r = requests.get(''.join([BASE_URL, link]), timeout=10, allow_redirects=False)
    if r.status_code == 200:
        return r.content
    else:
        return None


def getwordlist(file, base_dir='', tolower=False):
    words = readdata(file, base_dir)
    if words:
        wordlist = []
        p = re.compile(r'\s*\n\s*')
        words = p.sub('\n', words).strip()
        for word in words.split('\n'):
            try:
                w, u = word.split('\t')
                if tolower:
                    wordlist.append((w.strip().lower(), u.strip().lower()))
                else:
                    wordlist.append((w, u))
            except Exception, e:
                import traceback
                print traceback.print_exc()
                print word
        return wordlist
    print("%s: No such file or file content is empty." % file)
    return []


class downloader:
#common logic
    def __init__(self, name, diff):
        self.__session = None
        self.DIC_T = name
        self.__diff = diff
        self.__redirect = True

    @property
    def session(self):
        return self.__session

    @property
    def diff(self):
        return self.__diff

    def set_redirect(self, allow_redirect):
        self.__redirect = allow_redirect

    def login(self, ORIGIN='', REF=''):
        HEADER = 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.102 Safari/537.36'
        self.__session = requests.Session()
        self.__session.headers['User-Agent'] = HEADER
        self.__session.headers['Origin'] = ORIGIN
        self.__session.headers['Referer'] = REF

    def logout(self):
        pass

    def makeurl(self, cur):
        pass

    def getcref(self, url, raiseErr=True):
        pass

    def makeword(self, page, word, words, logs, d_app):
        pass

    def formatEntry(self, key, line, crefs, logs):
        pass

    def getpage(self, link, BASE_URL=''):
        r = self.__session.get(''.join([BASE_URL, link]), timeout=10, allow_redirects=False)
        if r.status_code == 200:
            return (r.status_code, r.content)
        elif r.status_code==301 and self.__redirect:
            return (r.status_code, r.headers['Location'])
        return (r.status_code, None)

    def cleansp(self, html):
        p = re.compile(r'\s+')
        html = p.sub(' ', html)
        p = re.compile(r'<!--[^<>]+?-->')
        html = p.sub('', html)
        p = re.compile(r'\s*<br/?>\s*')
        html = p.sub('<br>', html)
        p = re.compile(r'(\s*<br>\s*)*(<hr[^>]*>)(\s*<br>\s*)*', re.I)
        html = p.sub(r'\2', html)
        p = re.compile(r'(\s*<br>\s*)*(<(?:/?(?:div|p)[^>]*|br)>)(\s*<br>\s*)*', re.I)
        html = p.sub(r'\2', html)
        p = re.compile(r'\s*(<(?:/?(?:div|p|ul|li)[^>]*|br)>)\s*', re.I)
        html = p.sub(r'\1', html)
        p = re.compile(r'\s+(?=[,\.;\?\!])')
        html = p.sub(r'', html)
        p = re.compile(r'\s+(?=</?\w+>[\)\]\s])')
        html = p.sub(r'', html)
        return html

    def getcreflist(self, file, base_dir=''):
        words = readdata(file, base_dir)
        if words:
            p = re.compile(r'\s*\n\s*')
            words = p.sub('\n', words).strip()
            crefs = {}
            for word in words.split('\n'):
                k, v = word.split('\t')
                crefs[urllib.unquote(k).strip().lower()] = v.strip()
                crefs[v.strip().lower()] = v.strip()
            return crefs
        print("%s: No such file or file content is empty." % file)
        return {}

    def __mod(self, flag):
        return 'a' if flag else 'w'

    def __dumpwords(self, sdir, words, sfx='', finished=True):
        f = fullpath('rawhtml.txt', sfx, sdir)
        if len(words):
            mod = self.__mod(sfx)
            fw = open(f, mod)
            try:
                [fw.write('\n'.join([en[0], en[1], '</>\n'])) for en in words]
            finally:
                fw.close()
        elif not path.exists(f):
            fw = open(f, 'w')
            fw.write('\n')
            fw.close()
        if sfx and finished:
            removefile(fullpath('failed.txt', '', sdir))
            l = -len(sfx)
            cmd = '\1'
            nf = f[:l]
            if path.exists(nf):
                msg = "Found rawhtml.txt in the same dir, delete?(default=y/n)"
                cmd = 'y'#raw_input(msg)
            if cmd == 'n':
                return
            elif cmd != '\1':
                removefile(nf)
            os.rename(f, nf)

    def __fetchdata_and_make_mdx(self, arg, part, suffix=''):
        sdir, d_app = arg['dir'], OrderedDict()
        words, logs, crefs, count, failed = [], [], {}, 1, []
        leni = len(part)
        while leni:
            for cur, url in part:
                if count % 100 == 0:
                    print ".",
                    if count % 1000 == 0:
                        print count,
                try:
                    page = self.getpage(self.makeurl(url))
                    if page[1]:
                        if self.makeword(page, cur, words, logs, d_app):
                            crefs[url] = cur
                            count += 1
                    else:
                        logs.append("I01: cannot find '%s'" % cur)
                        if page[0] == 301:
                            failed.append((cur, url))
                except Exception, e:
                    import traceback
                    print traceback.print_exc()
                    print "%s failed, retry automatically later" % cur
                    failed.append((cur, url))
            lenr = len(failed)
            if lenr >= leni:
                break
            else:
                leni = lenr
                part, failed = failed, []
        print "%s browsed" % info(count-1),
        if crefs:
            mod = self.__mod(path.exists(fullpath('cref.txt', base_dir=sdir)))
            dump(''.join(['\n'.join(['\t'.join([k, v]) for k, v in crefs.iteritems()]), '\n']), ''.join([sdir, 'cref.txt']), mod)
        if d_app:
            mod = self.__mod(path.exists(fullpath('appd.txt', base_dir=sdir)))
            dump(''.join(['\n'.join(['\t'.join([k, v]) for k, v in d_app.iteritems()]), '\n']), ''.join([sdir, 'appd.txt']), mod)
        if failed:
            dump(''.join(['\n'.join(['\t'.join([w, u]) for w, u in failed]), '\n']), ''.join([sdir, 'failed.txt']))
            self.__dumpwords(sdir, words, '.part', False)
        else:
            print ", 0 word failed"
            self.__dumpwords(sdir, words, suffix)
        if logs:
            mod = self.__mod(path.exists(fullpath('log.txt', base_dir=sdir)))
            dump('\n'.join(logs), ''.join([sdir, 'log.txt']), mod)
        return d_app

    def start(self, arg):
        import socket
        socket.setdefaulttimeout(120)
        import sys
        reload(sys)
        sys.setdefaultencoding('utf-8')
        sdir = arg['dir']
        fp1 = fullpath('rawhtml.txt.part', base_dir=sdir)
        fp2 = fullpath('failed.txt', base_dir=sdir)
        fp3 = fullpath('rawhtml.txt', base_dir=sdir)
        if path.exists(fp1) and path.exists(fp2):
            print ("Continue last failed")
            failed = getwordlist('failed.txt', sdir)
            return self.__fetchdata_and_make_mdx(arg, failed, '.part')
        elif not path.exists(fp3):
            print ("New session started")
            return self.__fetchdata_and_make_mdx(arg, arg['alp'])

    def combinefiles(self, dir):
        print "combining files..."
        times = 0
        for d in os.listdir(fullpath(dir)):
            if path.isdir(fullpath(''.join([dir, d, path.sep]))):
                times += 1
        for fn in ['cref.txt', 'log.txt']:
            fw = open(fullpath(''.join([dir, fn])), 'w')
            for i in xrange(1, times+1):
                sdir = ''.join([dir, '%d'%i, path.sep])
                if path.exists(fullpath(fn, base_dir=sdir)):
                    fw.write('\n'.join([readdata(fn, sdir).strip(), '']))
            fw.close()
        words, logs = [], []
        crefs = self.getcreflist('cref.txt', dir)
        fnm = 'COT' if self.diff=='t' else self.DIC_T
        fw = open(fullpath(''.join([dir, fnm, path.extsep, 'txt'])), 'w')
        d_uni = {}
        try:
            for i in xrange(1, times+1):
                sdir = ''.join([dir, '%d'%i, path.sep])
                file = fullpath('rawhtml.txt', base_dir=sdir)
                lns = []
                for ln in fileinput.input(file):
                    ln = ln.strip()
                    if ln == '</>':
                        ukey = lns[0].lower().strip()
                        if not ukey in d_uni:
                            entry = self.formatEntry(lns[0], lns[1], crefs, logs)
                            if entry:
                                fw.write(''.join([entry, '\n']))
                                d_uni[ukey] = None
                                words.append(lns[0])
                        del lns[:]
                    elif ln:
                        lns.append(ln)
        finally:
            fw.close()
        print "%s totally" % info(len(words))
        fw = open(fullpath(''.join([dir, 'words.txt'])), 'w')
        fw.write('\n'.join(words))
        fw.close()
        if logs:
            mod = self.__mod(path.exists(fullpath('log.txt', base_dir=dir)))
            dump('\n'.join(logs), ''.join([dir, 'log.txt']), mod)


def f_start((obj, arg)):
    return obj.start(arg)


def multiprocess_fetcher(dir, d_refs, wordlist, obj, base):
    times = int(len(wordlist)/STEP)
    pl = [wordlist[i*STEP: (i+1)*STEP] for i in xrange(0, times)]
    pl.append(wordlist[times*STEP:])
    times = len(pl)
    if not path.exists(fullpath(dir)):
        os.mkdir(dir)
    for i in xrange(1, times+1):
        subdir = ''.join([dir, '%d'%(base+i)])
        subpath = fullpath(subdir)
        if not path.exists(subpath):
            os.mkdir(subpath)
    pool = Pool(MAX_PROCESS)
    d_app = OrderedDict()
    leni = times+1
    while 1:
        args = []
        for i in xrange(1, times+1):
            sdir = ''.join([dir, '%d'%(base+i), path.sep])
            file = fullpath(sdir, 'rawhtml.txt')
            if not(path.exists(file) and os.stat(file).st_size):
                param = {}
                param['alp'] = pl[i-1]
                param['dir'] = sdir
                args.append((obj, param))
        lenr = len(args)
        if len(args) > 0:
            if lenr >= leni:
                print "The following parts cann't be fully downloaded:"
                for arg in args:
                    print arg[1]['dir']
                break
            else:
                dts = pool.map(f_start, args)#f_start(args[0])#for debug
                [d_app.update(dict) for dict in dts]
        else:
            break
        leni = lenr
    dt = OrderedDict()
    for k, v in d_app.iteritems():
        if not k in d_refs:
            dt[k] = v
    return times, dt.items()


def getlink(diff, ap, dict):
    subu = '-thesaurus' if diff=='t' else ''
    p1 = re.compile(''.join([r'<a\s+href="(http://www\.collinsdictionary\.com/browse/english', subu, '/\w/[^<>"]+)"']), re.I)
    p2 = re.compile(''.join([r'<a\s+href="http://www\.collinsdictionary\.com/dictionary/english', subu, '/([^<>"]+)"[^<>]*>\s*(.+?)\s*</a>']), re.I)
    las, failed = p1.findall(ap), []
    if las:
        leni = len(las)
        while leni:
            for la in las:
                try:
                    lp = getpage(la)
                    for url, word in p2.findall(lp):
                        dict[word] = url
                except Exception, e:
                    import traceback
                    print traceback.print_exc()
                    print "%s failed, retry automatically later" % la
                    failed.append(la)
            lenr = len(failed)
            if lenr >= leni:
                break
            else:
                leni, las, failed = lenr, failed, []
        assert not failed
    else:
        for url, word in p2.findall(ap):
            dict[word] = url


def getalphadict((a, diff)):
    dict = OrderedDict()
    ap = getpage(a)
    getlink(diff, ap, dict)
    return dict


def makewordlist(diff, file):
    fp = fullpath(file)
    if path.exists(fp):
        return OrderedDict(getwordlist(file))
    else:
        print "Get word list: start at %s" % datetime.now()
        url = 'http://www.collinsdictionary.com/'
        if diff == 't':
            url = ''.join([url, 'english-thesaurus'])
        page = getpage(url)
        p = re.compile(r'[\n\r]+')
        page = p.sub(r'', page)
        p = re.compile(r'(<ul class="alphabet[^<>"]*">)(.+?)(?=</ul>)', re.I)
        m = p.search(page)
        sub1 = '-thesaurus' if diff=='t' else ''
        sub2 = 'synonyms' if diff=='t' else 'words'
        p = re.compile(''.join([r'<a\s+href="(http://www\.collinsdictionary\.com/browse/english', sub1, '/', sub2, '-starting-with-\w+)">\w</a>']), re.I)
        pool = Pool(10)
        alphadicts = pool.map(getalphadict, [(a, diff) for a in p.findall(m.group(2))])
        dt = OrderedDict()
        [dt.update(dict) for dict in alphadicts]
        dump(''.join(['\n'.join(['\t'.join([k, v]) for k, v in dt.iteritems()]), '\n']), file)
        print "%s totally" % info(len(dt))
        print "Get word list: finished at %s" % datetime.now()
        return dt


def is_complete(path, ext='.part'):
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(ext):
                return False
    return True


class dic_downloader(downloader):
#COL downloader
    def __init__(self, diff):
        downloader.__init__(self, 'COL', diff)
        subu = '-thesaurus' if diff=='t' else ''
        self.__base_url = ''.join(['http://www.collinsdictionary.com/dictionary/english', subu, '/'])

    def makeurl(self, cur):
        return ''.join([self.__base_url, cur])

    def getcref(self, url, raiseErr=True):
        p = re.compile(''.join([self.__base_url, r'(.+)(?=$)']), re.I)
        m = p.search(url)
        if not m and raiseErr:
            raise AssertionError('%s : Wrong URL'%url)
        return m.group(1) if m else None

    def __preformat(self, page):
        p = re.compile(r'[\n\r]+')
        page = p.sub(r'', page)
        p = re.compile(r'[\t]+|&nbsp;')
        page = p.sub(r' ', page)
        p = re.compile(r'<!--[^<>]+?-->')
        page = p.sub(r'', page)
        p = re.compile(r'(</?)strong(?=[^>]*>)')
        page = p.sub(r'\1b', page)
        return page

    def __rec_url(self, p, div, d_app):
        for url, word in p.findall(div):
            url = urllib.unquote(url).strip().lower()
            if not url in d_app:
                d_app[url] = word

    def makeword(self, rawpage, word, words, logs, d_app):
        status, page, exist = rawpage[0], rawpage[1], False
        if status == 301:
            ref = urllib.unquote(self.getcref(page, False))
            if ref:
                p = re.compile(r'[\s\-\']|\.$')
                if p.sub(r'', word).lower() != p.sub(r'', ref).lower():
                    words.append([word, ''.join(['@@@LINK=', ref])])
                    exist = True
            else:
                logs.append("E01: '%s' = wrong URL, please check" % word)
        else:
            page = self.__preformat(page)
            p = re.compile(r'(<div class="nearby_entries">\s*<h2>Browse nearby words</h2>).+?(?=</ul>)', re.I)
            m = p.search(page)
            if not m:
                print "'%s' has no Nearby words" % word
                logs.append("W01:'%s' has no Nearby words" % word)
            else:
                p = re.compile(''.join([r'<a\s+href="', self.__base_url, '([^<>"]+)">\s*(.+?)\s*</a>']), re.I)
                self.__rec_url(p, m.group(0), d_app)
                if self.diff == 't':
                    q = re.compile(r'<a class="xr_ref_link" href="([^<>"#]+)#?[^<>"]*">([^<>]+)</a>', re.I)
                    self.__rec_url(q, page, d_app)
            p = re.compile(r'<div\s+class="homograph-entry">', re.I)
            if not p.search(page):
                logs.append("I02: '%s' is not found in DIC" % word)
            else:
                p = re.compile(r'<div\s+class="definition_content col main_bar">(.+?)<div id=[\'"]ad_btmslot_a\b[^<>]*>\s*<script', re.I)
                m1 = p.search(page)
                p = re.compile(r'(?<=<span>Word Frequency</span>)\s*<div[^<>]*>', re.I)
                m2 = p.search(page)
                freq = '' if not m2 else ''.join(['###', m2.group(0), '</div>'])
                worddef = self.cleansp(''.join([m1.group(1), freq])).strip()
                words.append([word, worddef])
                exist = True
        return exist

    def __repcls(self, m):
        tag = m.group(1)
        cls = m.group(3)
        self.span = {'synonym odd': 'xdu', 'synonym even': 'egz', 'synonym even first': 'efu',
        'syn_prefix': 'sak', 'pos': 'sg0', 'gramGrp': 'kgo', 'drv': 'w4y', 'def': 'sd9', 'lbl register': 'rgm',
        'infl_partial': 'fvd', 'orth': 'u9w', 'pron': 'kf5', 'var': 'vla', 'lbl misc': 'iau', 'lbl': 'czw',
        'lbl geo': 'ggs', 'smallcaps': 's4k', 'colloc': 'h5w', 'subc': 'n7y', 'roman': 'r4h',
        'lbl subj': 'uyp', 'xr_ref': 'xf7', 'xr': 'x3h', 'lbl gram': 'sut', 'author': 'n6a',
        'infl': 'qqb', 'ant': 'opn', 'lbl lang': 'hpa', 'lbl tm': 'bdm', 'syn': 'fxr',
        'infl_': 'st0'}
        self.div = {'thesaurus_synonyms': 'xvu', 'lang_en-gb': 'm6d', 'etym hom-subsec': 'roj',
        'context_box context_box_ENGLISH_DICTIONARY hom-subsec': 'sib', 're hom-subsec': 'sbt',
        'hom': 'x5z', 'definitions hom-subsec': 'mh1', 'homograph-entry': 'j84',
        'context_box context_box_ENGLISH_DICTIONARY term-subsec': 't6l', 'inflected_forms': 'ddh',
        'similar-words hom-subsec': 'klp', 'semantic': 'yxc', 'xr hom-subsec': 'z1r'}
        self.ol = {'sense_list level_0': 'o8h', 'sense_list level_1': 'oyu',
        'sense_list level_2': 'ohr', 'sense_list level_3': 'heo'}
        self.li = {'sense_list_item level_1': 'iji', 'sense_list_item level_2': 'iiz'}
        self.h1 = {'orth h1_entry': 'f9d'}
        self.h2 = {'h2_entry': 'h2k', 'sc h2_entry': 'fhq', 'orth h1_entry': 'quf',
        'gramGrp h2_entry': 'yeq'}
        self.h3 = {'h2_entry': 'qb3', 'sc h2_entry': 's5r', 'h3_entry': 'sqw',
        'gramGrp h3_entry': 'jgs', 'gramGrp h2_entry': 'g1p', 'gramGrp entry_h3': 'hni'}
        self.h4 = {'h3_entry': 'tsw', 'gramGrp h3_entry': 'jnw', 'gramGrp entry_h3': 'hyt'}
        self.p = {'phrase': 'pkh'}
        self.em = {'hi': 'ue8', 'italics': 'ilg'}
        self.sup = {'homnum': 'nfl'}
        self.ul = {'quotations_list': 'uoh', 'sense_list level_1': 'cfu'}
        self.cite = {'bibl': 'bwx'}
        if tag=='span' and cls in self.span:
            return ''.join([tag, m.group(2), self.span[cls]])
        elif tag=='div' and cls in self.div:
            return ''.join([tag, m.group(2), self.div[cls]])
        elif tag=='ol' and cls in self.ol:
            return ''.join([tag, m.group(2), self.ol[cls]])
        elif tag=='li' and cls in self.li:
            return ''.join([tag, m.group(2), self.li[cls]])
        elif tag=='h1' and cls in self.h1:
            return ''.join([tag, m.group(2), self.h1[cls]])
        elif tag=='h2' and cls in self.h2:
            return ''.join([tag, m.group(2), self.h2[cls]])
        elif tag=='h3' and cls in self.h3:
            return ''.join([tag, m.group(2), self.h3[cls]])
        elif tag=='h4' and cls in self.h4:
            return ''.join([tag, m.group(2), self.h4[cls]])
        elif tag=='p' and cls in self.p:
            return ''.join([tag, m.group(2), self.p[cls]])
        elif tag=='em' and cls in self.em:
            return ''.join([tag, m.group(2), self.em[cls]])
        elif tag=='sup' and cls in self.sup:
            return ''.join([tag, m.group(2), self.sup[cls]])
        elif tag=='ul' and cls in self.ul:
            return ''.join([tag, m.group(2), self.ul[cls]])
        elif tag=='cite' and cls in self.cite:
            return ''.join([tag, m.group(2), self.cite[cls]])
        else:
            return m.group(0)

    def __replbl(self, m):
        lbl = ''.join([m.group(1), '.', m.group(2), ' '])
        p = re.compile(r'(\s*&amp;\s*)(<span class="lbl (?:geo|subj|register|misc|lang)">)', re.I)
        lbl = p.sub(r'\2\1', lbl)
        p = re.compile(r'\s*</span>\s*\(\s*<span class="lbl (?:geo|subj|register|misc|lang)">\s*', re.I)
        return p.sub(r'. ', lbl)

    def __repexp(self, m):
        text = m.group(2)
        p = re.compile(r'(</?)blockquote(?=>)', re.I)
        text, n = p.subn(r'\1p', text)
        if n > 6:
            img = 'ax'
            sty = ' style="display:none"'
        else:
            img = 'ac'
            sty = ''
        p = re.compile(r'(?<=<h2>Example Sentences)\s+Including[^<>]+(</h2>\s*<div )id="examples_box"(?=>)', re.I)
        text = p.sub(''.join(['<img src="', img, '.png" class="yjp" onclick="opc(this)">', r'\1class="d3l"', sty]), text)
        return ''.join([m.group(1), '"exq"', text])

    def __replink(self, m, crefs, key, logs):
        word = m.group(4)
        ref = urllib.unquote(m.group(2)).lower()
        if ref in crefs:
            ref = crefs[ref]
        else:
            logs.append("W02: %s The ref target of '%s' is not found" % (key, ref))
            p = re.compile(r'</?[^<>]+>')
            ref = p.sub(r'', word.replace('&amp;', '&')).strip()
        return ''.join([m.group(1), ref.replace('/', '%2F'), m.group(3), word])

    def __repb(self, m):
        text = m.group(1)
        p = re.compile(r'(</?)b(?=>)', re.I)
        return p.sub(r'\1i', text)

    def __repem(self, m):
        text = m.group(3)
        p = re.compile(r'(.+?)<em>(\w+)</em>(.+?)', re.I)
        text = p.sub(r'\1<i>\2</i>\3', text)
        return ''.join([m.group(1), text])

    def __addbr(self, m):
        p = re.compile(r'(?<=</span>)\s*,\s*(?=<span class="orth">)', re.I)
        return ''.join([m.group(1), '<div><span class="k75">', m.group(2), '</span>',
            p.sub('</div><div><span class="k75">\xE2\x87\x92</span> ', m.group(3)), '</div>'])

    def __addbr2(self, m):
        text = m.group(1)
        p = re.compile(r'\s*\xE2\x80\xA2\s*', re.I)
        return ''.join(['<div>', p.sub('</div><div>', text), '</div>'])

    def formatEntry(self, key, line, crefs, logs):
        if line.startswith('@@@'):
            lk, ref = line.split('=')
            ref = ref.strip().lower()
            if ref in crefs:
                p = re.compile(r'[\s\-\'/]|\.$')
                if p.sub(r'', key).lower() != p.sub(r'', crefs[ref]).lower():
                    return '\n'.join([key.replace('&amp;', '&'), ''.join(['@@@LINK=', crefs[ref].replace('/', '%2F')]), '</>'])
                else:
                    return ''
            else:
                logs.append("E02: The ref target of '%s' is not found" % key)
                return ''
        p = re.compile(r'<div id="translations-content"[^<>]*>.+?</div>', re.I)
        line = p.sub(r'', line)
        p = re.compile(r'<div id="translations_box"[^<>]*>.+?</div>', re.I)
        line = p.sub(r'', line)
        p = re.compile(r'<div class="breadcrumb"\s*id="search_found">.+?</div>', re.I)
        line = p.sub(r'', line)
        p = re.compile(r'<div class="breadcrumb clear">.+?</div>', re.I)
        line = p.sub(r'', line)
        p = re.compile(r'<h1[^<>]*>(?:Definitions|Synonyms) of[^<>]+</h1>', re.I)
        line = p.sub(r'', line)
        p = re.compile(r'(?<=<li)\s+style="list-style-type:\s*none"(?=>)', re.I)
        line = p.sub(r' class="d9y"', line)
        p = re.compile(r'\s*</span>\s*</span>\s*(<span class="def">)\s*(\.)\s*', re.I)
        line = p.sub(r'</span>\2</span> \1', line)
        p = re.compile(r'(?<=<span class="def">)\s*\.?\s*', re.I)
        line = p.sub(r'', line)
        p = re.compile(r'\s*(</span>)(<span class="def">)\s*', re.I)
        line = p.sub(r'\1 \2', line)
        p = re.compile(r'(?<=<li class=")[^<>"]+"\s*style="list-style-type:\s*none(?=">)', re.I)
        line = p.sub(r'lij', line)
        p = re.compile(r'(<li class="[^<>"]+")\s*value=[^<>]*(?=>)', re.I)
        line = p.sub(r'\1', line)
        p = re.compile(r'<h([23])[^<>]*>Definitions</h\1>', re.I)
        line = p.sub(r'', line)
        p = re.compile(r'<ol[^<>]*>\s*<li[^<>]*>\s*</li>\s*</ol>', re.I)
        line = p.sub(r'', line)
        p = re.compile(r'<([ou]l|li)[^<>]*>\s*</\1>', re.I)
        line = p.sub(r'', line)
        p = re.compile(r'<div [^<>]*class="[^<>"]*?term-subsec">\s*<h(\d)>[^<>]*</h\1>\s*</div>', re.I)
        line = p.sub(r'', line)
        n = 1
        while n:
            p = re.compile(r'<div(?: class="[^<>"]*?hom-subsec")?>\s*</div>', re.I)
            line, n = p.subn(r'', line)
        if self.diff != 't':
            p = re.compile(r'###(.+?)(?=$)', re.I)
            m = p.search(line)
            line = p.sub(r'', line)
            if m:
                p = re.compile(r'(?<=<div style=")[^<>"]+?;(background-position[^<>"]+?)\s*;background-image:url[^<>"]+("\s*title="[^<>"]+")[^<>]*(?=>)', re.I)
                freq = p.sub(r'\1px\2 class="ig6"', m.group(1))
                p = re.compile(r'(<h([12])[^<>]*>)(?=.+?</h\2>\s*<div\s+class="definitions hom-subsec"[^<>]*>)', re.I)
                line = p.sub(''.join([freq, r'\1']), line, 1)
            p = re.compile(r'<span class="hwd_sound">\s*<span class="hwd_sound">\s*(<img src=")[^<>]+?(onclick=)[^<>]+?[\'"]/sounds/([^<>]+?)\.mp3[^<>]+>\s*</span>\s*</span(?=>)', re.I)
            line = p.sub(r'''\1sp.png" class="ik4" \2"aes(this,'\3')"''', line)
            p = re.compile(r'\s*(<span\s+class="pron">)\s*', re.I)
            line = p.sub(r' \1', line)
            p = re.compile(r'(<span class="synonym[^<>"]*">[^<>]+)</a>(?=\s*</span>)', re.I)
            line = p.sub(r'\1', line)
            p = re.compile(r'(<h([34]) class="gramGrp entry_h3">related[^<>]+</h\2>)\s*([^<>]+)\s*(?=</div>)', re.I)
            line = p.sub(r'\1<span class="zkl">\3</span>', line)
            p = re.compile(r'<a class="link-right"[^<>]*>View thesaurus entry</a>', re.I)
            line = p.sub(r'', line)
            p = re.compile(r'\(?\s*(<span class="lbl (?:geo|subj|register|misc|lang)">.+?)\s*(</span>)\s*\)\s*', re.I)
            line = p.sub(self.__replbl, line)
            p = re.compile(r'(?<=<div )id="examples_box"\s+(class=)[^<>]+(>.+?</div>$)', re.I)
            line = p.sub(self.__repexp, line)
            line = line.replace('<span class=\'title\' lang=\'en-gb\'>', '<span class="tly">')
            line = line.replace('<span class=\'author\'>', '<span class="aox">')
            line = line.replace('<span class=\'year\'>', '<span class="yc1">')
            p = re.compile(r'(?<=<span class="pron">)\s*\((.+?)\)\s*(?=</span>)', re.I)
            line = p.sub(r'/\1/', line)
            p = re.compile(r'(?<=<li class=")sense_list_item level_3"\s*style="list-style-type:\s*square(?=">)', re.I)
            line = p.sub(r'ko0', line)
            p = re.compile(r'\(\s*<em( class=")hi(">)([^<>]+)(</)em>\s*\)', re.I)
            line = p.sub(r'<span\1igi\2<span>(</span>\3<span>)</span>\4span>', line)
            p = re.compile(r'([^>\s]\s*</span>)\s*(\xE2\x87\x92)(\s*.+?)(?=</li>)', re.I)
            line = p.sub(self.__addbr, line)
            p = re.compile(r'(\xE2\x87\x92)(?=\s*<span class="orth">)', re.I)
            line = p.sub(r'<span class="vif">\1</span>', line)
            p = re.compile(r'(<h(\d) class="[^<>"]+">)Word (Origin)\s*(?=</h\2>)', re.I)
            line = p.sub(r'\1\3', line)
            p = re.compile(r'(<h(\d)>Quotations) including.+?(?=</h\2>)', re.I)
            line = p.sub(r'\1', line)
            p = re.compile(r'(?<=<q>)\s*"*(.+?)"*\s*(?=</q>)', re.I)
            line = p.sub(r'\1', line)
            p = re.compile(r'(\[[^<>\]]+)(?=</span>)', re.I)
            line = p.sub(r'\1]', line)
            p = re.compile(r'\s*(</span>)\s*(<span class="gramGrp">)\s*(<span class="pos">)', re.I)
            line = p.sub(r'\1\2\3 ', line)
            p = re.compile(r'(<div id="synonyms_box"[^<>]*>\s*<h([23])[^<>]*>Synonyms)(?=</h\2>)', re.I)
            line = p.sub(r'\1<img src="ac.png" class="yjp" onclick="opc(this)">', line)
            p = re.compile(r'(<div id="quotation_box"[^<>]*>\s*<h([23])>Quotations.*?)(?=</h\2>)', re.I)
            line = p.sub(r'\1<img src="ac.png" class="yjp" onclick="opc(this)">', line)
            line = line.replace('<h2>', '<h2 class="iht">')
            line = line.replace('<h3>', '<h3 class="v3p">')
            if line.find('onclick="')>0:
                src = ''.join(['<script type="text/javascript"src="cl.js"></script><script>if(typeof(uc1)=="undefined"){var _l=document.getElementsByTagName("link");var _r=/',
                self.DIC_T, '.css$/;for(var i=_l.length-1;i>=0;i--)with(_l[i].href){var _m=match(_r);if(_m&&_l[i].id=="kc1"){document.write(\'<script src="\'+replace(_r,"cl.js")+\'"type="text/javascript"><\/script>\');break;}}}</script>'])
            else:
                src = ''
            lid, cls, cfs = 'id="kc1"', 'dxr', self.DIC_T
        else:
            p = re.compile(r'(?<=<div class=")xr[^<>"]+?hom-subsec(?=">\s*<span[^<>]+>[^<>]+</span>)', re.I)
            line = p.sub(r'wvh', line)
            p = re.compile(r'(?<=<div class=")xr[^<>"]+?hom-subsec(?=">)', re.I)
            line = p.sub(r'hdu', line)
            p = re.compile(r'(?<=<span class=")lbl(?=">[^<>]+</span>\s*<div class="wvh">)', re.I)
            line = p.sub(r'wve', line)
            p = re.compile(r'\s*\xE2\x80\xA2(.+?)(?=</li>)', re.I)
            line = p.sub(self.__addbr2, line)
            p = re.compile(r'(<li[^<>]*>)\s*(\=)', re.I)
            line = p.sub(r'\1<span class="bbw">\2</span>', line)
            p = re.compile(r'\(\s*(<span class="lbl (?:geo|subj|register|misc|lang)">)(.+?)(</span>)\s*\)', re.I)
            line = p.sub(r'\1<span>(</span>\2<span>)</span>\3', line)
            p = re.compile(r'(\s*&amp;\s*)(<span class="lbl (?:geo|subj|register|misc|lang)">)', re.I)
            line = p.sub(r'\2\1', line)
            p = re.compile(r'(?<=<b>opp)osites:\s*(</b>)', re.I)
            line = p.sub(r'\1 ', line)
            p = re.compile(r'(?<=<span class="subc">\()(.+?)(?=\))', re.I)
            line = p.sub(self.__repb, line)
            p = re.compile(r'(<h([1-4])[^<>]*>)(.+?)(?=</h\2>)', re.I)
            line = p.sub(self.__repem, line)
            lid, src, cls, cfs = '', '', 'tvr', 'COT'
        p = re.compile(r'(<span class="lbl (?:geo|subj|register|misc|lang)">\s*)\(([^<>]+?)\)(?=\s*</span>)', re.I)
        line = p.sub(r'\1<span>(</span>\2<span>)</span>', line)
        p = re.compile(r'<h3 class="gramGrp h3_entry">([^<>]+?)\s*</h3>\s*', re.I)
        line = p.sub(r'<span class="bxt">\1</span> ', line)
        p = re.compile(r'<h4 class="gramGrp h3_entry">([^<>]+?)\s*</h4>\s*', re.I)
        line = p.sub(r'<span class="jzb">\1</span> ', line)
        p = re.compile(r'<a class="xr_ref_link"\s*href="">(.+?)</a>', re.I)
        line = p.sub(r'\1', line)
        p = re.compile(r'(<a [^<>]*?href=")([^<>"#]+)([#"][^<>]*>)(.+?)(?=</a>)', re.I)
        line = p.sub(lambda m: self.__replink(m, crefs, key, logs), line)
        p = re.compile(r'(?<=<a class=")xr_ref_link(" href=")(?=[^<>"]+">)', re.I)
        line = p.sub(r'xgv\1entry://', line)
        p = re.compile(r'(?<=<a href=")(?=[^<>"]+">)', re.I)
        line = p.sub(r'entry://', line)
        p = re.compile(r'(?<=<)(span|div|h[1-4]|p|ol|li|em|ul|sup|cite)\s*(?:id="[^<>"]+")?(\sclass=")([^<>"]+?)\s*(?=")', re.I)
        line = p.sub(self.__repcls, line)
        p = re.compile(r'(</?)(?:h1|ul|ol|li)\b', re.I)
        line = p.sub(r'\1div', line)
        line = ''.join(['<link ', lid, 'rel="stylesheet"href="', cfs, '.css"type="text/css"><div class="', cls, '">', line, src, '</div>'])
        p = re.compile(r'\s+(?=>|</?div|</?p)', re.I)
        line = p.sub(r'', line)
        line = '\n'.join([key.replace('&amp;', '&'), line, '</>'])
        return line


def process(dic_dl, args):
    listfile = F_THESLIST if args.diff=='t' else F_WORDLIST
    d_all = makewordlist(args.diff, listfile)
    d_refs = OrderedDict()
    for k, v in d_all.iteritems():
        d_refs[urllib.unquote(v).strip().lower()] = k
    if not path.exists(fullpath(dic_dl.DIC_T)):
        os.mkdir(dic_dl.DIC_T)
    subd = 'thesaurus' if args.diff=='t' else 'dictionary'
    dir = ''.join([dic_dl.DIC_T, path.sep, subd, path.sep])
    if args.diff=='p' or (args.diff=='t' and args.file):
        print "Start to download missing words..."
        dt, wordlist, base, d_app = OrderedDict(), [], 0, OrderedDict()
        for d in os.listdir(fullpath(dir)):
            if path.isdir(fullpath(''.join([dir, d, path.sep]))):
                base += 1
        for i in xrange(1, base+1):
            sdir = ''.join([dir, '%d'%i, path.sep])
            if path.exists(fullpath('appd.txt', base_dir=sdir)):
                dt.update(getwordlist(''.join([sdir, 'appd.txt'])))
        if args.file and path.isfile(fullpath(args.file)):
            for k, v in getwordlist(args.file):
                dt[urllib.unquote(v).strip().lower()] = k
        for k, v in dt.iteritems():
            uk = urllib.unquote(k).strip().lower()
            if not uk in d_refs:
                wordlist.append((v, k))
                d_refs[uk] = v
    else:
        wordlist, base = d_all.items(), 0
    dic_dl.set_redirect(args.diff=='t' and not args.file)
    while wordlist:
        blks, addlist = multiprocess_fetcher(dir, d_refs, wordlist, dic_dl, base)
        base += blks
        wordlist = []
        for k, v in addlist:
            wordlist.append((v, k))
        if addlist:
            print "Downloading additional words..."
            d_refs.update(addlist)
    dump(''.join(['\n'.join(['\t'.join([v, k]) for k, v in d_refs.iteritems()]), '\n']), listfile)
    if is_complete(fullpath(dir)):
        dic_dl.combinefiles(dir)


def merge_d_t(name, dc, th, key):
    th = th.replace('<link rel="stylesheet"href="COT.css"type="text/css">', '')
    p = re.compile(r'<div class="sib">.+?</div></div></div>', re.I)
    dc = p.sub(r'', dc)
    p = re.compile(r'(<link\s[^<>]+>)', re.I)
    dc = p.sub(r'\1<div class="c1a"><div class="fvv"><span class="dzf"onclick="javascript:void(0);">Dictionary</span><span class="t3h"onclick="rvi(this)">Thesaurus</span></div>', dc, 1)
    p = re.compile(r'(?=<script)', re.I)
    if p.search(dc):
        dc = p.sub(''.join(['</div>', th]), dc, 1)
    else:
        src = ''.join(['<script type="text/javascript"src="cl.js"></script><script>if(typeof(uc1)=="undefined"){var _l=document.getElementsByTagName("link");var _r=/',
        name, '.css$/;for(var i=_l.length-1;i>=0;i--)with(_l[i].href){var _m=match(_r);if(_m&&_l[i].id=="kc1"){document.write(\'<script src="\'+replace(_r,"cl.js")+\'"type="text/javascript"><\/script>\');break;}}}</script>'])
        dc = ''.join([dc, th, src, '</div>'])
    return dc


def merge(basedir):
    dir_t = ''.join([basedir, path.sep, 'thesaurus', path.sep])
    file = fullpath('COT.txt', base_dir=dir_t)
    if not path.exists(file):
        print "Cannot find thesaurus file 'COT.txt'."
        return
    words, lns, thes = [], [], OrderedDict()
    for ln in fileinput.input(file):
        ln = ln.strip()
        if ln == '</>':
            thes[lns[0].lower()] = (lns[0], lns[1])
            del lns[:]
        elif ln:
            lns.append(ln)
    fnm = ''.join([basedir, path.extsep, 'txt'])
    dir_t = ''.join([basedir, path.sep, 'dictionary', path.sep])
    file = fullpath(fnm, base_dir=dir_t)
    if not path.exists(file):
        print "Cannot find dictionary file '%s'." % fnm
        return
    fw = open(fullpath(''.join([basedir, path.sep, fnm])), 'w')
    try:
        for ln in fileinput.input(file):
            ln = ln.strip()
            if ln == '</>':
                key, wdef, uk = lns[0], lns[1], lns[0].lower()
                if uk in thes and thes[uk]:
                    if not wdef.startswith('@@@') and not thes[uk][1].startswith('@@@'):
                        wdef = merge_d_t(basedir, wdef, thes[uk][1], lns[0])
                        thes[uk] = None
                fw.write('\n'.join([key, wdef, '</>\n']))
                words.append(key)
                del lns[:]
            elif ln:
                lns.append(ln)
        for k, v in thes.iteritems():
            if v:
                fw.write('\n'.join([v[0], v[1], '</>\n']))
                words.append(v[0])
    finally:
        fw.close()
    print "%s totally" % info(len(words))
    fw = open(fullpath(''.join([basedir, path.sep, 'words.txt'])), 'w')
    fw.write('\n'.join(words))
    fw.close()


if __name__=="__main__":
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("diff", nargs="?", help="[p] To download missing words \n[t] To download thesaurus \n[c] To combine dictionary & thesaurus")
    parser.add_argument("file", nargs="?", help="[file name] To specify additional wordlist")
    print "Start at %s" % datetime.now()
    args = parser.parse_args()
    dic_dl = dic_downloader(args.diff)
    dic_dl.login()
    if dic_dl.session:
        if not args.diff or args.diff == 'p':
            print "Start to make dictionary..."
            process(dic_dl, args)
        elif args.diff == 't':
            print "Start to make thesaurus..."
            process(dic_dl, args)
        elif args.diff == 'c':
            print "Start to combine dictionary & thesaurus..."
            merge(dic_dl.DIC_T)
        else:
            print "USAGE: [p] To download missing words \n[t] To download thesaurus \n[c] To combine dictionary & thesaurus"
        print "Done!"
        dic_dl.logout()
    else:
        print "ERROR: Login failed."
    print "Finished at %s" % datetime.now()
