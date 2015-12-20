import re
from urllib import unquote
import requests
from xml.dom.minidom import parseString


PRE_LOGIN_URL = "https://secure.net.wwe.com/enterworkflow.do?flowId=account.login"
LOGIN_URL = "https://secure.net.wwe.com/workflow.do"
LOGOUT_URL = "https://secure.net.wwe.com/enterworkflow.do?flowId=registration.logout"
VIDEO_URL = "https://ws.media.net.wwe.com/ws/media/mf/op-findUserVerifiedEvent/v-2.3"
SOAPCODES = {
    "1": "OK",
    "-1000": "Requested Media Not Found",
    "-1500": "Other Undocumented Error",
    "-2000": "Authentication Error",
    "-2500": "Blackout Error",
    "-3000": "Identity Error",
    "-3500": "Sign-on Restriction Error",
    "-4000": "System Error",
}


class NetworkItem(object):
    def __init__(self):
        self.item_type = "episode"
        self.show_name = ""
        self.name = ""
        self.title = ""
        self.description = ""
        self.icon = ""
        self.thumbnail = ""
        self.fan_art = ""
        self.banner = ""
        self.media_id = ""
        self.air_date = ""
        self.duration = ""
        self.genre = ""
        self.on_watchlist = False


class Network:

    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.user_uuid = ''
        self.cookies = None
        self.logged_in = False

    def login(self):
        with requests.Session() as s:

            s.get(PRE_LOGIN_URL)

            auth_values = {'registrationAction': 'identify',
                           'emailAddress': self.user,
                           'password': self.password}

            s.post(LOGIN_URL, data=auth_values)

            try:
                self.user_uuid = unquote(s.cookies['mai']).split('useruuid=')[1].replace('[', '').replace(']', '')
                self.cookies = s.cookies
                self.logged_in = True
            except:
                raise ValueError('Login was unsuccessful.')

    def set_cookies(self, cookies):
        self.user_uuid = unquote(cookies['mai']).split('useruuid=')[1].replace('[', '').replace(']', '')
        self.cookies = cookies
        self.logged_in = True

    def get_video_url(self, content_id, bit_rate):
        if not self.logged_in:
            self.login()

        query_values = {
            'contentId': content_id,
            'fingerprint': unquote(self.cookies['fprt']),
            'identityPointId': self.cookies['ipid'],
            'playbackScenario': 'FMS_CLOUD',
        }

        with requests.Session() as s:
            s.cookies = self.cookies
            response = s.get(VIDEO_URL, params=query_values).content
            parsed_response = parseString(response)

            status_code = parsed_response.getElementsByTagName('status-code')[0].childNodes[0].data
            if status_code != "1":
                raise ValueError(SOAPCODES[status_code])

            stream_url = parsed_response.getElementsByTagName('url')[0].childNodes[0].data

            smil = parseString(s.get(stream_url).content)

            rtmp_base = smil.getElementsByTagName('meta')[0].getAttribute('base')

            auth_pat = re.compile(r'auth=(.*)')
            auth_chunk = '?auth=' + re.search(auth_pat, stream_url).groups()[0]

            if 'ondemand' in rtmp_base:
                rtmp_base += '?_fcs_vhost=cp271756.edgefcs.net&akmfv=1.6&aifp=v0004' + auth_chunk
            else:
                rtmp_base += '?_fcs_vhost=cp269217.live.edgefcs.net&akmfv=1.6&aifp=v0004' + auth_chunk

            swf_url = 'http://ui.bamstatic.com/fedapp/video/flash/fvp/wwenetwork/3.0.0/fvp.swf swfVfy=1'
            if 'live' in rtmp_base:
                swf_url += ' live=1'

            for elem in smil.getElementsByTagName('video'):
                try:
                    speed = elem.getAttribute('system-bitrate')
                    vid_src = elem.getAttribute('src')
                    if bit_rate.replace('K', '000') == speed:
                        break
                except ValueError:
                    continue

            return rtmp_base + ' Playpath=' + vid_src + auth_chunk + ' swfUrl=' + swf_url

    def logout(self):
        with requests.Session() as s:
            s.cookies = self.cookies
            response = s.get(LOGOUT_URL)
            pattern = re.compile(r'You are now logged out.')
            if not re.search(pattern, response):
                raise ValueError("Logout was unsuccessful.")

    def get_live_stream(self):
        json_object = requests.get('http://epg.media.net.wwe.com/epg_small.json').json()
        live_stream = NetworkItem()

        for i in json_object['events']:
            if i['live_media_state'] == 'MEDIA_ON':
                live_stream.item_type = 'episode'
                live_stream.show_name = i['show_name']
                live_stream.name = 'LIVE: ' + i['title']
                live_stream.title = i['title']
                live_stream.media_id = i['media_playback_ids']['live']['content_id']
                live_stream.icon = i['thumbnail_scenarios']['7']
                live_stream.thumbnail = i['thumbnail_scenarios']['35']
                live_stream.fan_art = i['thumbnail_scenarios']['67']
                live_stream.banner = i['thumbnail_scenarios']['63']
                live_stream.description = i['big_blurb']
                live_stream.air_date = i['dates_and_times']['air_date_gmt']
                live_stream.duration = self.get_length_in_seconds(i['duration'])
                live_stream.genre = i['genre']
                break

        return live_stream

    def get_sections(self):
        sections = []

        ppv_response = requests.get('http://network.wwe.com/gen/content/tag/v1/section/ppv/jsonv4.json').json()
        for i in ppv_response['list']:
            if i['type'] == 'wwe-section':
                temp = NetworkItem()
                temp.item_type = 'section'
                temp.title = i['title']
                temp.name = i['title']
                temp.icon = i['thumbnails']['124x70']['src']
                temp.thumbnail = i['thumbnails']['400x224']['src']
                if '1920x1080' in i['thumbnails']:
                    temp.fan_art = i['thumbnails']['1920x1080']['src']
                else:
                    temp.fan_art = i['thumbnails']['1280x720']['src']
                temp.media_id = i['key']
                temp.air_date = i['userDate']
                sections.append(temp)

        show_response = requests.get('http://network.wwe.com/gen/content/tag/v1/section/shows/jsonv4.json').json()
        for i in show_response['list']:
            if i['type'] == 'wwe-section':
                temp = NetworkItem()
                temp.item_type = 'section'
                temp.title = i['title']
                temp.name = i['title']
                temp.icon = i['thumbnails']['124x70']['src']
                temp.thumbnail = i['thumbnails']['400x224']['src']
                if '1920x1080' in i['thumbnails']:
                    temp.fan_art = i['thumbnails']['1920x1080']['src']
                else:
                    temp.fan_art = i['thumbnails']['1280x720']['src']
                temp.media_id = i['key']
                temp.air_date = i['userDate']
                sections.append(temp)

        return sections

    def get_recommended(self):
        recommended = []

        json_object = requests.get('http://network.wwe.com/gen/content/tag/v1/list/recommended/jsonv4.json').json()
        for i in json_object['list']:
            if i['type'] == 'wwe-asset' and all(r.name != i['headline'] for r in recommended):
                temp = NetworkItem()
                temp.item_type = "episode"
                temp.show_name = i['show_name']
                temp.name = i['headline']
                temp.title = i['headline']
                temp.description = i['notes']
                temp.icon = i['thumbnails']['124x70']['src']
                temp.thumbnail = i['thumbnails']['400x224']['src']
                if '1920x1080' in i['thumbnails']:
                    temp.fan_art = i['thumbnails']['1920x1080']['src']
                else:
                    temp.fan_art = i['thumbnails']['1280x720']['src']
                temp.media_id = i['itemTags']['media_playback_id'][0]
                temp.air_date = i['userDate']
                temp.duration = self.get_length_in_seconds(i['duration'])
                temp.genre = i['genre']
                recommended.append(temp)

        return recommended

    def search(self, search_text):
        results = []

        search_url = 'http://network.wwe.com/ws/search/generic'
        query_values = {
                'result_format': 'json',
                'bypass': 'y',
                'hitsPerPage': '75',
                'indextype': 'homebase',
                'parental_control': 'n',
                'query': search_text,
                'sort_type': 'relevance'
            }

        response = requests.get(search_url, params=query_values).json()

        for i in response['content']:
            if i['subtype'] == 'wwe-asset' and all(r.name != i['headline'] for r in results):
                temp = NetworkItem()
                temp.item_type = "episode"
                temp.show_name = i['show_name']
                temp.name = i['headline']
                temp.title = i['headline']
                temp.description = i['notes'] if 'notes' in i else ''
                temp.icon = i['thumbnail7'] if 'thumbnail17' in i else ''
                temp.thumbnail = i['thumbnail35'] if 'thumbnail35' in i else ''
                temp.fan_art = i['thumbnail67'] if 'thumbnail67' in i else ''
                temp.media_id = i['media_playback_id_key']
                temp.air_date = i['air_date']
                temp.duration = self.get_length_in_seconds(i['duration'])
                temp.genre = i['genre']
                results.append(temp)

        return results

    def get_shows(self, section):
        shows = []

        json_object = requests.get('http://network.wwe.com/gen/content/tag/v1/section/' + section + '/jsonv4.json').json()

        for i in json_object['list']:
            if i['type'] == 'wwe-show':
                temp = NetworkItem()
                temp.item_type = 'show'
                temp.title = i['title']
                temp.name = i['title']
                temp.icon = i['thumbnails']['124x70']['src']
                temp.thumbnail = i['thumbnails']['400x224']['src']
                if '1920x1080' in i['thumbnails']:
                    temp.fan_art = i['thumbnails']['1920x1080']['src']
                else:
                    temp.fan_art = i['thumbnails']['1280x720']['src']
                temp.media_id = i['itemTags']['show_name'][0]
                temp.air_date = i['userDate']
                shows.append(temp)

        return shows

    def get_episodes(self, show):
        episodes = []

        json_object = requests.get('http://network.wwe.com/gen/content/tag/v1/show_name/r/' + show + '/jsonv4.json').json()
        for i in json_object['list']:
            if i['type'] == 'wwe-asset' and all(e.media_id != i['itemTags']['media_playback_id'][0] for e in episodes):
                temp = NetworkItem()
                temp.item_type = "episode"
                temp.show_name = i['show_name']
                temp.name = i['headline']
                temp.title = i['headline']
                temp.description = i['notes']
                temp.icon = i['thumbnails']['124x70']['src']
                temp.thumbnail = i['thumbnails']['400x224']['src']
                if '1920x1080' in i['thumbnails']:
                    temp.fan_art = i['thumbnails']['1920x1080']['src']
                else:
                    temp.fan_art = i['thumbnails']['1280x720']['src']
                temp.media_id = i['itemTags']['media_playback_id'][0]
                temp.air_date = i['userDate']
                temp.duration = self.get_length_in_seconds(i['duration'])
                temp.genre = i['genre']
                episodes.append(temp)

        for i in json_object['itemTagLibrary']['year']:
            json_object2 = requests.get('http://network.wwe.com/gen/content/tag/v1/show_name/' + i + '/r/' + show + '/jsonv4.json').json()
            for j in json_object2['list']:
                if j['type'] == 'wwe-asset' and all(e.media_id != j['itemTags']['media_playback_id'][0] for e in episodes):
                    temp = NetworkItem()
                    temp.item_type = 'episode'
                    temp.title = j['headline']
                    temp.name = j['headline']
                    temp.description = j['notes']
                    temp.icon = j['thumbnails']['124x70']['src']
                    temp.thumbnail = j['thumbnails']['400x224']['src']
                    if '1920x1080' in j['thumbnails']:
					    temp.fan_art = j['thumbnails']['1920x1080']['src']
                    else:
					    temp.fan_art = j['thumbnails']['1280x720']['src']
                    temp.media_id = j['itemTags']['media_playback_id'][0]
                    temp.air_date = j['userDate']
                    temp.duration = self.get_length_in_seconds(j['duration'])
                    temp.genre = j['genre']
                    episodes.append(temp)

        return sorted(episodes, key=lambda x: x.air_date)

    def get_episodes_watchlist(self):
        watchlist = []

        url = "http://wwe-streamrest.am1.prod.ext.bamgrid.com/user/" + self.user_uuid + "/watchlist/episode"

        episode_response = requests.get(url).json()
        if episode_response['statusCode'] == 200:
            for i in episode_response['watchList']['items']:
                temp = NetworkItem()
                temp.item_type = "episode"
                temp.show_name = i['episode']['show_name']
                temp.name = i['episode']['headline']
                temp.title = i['episode']['headline']
                temp.description = i['episode']['notes']
                temp.icon = i['episode']['thumbnails']['124x70']['src']
                temp.thumbnail = i['episode']['thumbnails']['400x224']['src']
                if '1920x1080' in i['episode']['thumbnails']:
                    temp.fan_art = i['episode']['thumbnails']['1920x1080']['src']
                else:
                    temp.fan_art = i['episode']['thumbnails']['1280x720']['src']
                temp.media_id = i['episode']['itemTags']['media_playback_id'][0]
                temp.air_date = i['episode']['itemTags']['air_date'][0]
                temp.duration = self.get_length_in_seconds(i['episode']['duration'])
                temp.genre = i['episode']['genre']
                watchlist.append(temp)

        return watchlist

    def add_episode_to_watchlist(self, media_id):
        base_url = "http://wwe-streamrest.am1.prod.ext.bamgrid.com/user/" + self.user_uuid + "/watchlist/episode/"
        response = requests.put(base_url + media_id)
        if 200 <= response.status_code < 300:
            return True
        else:
            return False

    def remove_episode_from_watchlist(self, media_id):
        base_url = "http://wwe-streamrest.am1.prod.ext.bamgrid.com/user/" + self.user_uuid + "/watchlist/episode/"
        response = requests.delete(base_url + media_id)
        if 200 <= response.status_code < 300:
            return True
        else:
            return False

    def get_series_watchlist(self):
        watchlist = []

        url = "http://wwe-streamrest.am1.prod.ext.bamgrid.com/user/" + self.user_uuid + "/watchlist/series"
        series_response = requests.get(url).json()
        if series_response['statusCode'] == 200:
            for i in series_response['watchList']['items']:
                temp = NetworkItem()
                temp.item_type = 'show'
                temp.title = i['series']['title']
                temp.name = i['series']['title']
                temp.icon = i['series']['thumbnails']['124x70']['src']
                temp.thumbnail = i['series']['thumbnails']['400x224']['src']
                if '1920x1080' in i['series']['thumbnails']:
                    temp.fan_art = i['series']['thumbnails']['1920x1080']['src']
                else:
                    temp.fan_art = i['series']['thumbnails']['1280x720']['src']
                temp.media_id = i['series']['itemTags']['show_name'][0]
                watchlist.append(temp)

        return watchlist

    def add_series_to_watchlist(self, show_name):
        base_url = "http://wwe-streamrest.am1.prod.ext.bamgrid.com/user/" + self.user_uuid + "/watchlist/series/"
        response = requests.put(base_url + show_name)
        if 200 <= response.status_code < 300:
            return True
        else:
            return False

    def remove_series_from_watchlist(self, show_name):
        base_url = "http://wwe-streamrest.am1.prod.ext.bamgrid.com/user/" + self.user_uuid + "/watchlist/series/"
        response = requests.delete(base_url + show_name)
        if 200 <= response.status_code < 300:
            return True
        else:
            return False

    def get_watched_duration(self, media_id):

        if len(media_id) == 0:
            watched_duration = dict()

            base_url = "http://wwe-streamrest.am1.prod.ext.bamgrid.com"
            ext_url = "/user/" + self.user_uuid + "/bookmarks"

            while True:
                json_object = requests.get(base_url + ext_url).json()
                ext_url = None

                if json_object['statusCode'] == 200:
                    for i in json_object['bookmarks']['items']:
                        watched_duration[i['contentId']] = i['playHead']
                    if len(json_object['bookmarks']['links']) > 0:
                        ext_url = json_object['bookmarks']['links'][0]['href']
                if not ext_url:
                    break

            duration_items = watched_duration

        return duration_items[media_id]

    def get_length_in_seconds(self, length):
        l_split = length.split(':')
        seconds = (int(l_split[0])) * 60 * 60
        seconds += int(l_split[1]) * 60
        seconds += int(l_split[2])
        return int(seconds)
