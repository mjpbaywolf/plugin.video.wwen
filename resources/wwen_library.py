__author__ = 'bay_wolf'

import urllib2
import json


class NetworkItem(object):
    item_type = 'episode'
    name = ""
    title = ""
    description = ""
    icon = ""
    thumbnail = ""
    fan_art = ""
    id = ""
    air_date = "2008-12-07"
    year = 0
    duration = ""

    def __init__(self, item_type='episode', name='', title='', description='', icon='', thumbnail='', fan_art='', id='', air_date='', year=0, duration=''):
        self.item_type = item_type
        self.name = name
        self.title = title
        self.description = description
        self.icon = icon
        self.thumbnail = thumbnail
        self.fan_art = fan_art
        self.id = id
        self.air_date = air_date
        self.year = year
        self.duration = duration


def get_live_stream():
    json_file = get_request('http://epg.media.net.wwe.com/epg_small.json')
    json_object = json.loads(json_file)
    live_stream = NetworkItem()

    for i in json_object['events']:
        if i['live_media_state'] == 'MEDIA_ON':
            live_stream.item_type = 'live'
            live_stream.name = 'Watch Live'
            live_stream.id = i['media_playback_ids']['live']['content_id']
            live_stream.icon = i['thumbnail_scenarios']['2']
            live_stream.thumbnail = i['thumbnail_scenarios']['60']
            live_stream.fan_art = i['thumbnail_scenarios']['66']
            live_stream.description = i['big_blurb']
            live_stream.year = i['dates_and_times']['air_date_gmt'][0:4]
            live_stream.title = i['title']
            live_stream.duration = get_length_in_minutes(i['duration'])
            break

    return live_stream


def get_sections():
    sections = [
        NetworkItem(
            'section',
            'WWE PPVs',
            'WWE PPVs',
            'All WWE Pay Per Views',
            'http://network.wwe.com/assets/images/7/5/6/90266756/cuts/PPV_Logo_WWE_New_7iruonk2_dhreqldm.jpg',
            'http://network.wwe.com/assets/images/7/5/6/90266756/cuts/PPV_Logo_WWE_New_7iruonk2_o0jdl9sx.jpg',
            'http://network.wwe.com/assets/images/7/5/6/90266756/cuts/PPV_Logo_WWE_New_7iruonk2_qcygj14h.jpg',
            'wwe'),
        NetworkItem(
            'section',
            'WCW PPVs',
            'WCW PPVs',
            'All WCW Pay Per Views',
            'http://network.wwe.com/assets/images/1/3/0/67190130/cuts/wcw_7ep4kukg_dovaff03.jpg',
            'http://network.wwe.com/assets/images/1/3/0/67190130/cuts/wcw_7ep4kukg_bi170tam.jpg',
            'http://network.wwe.com/assets/images/1/3/0/67190130/cuts/wcw_7ep4kukg_3fri1q8w.jpg',
            'wcw'),
        NetworkItem(
            'section',
            'ECW PPVs',
            'ECW PPVs',
            'All ECW Pay Per Views',
            'http://network.wwe.com/assets/images/8/1/6/67189816/cuts/ecw_81vrb1k5_w1c2m4xv.jpg',
            'http://network.wwe.com/assets/images/8/1/6/67189816/cuts/ecw_81vrb1k5_9oakn7lq.jpg',
            'http://network.wwe.com/assets/images/8/1/6/67189816/cuts/ecw_81vrb1k5_gv7fi6bt.jpg',
            'ecw'),
        NetworkItem(
            'section',
            'Originals',
            'Originals',
            'Original Programming',
            'http://network.wwe.com/assets/images/9/2/6/66393926/cuts/wwe_3tlu8ogp_csgao4hx.jpeg',
            'http://network.wwe.com/assets/images/9/2/6/66393926/cuts/wwe_3tlu8ogp_rw09n4c0.jpeg',
            'http://network.wwe.com/assets/images/9/2/6/66393926/cuts/wwe_3tlu8ogp_zzt8wbc1.jpeg',
            'original'),
        NetworkItem(
            'section',
            'In Ring',
            'In Ring',
            'In Ring Events',
            'http://network.wwe.com/assets/images/9/5/2/115985952/cuts/ATTITUDE_ERA_NET_ICON_32p1pr64_smoaiknt.jpg',
            'http://network.wwe.com/assets/images/9/5/2/115985952/cuts/ATTITUDE_ERA_NET_ICON_32p1pr64_4eio6ubf.jpg',
            'http://network.wwe.com/assets/images/9/5/2/115985952/cuts/ATTITUDE_ERA_NET_ICON_32p1pr64_9txv3zkg.jpg',
            'in_ring'),
        NetworkItem(
            'section',
            'Vault',
            'Vault',
            'Classic Wrestling Events',
            'http://network.wwe.com/assets/images/5/5/2/91736552/cuts/Nitro_Logo_9cvukpgb_q3gefbba.jpg',
            'http://network.wwe.com/assets/images/5/5/2/91736552/cuts/Nitro_Logo_9cvukpgb_cd2aiocc.jpg',
            'http://network.wwe.com/assets/images/5/5/2/91736552/cuts/Nitro_Logo_9cvukpgb_um0c5ked.jpg',
            'vault'
        )
    ]

    return sections


def get_shows(section):
    shows = []

    json_file = get_request('http://network.wwe.com/gen/content/tag/v1/section/' + section + '/jsonv4.json')
    json_object = json.loads(json_file)

    for i in json_object['list']:
        if i['type'] == 'wwe-show':
            shows.append(
                NetworkItem(
                    'show',
                    i['title'],
                    i['title'],
                    i['bigblurb'] if 'bigblurb' in i else '',
                    i['thumbnails']['124x70']['src'],
                    i['thumbnails']['400x224']['src'],
                    i['thumbnails']['1280x720']['src'] if '1280x720' in i else '',
                    i['itemTags']['show_name'][0],
                    i['userDate'],
                    i['userDate'][0:4]
                )
            )

    return shows


def get_episodes(show):
    episodes = []

    json_file = get_request('http://network.wwe.com/gen/content/tag/v1/show_name/r/' + show + '/jsonv4.json')
    json_object = json.loads(json_file)

    for i in json_object['itemTagLibrary']['year']:
        json_file2 = get_request('http://network.wwe.com/gen/content/tag/v1/show_name/' + i + '/r/' + show + '/jsonv4.json')
        json_object2 = json.loads(json_file2)
        for j in json_object2['list']:
            if j['type'] == 'wwe-asset' and all(e.name != j['headline'] for e in episodes):
                episodes.append(
                    NetworkItem(
                        'episode',
                        j['headline'],
                        j['headline'],
                        j['bigblurb'],
                        j['thumbnails']['124x70']['src'],
                        j['thumbnails']['400x224']['src'],
                        i['thumbnails']['1280x720']['src'] if '1280x720' in i else '',
                        j['itemTags']['media_playback_id'][0],
                        j['userDate'],
                        j['userDate'][0:4],
                        get_length_in_minutes(j['duration'])
                    )
                )

    return episodes


def get_request(url, data=None, headers=None):

    if headers is None:
        headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:19.0) Gecko/20100101 Firefox/19.0',
                   'Referer': 'http://www.wwe.com'}
    opener = urllib2.build_opener()
    urllib2.install_opener(opener)
    try:
        # Debug
        req = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        print response.info()

        return data
    except urllib2.URLError, e:
        return


def get_length_in_minutes(length):
    l_split = length.split(':')
    minutes = (int(l_split[0])) * 60
    minutes += int(l_split[1])
    return minutes
