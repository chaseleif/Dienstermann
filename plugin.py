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

import os, re
from time import time
from random import randint
#bot
from supybot import utils, plugins, ircutils, callbacks, ircmsgs
import supybot.ircmsgs as ircmsgs
from supybot.commands import *
#weather
import requests, json
#translator
from ibm_watson import LanguageTranslatorV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import ApiException

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Dienste')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class Dienste(callbacks.Plugin):
    """Simple minimal DCC server"""
    threaded = True
    def __init__(self, irc):
        self.__parent = super(Dienste, self)
        self.__parent.__init__(irc)
        #conf.supybot.nick.addCallback(self.getavailfiles)

    def refreshfiles(self, irc, msg, args):
        txtdir = self.registryValue('txtdir')
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
        self.setRegistryValue('filesavail', value=filesavail)
        irc.reply('File list updated.')
        self.getavailfiles(irc=irc,msg=msg,args=args)

    def getavailfiles(self, irc, msg, args):
        filelist = ''.join(self.registryValue('filesavail')).split(' ')
        files = filelist[0]
        for i, val in enumerate(filelist):
            if i>0 and i%2==0:
                files+=', '+val
            elif i>0:
                files+=' ('+val+')'
        irc.reply(str(files))

    def readfile(self, irc, msg, args):
        txtdir = self.registryValue('txtdir')
        fullstr = str(msg).strip()
        theuser = fullstr.split('=')[1].split(' ')[0]
        thefile = fullstr.split(' ')[-1]
        if thefile=='' or ' ' in thefile or '/' in thefile or not os.path.isfile(txtdir+'/'+thefile):
            irc.reply('\"'+thefile+'\" is not a valid filename.')
            return
        with open(txtdir+'/'+thefile,'r') as infile:
            for line in infile.readlines():
                line = line.strip()
                try:
                    m = ircmsgs.IrcMsg(command='PRIVMSG',args=(theuser,line))
                except Exception as e:
                    irc.error(utils.exnToString(e))
                    break
                else:
                    irc.queueMsg(m)
                    irc.noReply()

    def spacestation(self, irc, msg, args):
        response = requests.get('http://api.open-notify.org/iss-now.json')
        if response.status_code==200:
            response = response.json()
        else:
            print('Request returned status code: '+str(response.status_code))
            return
        if 'message' not in response or response['message']!='success':
            irc.reply(str(response))
            irc.reply('Error receiving the location of the ISS')
            return
        pasttime = response['timestamp']
        elapsedtime = time()-pasttime
        hours=0
        minutes=0
        seconds=0
        hours = int(elapsedtime/3600)
        elapsedtime %= 3600
        minutes = int(elapsedtime/60)
        seconds = round(elapsedtime%60,3)
        timestr = ''
        if hours>0:
            timestr+=str(hours)+' hour'
            if hours!=1:
                timestr+='s'
            timestr+=', '
        if minutes>0:
            timestr+=str(minutes)+' minute'
            if minutes!=1:
                timestr+='s'
            timestr+=', '
        timestr+=str(seconds)+' seconds'
        longitude = response['iss_position']['longitude']
        latitude = response['iss_position']['latitude']
        vstr = 'S' if float(longitude)<0 else 'N'
        hstr = 'W' if float(latitude)<0 else 'E'
        coordstring = str(abs(int(float(longitude))))+u'\N{DEGREE SIGN}'+vstr
        coordstring+=', '+str(abs(int(float(latitude))))+u'\N{DEGREE SIGN}'+hstr
        irc.reply(timestr+' ago the international space station was at:')
        irc.reply('('+str(longitude)+', '+str(latitude)+'), or ('+coordstring+')')
        urlstring = 'https://geocodeapi.p.rapidapi.com/GetNearestCities'
        querystring = {'range':'0','longitude':longitude,'latitude':latitude}
        headers = {
            'x-rapidapi-key': self.registryValue('rapidapikey'),
            'x-rapidapi-host': "geocodeapi.p.rapidapi.com"
        }
        response = requests.request('GET',urlstring,headers=headers,params=querystring)
        if response.status_code==200:
            response = response.json()
        else:
            print('Distance api returned status code: '+str(response.status_code))
            return
        if len(response)>0 and 'City' in response[0]:
            for i in range(2):
                neareststring = 'The '
                if i==1:
                    neareststring+='second '
                neareststring+='nearest city is '
                neareststring+=response[i]['City']+', '
                neareststring+=response[i]['Country']+' which is '
                if response[i]['Distance'] > 999.9:
                    neareststring+=str(round(float(response[i]['Distance'])/1000,3))+'km'
                else:
                    neareststring+=str(int(float(response[i]['Distance'])))+'m'
                neareststring+=' away'
                irc.reply(neareststring)

    def weather(self, irc, msg, args):
        url = 'https://weatherapi-com.p.rapidapi.com/current.json'
        headers = {
            'x-rapidapi-key': self.registryValue('rapidapikey'),
            'x-rapidapi-host': "weatherapi-com.p.rapidapi.com"
        }
        querystring = {'q':'78666'}
        response = requests.request('GET', url, headers=headers, params=querystring)
        if response.status_code==200:
            response = response.json()
        else:
            print('Request returned status code: '+str(response.status_code))
            return
        if 'current' in response:
            loc = response['location']
            cur = response['current']
            irc.reply('It is '+cur['condition']['text']+' in '+loc['name']+' at '+loc['localtime'])
            irc.reply('The temperature is '+str(cur['temp_f'])+u'\N{DEGREE SIGN}'+'F, with a feels like temperatore of '+str(cur['feelslike_f'])+u'\N{DEGREE SIGN}'+'F')
            irc.reply('The windspeed is '+str(cur['wind_mph'])+'-'+str(cur['gust_mph'])+'mph, with '+str(cur['cloud'])+'% cloud cover and '+str(cur['humidity'])+'% humidity')
        else:
            irc.reply(str(response))

    def numbertrivia(self, irc, msg, args):
        number=0
        if type(args) is not list or len(args)==0:
            number=randint(-100,100)
        else:
            try:
                number = int(args[-1])
            except:
                number=randint(-100,100)
        response = requests.request('GET','http://numbersapi.com/'+str(number))
        if response.status_code==200:
            irc.reply(response.text)
        else:
            irc.reply('Received bad response: '+str(response.status_code))

    def randomquote(self, irc, msg, args):
        url = "https://quotes15.p.rapidapi.com/quotes/random/"
        headers = {
            'x-rapidapi-key': self.registryValue('rapidapikey'),
            'x-rapidapi-host': "quotes15.p.rapidapi.com"
        }
        response = requests.request("GET", url, headers=headers)
        if response.status_code==200:
            response = response.json()
        else:
            print('Request returned status code: '+str(response.status_code))
            return
        if 'content' in response:
            thequotestr = '\"'+response['content']+'\"'
            thequotestr = re.sub('\r','',thequotestr)
            thequotestr = re.sub('\n',' ',thequotestr)
            thequotestr+=' - '+response['originator']['name']
            irc.reply(thequotestr)

    def numbermath(self, irc, msg, args):
        number=0
        if type(args) is not list or len(args)==0:
            number=randint(-100,100)
        else:
            try:
                number = int(args[-1])
            except:
                number=randint(-100,100)
        response = requests.request('GET','http://numbersapi.com/'+str(number)+'/math')
        if response.status_code==200:
            irc.reply(response.text)
        else:
            irc.reply('Received bad response: '+str(response.status_code))

    def translate(self, irc, msg, args):
        if type(args) is not list or len(args)==0:
            irc.reply('You must provide something to translate.')
            return
        try:
            high=[0.0,0.0]
            lang = ['','']
            targetlang=''
            if args[0][0]=='!':
                args[0]=args[0][1:].split('-')
                if len(args[0])==2:
                    lang[0]=args[0][0]+'-'+args[0][1]
                    high=[1,0]
                else:
                    targetlang=args[0][0]
                args = args[1:]
                if len(args)==0:
                    irc.reply('You must provide something to translate.')
                    return
            authenticator = IAMAuthenticator(self.registryValue('ibmapikey'))
            language_translator = LanguageTranslatorV3(
                version='2018-05-01',
                authenticator=authenticator
            )
            language_translator.set_service_url('https://api.us-south.language-translator.watson.cloud.ibm.com')
            intext = ' '.join(args)
            if lang[0]=='':
                language = language_translator.identify(intext).get_result()
                for i in range(len(language['languages'])):
                    if language['languages'][i]['confidence']>high[0]:
                        high[1] = high[0]
                        lang[1] = lang[0]
                        high[0] = language['languages'][i]['confidence']
                        lang[0] = language['languages'][i]['language']
                    elif language['languages'][i]['confidence']>high[1]:
                        high[1] = language['languages'][i]['confidence']
                        lang[1] = language['languages'][i]['language']
            for i in range(2):
                if lang[i]=='':
                    continue
                high[i]*=100
                if high[i]<10:
                    continue
                dolang=''
                if targetlang!='':
                    dolang=lang[i]+'-'+targetlang
                elif lang[0]=='en':
                    dolang='en-de'
                elif '-' in lang[i]:
                    dolang=lang[i]
                else:
                    dolang=lang[i]+'-en'
                translation = language_translator.translate(
                    text=intext,
                    model_id=dolang).get_result()
                if '-' in lang[i]: # explicit translation
                    irc.reply('('+lang[i]+'): '+translation['translations'][0]['translation'])
                elif lang[i]!='en':
                    irc.reply('('+lang[i]+' '+str(round(high[i],2))+'%): '+translation['translations'][0]['translation'])
                elif targetlang!='':
                    irc.reply('('+dolang+'): '+translation['translations'][0]['translation'])
                else:
                    irc.reply('Auf Deutsch: ' + translation['translations'][0]['translation'])
        except ApiException as ex:
            irc.reply('Translation error '+str(ex.code)+': '+ex.message)
        except Exception as e:
            irc.reply('Translation error: '+str(e))


Class = Dienste


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
