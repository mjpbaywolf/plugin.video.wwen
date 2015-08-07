__author__ = 'bay_wolf'

import os
import sys
import urllib
import urlparse
from resources import wwen_library, wwen_auth2
import xbmcaddon
import xbmcgui
import xbmcplugin

addon = xbmcaddon.Addon()
addon_path = xbmc.translatePath(addon.getAddonInfo('path'))
profile = xbmc.translatePath(addon.getAddonInfo('profile'))
cookie_file = os.path.join(profile, 'cookie_file')

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

xbmcplugin.setContent(addon_handle, 'tvshows')

wwe_auth = wwen_auth2.WWESession(addon.getSetting('emailaddress'), addon.getSetting('password'), cookie_file)


def build_url(query):
    return base_url + '?' + urllib.urlencode(query)


def get_list_item(network_item):

    liz = xbmcgui.ListItem(network_item.name, iconImage=network_item.icon, thumbnailImage=network_item.thumbnail)
    liz.setInfo(
        type="Video",
        infoLabels={
            "Title": network_item.title,
            "Plot": network_item.description,
            "Genre": 'Wrestling',
            "Year": network_item.year,
            "Duration": network_item.duration})

    liz.setProperty("Fanart_Image", network_item.fan_art)

    if network_item.item_type == 'episode' or network_item.item_type == 'live':
        liz.setProperty('IsPlayable', 'true')

    return liz

mode = args.get('mode', None)

if mode is None:
    live = wwen_library.get_live_stream()
    li = get_list_item(live)
    url = build_url({'mode': live.item_type, "id": live.id})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)

    for n in wwen_library.get_sections():
        li = get_list_item(n)
        url = build_url({'mode': n.item_type, "id": n.id})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'section':
    section_name = args['id'][0]
    for n in wwen_library.get_shows(section_name):
        li = get_list_item(n)
        url = build_url({'mode': n.item_type, "id": n.id})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'show':
    show_name = args['id'][0]
    for n in wwen_library.get_episodes(show_name):
        li = get_list_item(n)
        url = build_url({'mode': n.item_type, "id": n.id})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'episode':
    content_id = args['id'][0]
    try:
        item = xbmcgui.ListItem(path=wwe_auth.get_video_url(content_id, False, addon.getSetting('bitrate')))
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
    except ValueError as e:
        xbmcgui.Dialog().notification('Error occurred', str(e.message))

elif mode[0] == 'live':
    content_id = args['id'][0]
    try:
        item = xbmcgui.ListItem(path=wwe_auth.get_video_url(content_id, True, addon.getSetting('bitrate')))
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
    except ValueError as e:
        xbmcgui.Dialog().notification('Error occurred', str(e.message))
