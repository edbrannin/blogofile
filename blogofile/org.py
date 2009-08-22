#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
org.py convert org source file into html file 
"""

__author__ = "Jaemok Jeong(jmjeong@gmail.com)"
__date__   = "Tue Aug 11 12:50:17 2009"


import os
import tempfile
import logging
import re
import sys
import commands
from BeautifulSoup import BeautifulSoup

import post
import config

logger = logging.getLogger("blogofile.org")

class EmacsNotFoundException(Exception):
    pass

import util

class org:
    """
    Convert org file into html
    """
    def __init__(self, source):
        self.source    = source
        return self.__convert()
        
    def __convert(self):
        """
        Class to Convert org file into html file

        It composes org-content with source, preamble, and postample.
        Launches emacs and convert the org-content into html file.

        Generated html file is processed with BeautifulSoup module to
        extract body section and title and categories.

        self.content  = body
        self.title    = title (which is first '*' in org-file)
        self.category = categories (which is tags in first '*' in org-file)
        self.date     = date (which is scheduled file?)

    >>> src = '''
    ... ---
    ... * Title                                 :emacs:blog:
    ... some text
    ... ** First section
    ... some more text
    ... ** Second section
    ... 
    ... This is *bold* /italics/ _underline_ [[http://emacs.org][Emacs]]
    ...
    ... | name   | qty |
    ... | apple  | 5   |
    ... | banana | 10  |
    ... '''
    >>> config.emacs_binary = '/usr/bin/emacs'
    >>> p = org(src)
    >>> p.title
    u'Title'
    >>> p.categories == set([post.Category('emacs'),post.Category('blog')])
    True
    # >>> p.date
    # datetime.datetime(2008, 10, 20, 0, 0)
    # >>> p.permalink
    # u'/2008/10/20/first-post'
        """
        tempFile = tempfile.NamedTemporaryFile(suffix='.org')
        try:
            tempFile.write(config.emacs_orgmode_preamble)
            tempFile.write("\n")
        except AttributeError:
            pass
        tempFile.write(self.source)
        tempFile.flush()

        pname = ""

        try:
            pname = config.emacs_binary
        except AttributeError:
            raise EmacsNotFoundException, "Emacs binary is not defined"

        pname += " --batch"
        try:
            if config.emacs_preload_elisp:
                pname += " --load=%s" % config.emacs_preload_elisp
        except AttributeError:
            pass

        pname += " --visit=%s --funcall org-export-as-html-batch"
        pname = pname % tempFile.name
        logger.debug("Exec name::: %s" % pname)

        status, output = commands.getstatusoutput(pname)
        logger.debug("Convert output:::\n\t%s"%output)
        if status:
            raise EmacsNotFoundException, "orgfile filter failed"
        
        html = tempFile.name[:-4] + '.html'
        tempFile.close()

        content = open(html, 'r').read()

        # remote the temporary file
        os.remove(html)
            
        soup = BeautifulSoup(content.decode('utf-8'))
        self.title = re.sub('&nbsp;', '', soup.h2.contents[0]).strip()

        try:
            if soup.h2.span != None:
                if soup.h2.span.findAll(text=True):
                    self.categories = set(post.Category(''.join(soup.h2.span.findAll(text=True)).split('&nbsp;')))
                else:
                    self.categories = None
            else:
                self.categories = None
        
        except AttributeError:
            pass

        soup.body.div.h2.extract()  # delete h2 section (title and category)
        
        self.content = str(soup.body.div)
        
if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=True)
    
