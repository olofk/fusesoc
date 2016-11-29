class Vlnv(object):
    def __init__(self, s, default_relation = ">="):
        def _is_rev(s):
            return s.startswith('r') and s[1:].isdigit()
        def _is_version(s):
            return s[0].isdigit()

        if s.startswith('!'):
            self.conflict = True
            _s = s[1:]
        else:
            self.conflict = False
            _s = s[:]
        if _s[0:2] in ['>=', '<=']:
            self.relation = _s[0:2]
            _s = _s[2:]
        elif s[0] in ['>', '<']:
            self.relation = s[0]
            _s = _s[1:]
        elif s[0] in ['=']:
            self.relation = "=="
            _s = _s[1:]
        else:
            self.relation = ""

        vlnv_parts = _s.split(':')

        self.revision = 0
        #legacy naming. Only name
        if len(vlnv_parts) == 1:
            self.vendor  = ""
            self.library = ""
            sl = vlnv_parts[0].rsplit('-')
            if len(sl) == 1:
                #Simplest case. No '-' => Only name
                self.name = s
                self.version = ""
            else:
                #If last part is the revision, save and pop from list
                if _is_rev(sl[-1]):
                    self.revision = int(sl.pop()[1:])

                #If last part is version, save and pop from list
                if len(sl) > 1 and _is_version(sl[-1]):
                    self.version = sl.pop()
                else:
                    self.version = ""

                self.name    = '-'.join(sl)

        #No version tag
        elif len(vlnv_parts) == 3:
            self.vendor  = vlnv_parts[0]
            self.library = vlnv_parts[1]
            self.name    = vlnv_parts[2]
            self.version = ""
        #Full vlnv
        elif len(vlnv_parts) == 4:
            self.vendor  = vlnv_parts[0]
            self.library = vlnv_parts[1]
            self.name    = vlnv_parts[2]
            self.version = vlnv_parts[3]
        else:
            raise SyntaxError("Illegal core name '{}'".format(s)) 

        if self.version or (self.revision > 0):
            if not self.relation:
                # Version specified without relational operator
                # Assume user wants the exact version
                self.relation = "=="
            if not self.version:
                self.version = "0"
        else:
            if self.relation:
                _s = "{}: '{}' operator requires a version "
                raise SyntaxError(_s.format(s, self.relation))
            #No version specifier means any version i.e. >=0
            self.version = "0"
            self.relation = default_relation

        #Create sanitized name
        self.sanitized_name = str(self).lstrip(':').replace(":", "_")

    def __str__(self):
        if self.relation == '=':
            relation = ""
        else:
            relation = self.relation
        if self.revision > 0:
            revision = "-r"+str(self.revision)
        else:
            revision = ""
#        return "{}{}:{}:{}:{}{}".format(relation,
        return "{}{}:{}:{}:{}{}".format("",
                                        self.vendor,
                                        self.library,
                                        self.name,
                                        self.version,
                                        revision)
    def depstr(self):
        if self.relation == '==':
            relation = ""
        else:
            relation = self.relation
        return relation+str(self)
