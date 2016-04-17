"""
The MIT License (MIT)

Copyright (c) 2015 Olof Kindgren <olof.kindgren@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import yaml
import xml.etree.ElementTree as ET
from fusesoc.ipyxact import ipxact_yaml

class IpxactInt(int):
    def __new__(cls, *args, **kwargs):
        if not args:
            return super(IpxactInt, cls).__new__(cls)
        elif len(args[0]) > 2 and args[0][0:2] == '0x':
            return super(IpxactInt, cls).__new__(cls, args[0][2:], 16)
        elif "'" in args[0]:
            sep = args[0].find("'")
            if args[0][sep+1] == "h":
                base = 16
            else:
                raise Exception
            return super(IpxactInt, cls).__new__(cls, args[0][sep+2:], base)
        else:
            return super(IpxactInt, cls).__new__(cls, args[0])

class IpxactBool(str):
    def __new__(cls, *args, **kwargs):
        if not args:
            return None
        elif args[0] in ['true', 'false']:
            return super(IpxactBool, cls).__new__(cls, args[0])
        else:
            raise Exception

class IpxactItem(object):
    nsmap = {'1.4'  : ('spirit' , 'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4'),
             '1.5'  : ('spirit' , 'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5'),
             '2009' : ('spirit' , 'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009'),
             '2014' : ('ipxact' , 'http://www.accellera.org/XMLSchema/IPXACT/1685-2014'),
    }
    nsversion = '1.5'

    ATTRIBS = {}
    MEMBERS = {}
    CHILDREN = []
    CHILD = []
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if k in self.MEMBERS:
                setattr(self, k, v)
            elif k in self.ATTRIBS:
                setattr(self, k, v)
            else:
                s = "{} has no member or attribute '{}'"
                raise AttributeError(s.format(self.__class__.__name__, k))

    def load(self, f):
        tree = ET.parse(f)
        root = tree.getroot()

        #Warning: Semi-horrible hack to find out which IP-Xact version that is used
        for key, value in self.nsmap.items():
            if root.tag[1:].startswith(value[1]):
                self.nsversion = key

        S = '{%s}' % self.nsmap[self.nsversion][1]
        if not (root.tag == S+self._tag):
            raise Exception

        self.parse_tree(root, self.nsmap[self.nsversion])

    def parse_tree(self, root, ns):
        if self.ATTRIBS:
            for _name, _type in self.ATTRIBS.items():
                _tagname = '{' + ns[1] + '}' + _name
                if _tagname in root.attrib:
                    setattr(self, _name, eval(_type)(root.attrib[_tagname]))
        for _name, _type in self.MEMBERS.items():
            tmp = root.find('./{}:{}'.format(ns[0], _name), {ns[0] : ns[1]})
            if tmp is not None and tmp.text is not None:
                setattr(self, _name, eval(_type)(tmp.text))
            else:
                setattr(self, _name, eval(_type)())

        for c in self.CHILDREN:
            for f in root.findall(".//{}:{}".format(ns[0], c), {ns[0] : ns[1]}):
                child = getattr(self, c)[:]
                class_name = c[0].upper() + c[1:]
                #t = __import__(self.__module__)
                #t = getattr(t, 'ipyxact')
                #t = getattr(t, class_name)()
                t = eval(class_name)()
                t.parse_tree(f, ns)
                child.append(t)
                setattr(self, c, child)
        for c in self.CHILD:
            f = root.find(".//{}:{}".format(ns[0], c), {ns[0] : ns[1]})
            if f is not None:
                child = getattr(self, c)
                class_name = c[0].upper() + c[1:]
                t = eval(class_name)()
                t.parse_tree(f, ns)
                setattr(self, c, t)

    def _write(self, root, S):
        for a in self.ATTRIBS:
            root.attrib[S+a] = getattr(self, a)

        for m in self.MEMBERS:
            tmp = getattr(self, m)
            if tmp is not None:
                ET.SubElement(root, S+m).text = str(tmp)

        for c in self.CHILDREN:
            for child_obj in getattr(self, c):
                subel = ET.SubElement(root, S+c)
                child_obj._write(subel, S)
        for c in self.CHILD:
            tmp = getattr(self, c)
            if tmp is not None:
                subel = ET.SubElement(root, S+c)
                tmp._write(subel, S)

    def write(self, f):
        ET.register_namespace(self.nsmap[self.nsversion][0], self.nsmap[self.nsversion][1])
        S = '{%s}' % self.nsmap[self.nsversion][1]
        root = ET.Element(S+self._tag)
        self._write(root, S)

        et = ET.ElementTree(root)
        et.write(f, xml_declaration=True, encoding='unicode')

def _generate_classes(j):
    for tag, _items in j.items():
        if 'ATTRIBS' in _items:
            for key, value in _items['ATTRIBS'].items():
                _items.update({key : eval(value)})
        if 'MEMBERS' in _items:
            for key, value in _items['MEMBERS'].items():
                _items.update({key : eval(value)})
        if 'CHILDREN' in _items:
            for key in _items['CHILDREN']:
                _items.update({key : []})
        if 'CHILD' in _items:
            for key in _items['CHILD']:
                _items.update({key : None})
        _items.update({'_tag' : tag})

        generatedClass = type(tag[0].upper()+tag[1:], (IpxactItem,), _items)
        globals()[generatedClass.__name__] = generatedClass

_generate_classes(yaml.load(ipxact_yaml.description))
