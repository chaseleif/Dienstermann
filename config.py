###
# Copyright (c) 2021, Chase Phelps
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

from supybot import conf, registry
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Dienste')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified themself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Dienste', True)


Dienste = conf.registerPlugin('Dienste')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(Dienste, 'someConfigVariableName',
#     registry.Boolean(False, _("""Help for someConfigVariableName.""")))
#alrighty then, let's get a file list
import os, re
txtdir = '/'.join(os.path.realpath(__file__).split('/')[:-1])+'/'
### get our api keys
with open(txtdir+'apikeys','r') as infile:
    for line in infile.readlines():
        line=line.strip().split('=')
        conf.registerGlobalValue(Dienste, line[0], registry.String(line[1],
_("""API key.""")))
txtdir+='txts'
filesavail = {}
filenames = os.listdir(txtdir)
for filename in filenames:
    if not os.path.isfile(txtdir+'/'+filename):
        continue
    fsize = os.path.getsize(txtdir+'/'+filename)
    funit='B'
    if fsize>=1073742000:
        funit = 'GiB'
        fsize/=1073742000
    elif fsize>=1048576:
        funit = 'MiB'
        fsize/=1048576
    elif fsize>=1024:
        funit = 'KiB'
        fsize/=1024
    fsize=round(fsize,2)
    filesavail[filename] = str(fsize)+funit
# make the string representation of the dict a space separated list
filesavail = re.sub(',','',re.sub(':','',re.sub('\'','',str(filesavail)[1:-1])))
# the file list with filenames followed by sizes
conf.registerGlobalValue(Dienste, 'txtdir', registry.String(txtdir,
_("""Base directory for txt files.""")))
conf.registerGlobalValue(Dienste, 'filesavail', registry.SpaceSeparatedListOfStrings(filesavail, _("""Available files.""")))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
