"""Python client for Freckle"""
from cStringIO import StringIO
import datetime
import urllib

import httplib2
import iso8601
import yaml
# Ugh, this is sad...
ETREE_MODULES = [
    'lxml.etree',
    'xml.etree.cElementTree',
    'cElementTree',
    'xml.etree.ElementTree',
    'elementtree.ElementTree',
]
etree = None
for name in ETREE_MODULES:
    try:
        etree = __import__(name, '', '', [''])
        break
    except ImportError:
        continue
if etree is None:
    raise ImportError("Failed to import ElementTree from any known place")



class Freckle(object):
    """Class for interacting with the Freckle API"""

    def __init__(self, account, token):
        self.endpoint = "https://%s.letsfreckle.com/api" % account
        self.headers = {"X-FreckleToken":token}
        self.http = httplib2.Http()

    def request(self, url, method="GET", body=""):
        """Make a request to Freckle and return Python objects"""
        resp, content = self.http.request(url, method, body, 
                                          headers=self.headers)
        return self.parse_response(content)

    def get_entries(self, **kwargs):
        """
        Get time entries from Freckle

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
                date = kwargs[search].strftime("%Y-%m-%d")
                # strip "date_"
                freckle_keyword = 'search[%s]' % search[5:]
                search_args[freckle_keyword] = date
        if "billable" in kwargs:
            if kwargs['billable']:
                val = "true"
            else:
                val = "false"
            search_args['search[billable]'] = val
        query = urllib.urlencode(search_args)

        page = 1
        response = []
        while (page == 1) or paged_response:
            paged_response = self.request("%s/entries.xml?per_page=1000&page=%d&%s" % (self.endpoint, page, query))
            response.extend(paged_response)
            page += 1

        return response

    def get_users(self):
        """Get users from Freckle"""
        return self.request("%s/users.xml" % self.endpoint)

    def get_projects(self):
        """Get projects from Freckle"""
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
        """Convert text to boolean"""
        if val == 'true':
            return True
        else:
            return False
        
    def date_as_python(self, val):
        """Convert text to date"""
        return datetime.date(*[int(x) for x in val.split("-")])

    def datetime_as_python(self, val):
        """Convert text to datetime"""
        return iso8601.parse_date(val)

    def integer_as_python(self, val):
        """Convert text to integer"""
        return int(val)

    def array_as_python(self, val):
        """Convert text to list"""
        return val.split(",")

    def yaml_as_python(self, val):
        """Convert YAML to dict"""
        return yaml.load(val)
