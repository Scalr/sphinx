# -*- coding: utf-8 -*-
"""
    sphinx.writers.html
    ~~~~~~~~~~~~~~~~~~~

    docutils writers handling Sphinx' custom nodes.

    :copyright: Copyright 2014 by the Scalr team http://www.scalr.com/.
    :license: BSD, see LICENSE for details.
"""
from docutils import nodes
from docutils.writers.html4css1 import HTMLTranslator as BaseTranslator

from sphinx.util.pycompat import htmlescape
from sphinx.highlighting import PygmentsBridge
from sphinx.writers.html import HTMLTranslator
from sphinx.locale import _


class ConfluencePygmentsBridge(PygmentsBridge):
    
    def __init__(self, *args, **kwds):
	self.dest = 'html'

    def highlight_block(self, source, lang, warn=None, force=False, **kwargs):
        if not isinstance(source, unicode):
            source = source.decode()
	return self.unhighlighted(source)

    def unhighlighted(self, source):
	before = '<ac:structured-macro ac:name="code"><ac:plain-text-body><![CDATA['
	after = ']]></ac:plain-text-body></ac:structured-macro>'
        return before + source + after + '\n'
        #return u'%s%s%s\n' % (before, htmlescape(source), after)

class ConfluenceTranslator(HTMLTranslator):

    def __init__(self, builder, *args, **kwds):
        HTMLTranslator.__init__(self, builder, *args, **kwds)
	self.highlighter = ConfluencePygmentsBridge()

    #highlight warnings
    def visit_warning(self, node):
        before = '<ac:structured-macro ac:name="warning">'
        before += '<ac:parameter ac:name="icon">true</ac:parameter>'
        before += '<ac:rich-text-body>'
        after = '</ac:rich-text-body></ac:structured-macro>'
        self.body.append(before + node.rawsource + after)
	raise nodes.SkipNode

    def depart_warning(self, node):
        pass

    #<dt> -> <h2/h3/h4>
    def visit_desc_signature(self, node):
        # the id is set automatically
	if node.parent['objtype'] == 'class':
	    #XXX: generating clean <H2>-headings for classes in Table of contents
            self.body.append("<h2>%s</h2>\n" % node["ids"][0].split(".")[-1])
	    self.body.append(self.starttag(node, 'h4'))
	elif node.parent['objtype'] == 'method':
	    #XXX: generating clean <H3>-headings for methods in Table of contents
	    self.body.append("<h3>%s</h3>\n" % node["ids"][0].split(".")[-1])
	    self.body.append(self.starttag(node, 'h4'))
        # anchor for per-desc interactive data
        elif node.parent['objtype'] != 'describe' \
               and node['ids'] and node['first']:
            self.body.append('<!--[%s]-->' % node['ids'][0])

    def depart_desc_signature(self, node):
        if node['ids'] and self.permalink_text and self.builder.add_permalinks:
	    # replacing anchors with confluence macro
	    aname = node['ids'][0]
	    before = '<ac:structured-macro ac:name="anchor">'
            before += '<ac:parameter ac:name="">' 
            after = '</ac:parameter></ac:structured-macro>' 
            self.body.append(before + aname + after)

	if node.parent['objtype'] == 'class':
	    self.body.append('</h4>\n')
        elif node.parent['objtype'] == 'method':
	    self.body.append('</h4>\n')

    def depart_title(self, node):
        close_tag = self.context[-1]
        if (self.permalink_text and self.builder.add_permalinks and
            node.parent.hasattr('ids') and node.parent['ids']):
            aname = node.parent['ids'][0]
            # add permalink anchor
	    # replacing anchors with confluence macro
            before = '<ac:structured-macro ac:name="anchor">'
            before += '<ac:parameter ac:name="">'
            after = '</ac:parameter></ac:structured-macro>'
            self.body.append(before + aname + after)

        BaseTranslator.depart_title(self, node)
    
    #<tt> -> <span>
    def visit_desc_name(self, node):
        self.body.append(self.starttag(node, 'span', '', CLASS='descname'))

    def depart_desc_name(self, node):
        self.body.append('</span>')
	#self.body.append('</h3>')

    def visit_desc_addname(self, node):
        self.body.append(self.starttag(node, 'span', '', CLASS='descclassname'))

    def depart_desc_addname(self, node):
        self.body.append('</span>')

    def visit_literal(self, node):
        self.body.append(self.starttag(node, 'span', '', CLASS='docutils literal'))
        self.protect_literal_text += 1

    def depart_literal(self, node):
        self.protect_literal_text -= 1
        self.body.append('</span>')

    def visit_literal_block(self, node):
        if node.rawsource != node.astext():
            # most probably a parsed-literal block -- don't highlight
            return BaseTranslator.visit_literal_block(self, node)
        lang = self.highlightlang
        linenos = node.rawsource.count('\n') >= \
                  self.highlightlinenothreshold - 1
        highlight_args = node.get('highlight_args', {})
        if 'language' in node:
            # code-block directives
            lang = node['language']
            highlight_args['force'] = True
        if 'linenos' in node:
            linenos = node['linenos']
        def warner(msg):
            self.builder.warn(msg, (self.builder.current_docname, node.line))
        highlighted = self.highlighter.highlight_block(
            node.rawsource, lang, warn=warner, linenos=linenos,
            **highlight_args)
        starttag = self.starttag(node, 'div', suffix='',
                                 CLASS='highlight-%s' % lang)
        if 'filename' in node:
            starttag += '<div class="code-block-filename"><span>%s</span></div>' % (
                node['filename'],)
        self.body.append(starttag + highlighted + '</div>\n')
        raise nodes.SkipNode

    #<dd> -> <div>
    def visit_desc_content(self, node):
        self.body.append(self.starttag(node, 'div', ''))

    def depart_desc_content(self, node):
        self.body.append('</div>')

    #removing <dl> tags 
    def visit_desc(self, node):
	pass

    def depart_desc(self, node):
	pass

    #Prevent writing <div class="section"> tags
    def visit_section(self, node):
        self.section_level += 1

    def depart_section(self, node):
        self.section_level -= 1
