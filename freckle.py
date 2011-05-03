from cStringIO import StringIO
import datetime
import urllib

import httplib2
import iso8601
import yaml
# Ugh, this is sad...
# http://lxml.de/tutorial.html
try:
    from lxml import etree
except ImportError:
    try:
        # Python 2.5
        import xml.etree.cElementTree as etree
    except ImportError:
        try:
            # Python 2.5
            import xml.etree.ElementTree as etree
        except ImportError:
            try:
                # normal cElementTree install
                import cElementTree as etree
            except ImportError:
                try:
                # normal ElementTree install
                    import elementtree.ElementTree as etree
                except ImportError:
                    print("Failed to import ElementTree from any known place")



class Freckle(object):

    def __init__(self, account, token):
        self.endpoint = "https://%s.letsfreckle.com/api" % account
        self.headers = {"X-FreckleToken":token}
        self.http = httplib2.Http()

    def request(self, url, method="GET", body=""):
        resp, content = self.http.request(url, method, body, 
                                          headers=self.headers)
        return self.parse_response(content)

    def get_entries(self, **kwargs):
        """
        Optional search arguments:

           * people: a list of user ids
           * projects: a list of project ids
           * tags: a list of tag ids and/or names
           * date_to: a `datetime.date` object
           * date_from: a `datetime.date` object
           * billable: a boolean
        """
        search_args = {}
        for search in ('people', 'projects', 'tags'):
            if search in kwargs:
                as_string = ",".join([str(i) for i in kwargs[search]])
                search_args['search[%s]' % search] = as_string
        for search in ('date_to', 'date_from'):
            if search in kwargs:
                # strip "date_"
                search_args['search[%s]' % search[5:]] = kwargs[search].strftime("%Y-%m-%d")
        if "billable" in kwargs:
            if kwargs['billable']:
                val = "true"
            else:
                val = "false"
            search_args['search[billable]'] = val
        query = urllib.urlencode(search_args)
        return self.request("%s/entries.xml?%s" % self.endpoint, self.query)

    def get_users(self):
        return self.request("%s/users.xml" % self.endpoint)

    def get_projects(self):
        return self.request("%s/projects.xml" % self.endpoint)
    
    def parse_response(self, xml_content):
        """Parse XML response into Python"""
        content = []
        tree = etree.parse(StringIO(xml_content))
        for elem in tree.getroot().getchildren():
            as_dict = {}
            for item in elem.getchildren():
                if item.get("type") and item.text:
                    parser = "%s_as_python" % item.get("type")
                    as_python = getattr(self, parser)(item.text)
                elif item.get("type"):
                    as_python = None
                else:
                    as_python = item.text
                as_dict[item.tag] = as_python
            content.append(as_dict)
        return content

    def boolean_as_python(self, val):
        if val == 'true':
            return True
        else:
            return False
        
    def date_as_python(self, val):
        return datetime.date(*[int(x) for x in val.split("-")])

    def datetime_as_python(self, val):
        return iso8601.parse_date(val)

    def integer_as_python(self, val):
        return int(val)

    def array_as_python(self, val):
        return val.split(",")

    def yaml_as_python(self, val):
        return yaml.load(val)
