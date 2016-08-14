from PIL import Image
from io import StringIO
from datetime import datetime
import os


class DocsMaker(object):
    """A documentation site maker."""
    def __init__(self, section):
        self.section = section
        self.output_dir = '%s/livingdocs/content/%s' % (os.getcwd(), self.section)

    def fix_filename(self, s):
        parts = s.split('/')
        filename = parts[1]
        keyname = filename.split('.')[0]
        return 'feature/%s' % keyname

    def start_feature(self, context, feature):
        # beginning a feature. we should begine a file for this
        tags = [t.encode('ascii') for t in feature.tags]
        self.doc = HugoDoc(title=feature.name, tags=tags)

        # record the file path for later writing
        self.doc.path = self.fix_filename(feature.filename)

        # create the directory we will need later
        os.makedirs('%s/%s' % (self.output_dir, self.doc.path))

        self.doc.writeline(feature.description)
        self.doc.writeline(u'<!--more-->')

    def end_feature(self, context, feature):
        # calculate the number of scenarios
        self.doc.meta['num_scenarios'] = len(feature.scenarios)
        self.doc.meta['num_scenarios_passing'] = len([s for s in feature.scenarios if s.status == 'passed'])

        # write an index.md file for all the info we've accumulated about
        # this feature
        f = open('%s/%s/index.mmark' % (self.output_dir, self.doc.path), 'w')
        f.write(self.doc.getcontents())
        f.close()

    def start_scenario(self, context, scenario):
        # scenario header
        self.doc.writeline(u'\n### %s' % scenario.name)
        self.doc.writeline()

        # begin table header for the steps
        self.doc.writeline(u'{.table .table-hover}')
        self.doc.writeline(u' Step | Status | Time |   ')
        self.doc.writeline(u'------|--------|------|---')

    def end_scenario(self, context, scenario):
        pass

    def start_step(self, context, step):
        pass

    def end_step(self, context, step):
        slug = slugger(step.name)
        shot_name = '%s.png' % slug
        thumb_name = '%s_tm.png' % slug

        # get the screenshot
        try:
            context.browser.driver.get_screenshot_as_file('%s/%s/%s' % (self.output_dir, self.doc.path, shot_name))
        except:
            shot_name = None
            image_code = 'error capturing'

        # make a thumbnail of it
        if shot_name:
            im = Image.open('%s/%s/%s' % (self.output_dir, self.doc.path, shot_name))
            im.thumbnail((100, 100))
            im.save('%s/%s/%s' % (self.output_dir, self.doc.path, thumb_name))

            image_code = '<a href="%s"><img class="img-thumbnail" src="%s" width="100" /></a>' % (shot_name, thumb_name)

        # write the step information to file
        self.doc.writeline(u'%s %s | %s | %0.2f | %s' % (step.keyword, step.name, step.status, step.duration, image_code))


class HugoDoc(object):
    """
    A utility for creating hugo/markdown docs.
    How it should work:
        >>> doc = HugoDoc(title='Page One')
        >>> print doc.header()
        +++
        title = "Page One"
        tags = []
        date = "2016-08-14T09:45:27.006975"
        +++
        >>> doc.writeline(u'A description goes here')
        >>> print doc.getcontents()
        +++
        title = "Page One"
        +++
        <BLANKLINE>
        A description goes here
        <BLANKLINE>
        >>> doc.meta['number'] = 5
        >>> print doc.header()
        +++
        title = "Page One"
        +++
    """
    def __init__(self, title='', tags=[]):
        self.title = title
        self.meta = {}
        self.buff = StringIO()
        self.meta['tags'] = tags

    def header(self):
        lines = ['title = "%s"' % self.title]
        for key, val in self.meta.items():
            if isinstance(val, list):
                lines.append('%s = %s' % (key, val))
            else:
                lines.append('%s = "%s"' % (key, val))
        # auto date
        self.date = str(datetime.now().isoformat())
        lines.append('date = "%s"' % self.date)
        lines.insert(0, '+++')
        lines.append('+++')
        return '\n'.join(lines)

    def writeline(self, s=u''):
        self.buff.writelines(s)
        self.buff.writelines(u'\n')

    def getcontents(self):
        return self.header() + '\n\n' + self.buff.getvalue()