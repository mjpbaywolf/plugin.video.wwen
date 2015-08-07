__author__ = 'bay_wolf'

import urllib
import urllib2
import re
import time
import cookielib
import os
from xml.dom.minidom import parse
import xml.dom.minidom


IGNORE_DISCARD = True
USERAGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.13) Gecko/20080311 Firefox/2.0.0.13'
SOAPCODES = {
    "1"    : "OK",
    "-1000": "Requested Media Not Found",
    "-1500": "Other Undocumented Error",
    "-2000": "Authentication Error",
    "-2500": "Blackout Error",
    "-3000": "Identity Error",
    "-3500": "Sign-on Restriction Error",
    "-4000": "System Error",
}


class WWESession:

    def __init__(self, user, passwd, cookiefile):
        self.user = user
        if self.user is None:
            self.user = ""
        self.passwd = passwd
        self.cookiefile = cookiefile
        self.auth = True
        self.logged_in = None
        self.cookie_jar = None
        self.cookies = {}
        self.session_key = None

    def extractCookies(self):
        for c in self.cookie_jar:
            self.cookies[c.name] = c.value

    def readCookieFile(self):
        self.cookie_jar = cookielib.LWPCookieJar(self.cookiefile)
        if self.cookie_jar is not None:
            if os.path.isfile(self.cookiefile) is False:
                self.cookie_jar.save()
            self.cookie_jar.load(self.cookiefile, ignore_discard=IGNORE_DISCARD)
            self.extractCookies()
        else:
            raise ValueError("Couldn't open cookie jar")

    def login(self):

        self.readCookieFile()

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie_jar))
        urllib2.install_opener(opener)

        login_url = 'https://secure.net.wwe.com/enterworkflow.do?flowId=account.login'
        txheaders = {'User-agent': USERAGENT,
                     'Referer': 'http://network.wwe.com/'}
        data = None
        req = urllib2.Request(login_url, data, txheaders)

        if self.user == "":
            return

        try:
            handle = urllib2.urlopen(req)
        except:
            raise ValueError('Error occurred in HTTP request to login page')
        try:
            self.extractCookies()
        except Exception, detail:
            raise ValueError(detail)

        self.cookie_jar.save(self.cookiefile, ignore_discard=IGNORE_DISCARD)

        rdata = handle.read()

        # now authenticate
        txheaders['Referer'] = 'https://secure.net.wwe.com/enterworkflow.do?flowId=account.login'

        auth_values = {'registrationAction': 'identify',
                       'emailAddress': self.user,
                       'password': self.passwd,
                       'submitButton': ''}

        success_pat = re.compile(r'Account Management')
        auth_data = urllib.urlencode(auth_values)
        auth_url = 'https://secure.net.wwe.com/authenticate.do'
        req = urllib2.Request(auth_url, auth_data, txheaders)
        try:
            handle = urllib2.urlopen(req)
            self.cookie_jar.save(self.cookiefile, ignore_discard=IGNORE_DISCARD)
            self.extractCookies()
        except:
            raise ValueError('Error occurred in HTTP request to auth page')

        auth_page = handle.read()

        self.cookie_jar.save(self.cookiefile, ignore_discard=IGNORE_DISCARD)

        try:
            loggedin = re.search(success_pat, auth_page).groups()
            self.logged_in = True
        except:
            os.remove(self.cookiefile)
            raise ValueError('Login was unsuccessful.')


    def getSessionData(self):
        if self.cookie_jar is None:
            if self.logged_in is None:
                login_count = 0
                while not self.logged_in:
                    if self.user == "":
                        break
                    try:
                        self.login()
                    except:
                        if login_count < 3:
                            login_count += 1
                            time.sleep(1)
                        else:
                            raise

        wf_url = 'https://secure.net.wwe.com/enterworkflow.do?flowId=media'

        referer_str = ''
        txheaders = {'User-agent': USERAGENT,
                     'Referer': referer_str}
        req = urllib2.Request(url=wf_url, headers=txheaders, data=None)
        try:
            handle = urllib2.urlopen(req)
            self.extractCookies()
        except Exception:
            raise ValueError('Not logged in')
        url_data = handle.read()

        if self.auth:
            self.cookie_jar.save(self.cookiefile, ignore_discard=IGNORE_DISCARD)

        return url_data

    def get_video_url(self, content_id, live, bitrate):

        self.getSessionData()

        url = 'https://ws.media.net.wwe.com/ws/media/mf/op-findUserVerifiedEvent/v-2.3?'

        if live:
            subject = 'LIVE_EVENT_COVERAGE'
        else:
            subject = 'WWE_VOD_EVENT_ARCHIVE'

        query_values = {
            'contentId': content_id,
            'sessionKey': self.session_key,
            'fingerprint': urllib.unquote(self.cookies['fprt']),
            'identityPointId': self.cookies['ipid'],
            'playbackScenario': 'FMS_CLOUD',
            'subject': subject,
            'platform': 'WEB_MEDIAPLAYER'
        }

        url = url + urllib.urlencode(query_values)

        req = urllib2.Request(url)

        response = urllib2.urlopen(req)

        reply = xml.dom.minidom.parse(response)

        status_code = str(reply.getElementsByTagName('status-code')[0].childNodes[0].data)
        if status_code != "1":
            raise ValueError(SOAPCODES[status_code])

        self.session_key = reply.getElementsByTagName('session-key')[0].childNodes[0].data

        stream_url = reply.getElementsByTagName('url')[0].childNodes[0].data

        auth_pat = re.compile(r'auth=(.*)')
        auth_chunk = '?auth=' + re.search(auth_pat, stream_url).groups()[0]
        req = urllib2.Request(stream_url)
        handle = urllib2.urlopen(req)
        rsp = parse(handle)

        rtmp_base = rsp.getElementsByTagName('meta')[0].getAttribute('base')

        if 'ondemand' in rtmp_base:
            rtmp_base += '?_fcs_vhost=cp271756.edgefcs.net&akmfv=1.6&aifp=v0004' + auth_chunk

        for elem in rsp.getElementsByTagName('video'):
            try:
                speed = elem.getAttribute('system-bitrate')
            except ValueError:
                continue
            if bitrate.replace('K', '000') == speed:
                vid_src = elem.getAttribute('src')
                break

        swfurl = ' swfUrl=http://ui.bamstatic.com/fedapp/video/flash/fvp/wwenetwork/1.1.0/fvp.swf swfVfy=1'
        if live:
            swfurl += ' live=1'

        final_url = rtmp_base + ' Playpath=' + vid_src + auth_chunk + swfurl

        return final_url

    def logout(self):
        LOGOUT_URL="https://secure.net.wwe.com/enterworkflow.do?flowId=registration.logout"
        txheaders = {'User-agent': USERAGENT,
                     'Referer': 'http://network.wwe.com'}
        data = None
        req = urllib2.Request(LOGOUT_URL, data, txheaders)
        handle = urllib2.urlopen(req)
        logout_info = handle.read()
        handle.close()
        pattern = re.compile(r'You are now logged out.')
        if not re.search(pattern, logout_info):
            raise ValueError("Logout was unsuccessful.")
        else:
            self.logged_in = None

        self.cookie_jar = None
