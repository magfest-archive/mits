import shutil
from cherrypy.lib.static import serve_file

from uber.common import *

from mits._version import __version__
from mits.config import *
from mits.models import *
import mits.model_checks
import mits.automated_emails

static_overrides(join(config['module_root'], 'static'))
template_overrides(join(config['module_root'], 'templates'))
mount_site_sections(config['module_root'])
