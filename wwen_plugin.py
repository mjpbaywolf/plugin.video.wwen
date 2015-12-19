import sys
import urllib
import urlparse
from resources import wwe
import xbmcaddon
import xbmcgui
import xbmcplugin
from datetime import datetime, timedelta
import pickle

base_url = sys.argv[0]
addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
media_path = addon.getAddonInfo('path') + '/media/'
email = addon.getSetting('emailaddress')
password = addon.getSetting('password')


def build_url(query):
    return base_url + '?' + urllib.urlencode(query)


def get_list_item(network_item):
    liz = xbmcgui.ListItem(network_item.name, iconImage=network_item.icon, thumbnailImage=network_item.thumbnail)
    liz.setInfo(
        type="Video",
        infoLabels={
            "tvshowtitle": network_item.show_name,
            "title": network_item.title,
            "plot": network_item.description,
            "genre": network_item.genre,
            "year": network_item.air_date[0:4],
            "duration": network_item.duration,
            "aired": network_item.air_date})

    liz.setArt({'fanart': network_item.fan_art})
    liz.setArt({'banner': network_item.banner})

    if network_item.item_type == 'show':
        if network_item.on_watchlist:
            liz.addContextMenuItems([('Remove Series from Watchlist',
                                      'XBMC.RunPlugin(' + build_url({'mode': 'remove_series_watchlist',
                                                                     'id': network_item.media_id}) + ')')])
        else:
            liz.addContextMenuItems([('Add Series to Watchlist',
                                      'XBMC.RunPlugin(' + build_url({'mode': 'add_series_watchlist',
                                                                     'id': network_item.media_id}) + ')')])

    if network_item.item_type == 'episode':
        if network_item.on_watchlist:
            liz.addContextMenuItems([('Remove Episode from Watchlist',
                                      'XBMC.RunPlugin(' + build_url({'mode': 'remove_episode_watchlist',
                                                                     'id': network_item.media_id}) + ')')])
        else:
            liz.addContextMenuItems([('Add Episode to Watchlist',
                                      'XBMC.RunPlugin(' + build_url({'mode': 'add_episode_watchlist',
                                                                     'id': network_item.media_id}) + ')')])
        liz.setProperty('IsPlayable', 'true')

    return liz

if email == '' or password == '':
    xbmcgui.Dialog().ok("WWE Network", "Please visit www.WWENetwork.com", "and register for your login credentials")
    return_value = xbmcgui.Dialog().input('Enter WWE Network Account Email')
    if return_value and len(return_value) > 0:
        addon.setSetting('emailaddress', str(return_value))
        email = addon.getSetting('emailaddress')
    return_value = xbmcgui.Dialog().input('Enter WWE Network Account Password')
    if return_value and len(return_value) > 0:
        addon.setSetting('password', str(return_value))
        password = addon.getSetting('password')

wwe_network = wwe.Network(email, password)

cookie_exp_date = addon.getSetting('cookie_exp_date')

if cookie_exp_date != '' and pickle.loads(cookie_exp_date) > datetime.now():
    cookies = addon.getSetting('cookies')
    wwe_network.set_cookies(pickle.loads(cookies))
else:
    wwe_network.login()
    addon.setSetting('cookies', pickle.dumps(wwe_network.cookies))
    addon.setSetting('cookie_exp_date', pickle.dumps(datetime.now() + timedelta(days=1)))


mode = args.get('mode', None)

if mode is None:
    xbmcplugin.setContent(addon_handle, 'files')

    live = wwe_network.get_live_stream()
    li = get_list_item(live)
    li.setIconImage(media_path + 'live.png')
    li.setThumbnailImage(media_path + 'live.png')
    li.setArt({'fanart': addon.getAddonInfo('fanart')})
    li_url = build_url({'mode': live.item_type, "id": live.media_id})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=li_url, listitem=li)

    recommended = xbmcgui.ListItem("Recommended", iconImage=media_path + 'recommended.png', thumbnailImage=media_path + 'recommended.png')
    recommended.setArt({'fanart': addon.getAddonInfo('fanart')})
    recommended_url = build_url({'mode': 'recommended'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=recommended_url, listitem=recommended, isFolder=True)

    on_demand = xbmcgui.ListItem("On Demand", iconImage=media_path + 'on_demand.png', thumbnailImage=media_path + 'on_demand.png')
    on_demand.setArt({'fanart': addon.getAddonInfo('fanart')})
    on_demand_url = build_url({'mode': 'on_demand'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=on_demand_url, listitem=on_demand, isFolder=True)

    episodes_watchlist = xbmcgui.ListItem("Watchlist - Episodes", iconImage=media_path + 'watchlist.png', thumbnailImage=media_path + 'watchlist.png')
    episodes_watchlist.setArt({'fanart': addon.getAddonInfo('fanart')})
    episodes_watchlist_url = build_url({'mode': 'episodes_watchlist'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=episodes_watchlist_url, listitem=episodes_watchlist, isFolder=True)

    series_watchlist = xbmcgui.ListItem("Watchlist - Series", iconImage=media_path + 'watchlist.png', thumbnailImage=media_path + 'watchlist.png')
    series_watchlist.setArt({'fanart': addon.getAddonInfo('fanart')})
    series_watchlist_url = build_url({'mode': 'series_watchlist'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=series_watchlist_url, listitem=series_watchlist, isFolder=True)

    search = xbmcgui.ListItem("Search", iconImage=media_path + 'search.png', thumbnailImage=media_path + 'search.png')
    search.setArt({'fanart': addon.getAddonInfo('fanart')})
    search_url = build_url({"mode": "search"})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=search_url, listitem=search, isFolder=True)

    my_account = xbmcgui.ListItem("My Account", iconImage=media_path + 'my_account.png', thumbnailImage=media_path + 'my_account.png')
    my_account.setArt({'fanart': addon.getAddonInfo('fanart')})
    my_account_url = build_url({'mode': 'my_account'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=my_account_url, listitem=my_account, isFolder=True)
	
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)

elif mode[0] == 'recommended':
    xbmcplugin.setContent(addon_handle, 'episodes')

    for n in wwe_network.get_recommended():
        li = get_list_item(n)
        url = build_url({'mode': n.item_type, "id": n.media_id})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)

elif mode[0] == 'on_demand':
    xbmcplugin.setContent(addon_handle, 'tvshows')

    for n in wwe_network.get_sections():
        li = get_list_item(n)
        url = build_url({'mode': n.item_type, "id": n.media_id})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'episodes_watchlist':
    xbmcplugin.setContent(addon_handle, 'episodes')

    for n in wwe_network.get_episodes_watchlist():
        n.on_watchlist = True
        li = get_list_item(n)
        url = build_url({'mode': n.item_type, "id": n.media_id})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)

elif mode[0] == 'add_episode_watchlist':
    if wwe_network.add_episode_to_watchlist(args['id'][0]):
        xbmcgui.Dialog().notification('Success', 'Added episode to watchlist')
    else:
        xbmcgui.Dialog().notification('Error occurred', 'Failed to add episode to watchlist')

elif mode[0] == 'remove_episode_watchlist':
    if wwe_network.remove_episode_from_watchlist(args['id'][0]):
        xbmcgui.Dialog().notification('Success', 'Removed episode from watchlist')
    else:
        xbmcgui.Dialog().notification('Error occurred', 'Failed to remove episode from watchlist')

elif mode[0] == 'series_watchlist':
    xbmcplugin.setContent(addon_handle, 'tvshows')

    for n in wwe_network.get_series_watchlist():
        n.on_watchlist = True
        li = get_list_item(n)
        url = build_url({'mode': n.item_type, "id": n.media_id})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)

elif mode[0] == 'add_series_watchlist':
    if wwe_network.add_series_to_watchlist(args['id'][0]):
        xbmcgui.Dialog().notification('Success', 'Added series to watchlist')
    else:
        xbmcgui.Dialog().notification('Error occurred', 'Failed to add series to watchlist')

elif mode[0] == 'remove_series_watchlist':
    if wwe_network.remove_series_from_watchlist(args['id'][0]):
        xbmcgui.Dialog().notification('Success', 'Removed series from watchlist')
    else:
        xbmcgui.Dialog().notification('Error occurred', 'Failed to remove series from watchlist')

elif mode[0] == 'search':
    text = xbmcgui.Dialog().input('Search')

    if text:
        xbmcplugin.setContent(addon_handle, 'episodes')
        for s in wwe_network.search(text):
            li = get_list_item(s)
            url = build_url({'mode': s.item_type, "id": s.media_id})
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
        xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)

elif mode[0] == 'my_account':
    addon.openSettings()

elif mode[0] == 'section':
    xbmcplugin.setContent(addon_handle, 'tvshows')

    section_name = args['id'][0]
    for n in wwe_network.get_shows(section_name):
        li = get_list_item(n)
        url = build_url({'mode': n.item_type, "id": n.media_id})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'show':
    xbmcplugin.setContent(addon_handle, 'episodes')

    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DURATION)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)

    show_name = args['id'][0]
    for n in wwe_network.get_episodes(show_name):
        li = get_list_item(n)
        url = build_url({'mode': n.item_type, "id": n.media_id})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'episode':
    media_id = args['id'][0]
    try:
        item = xbmcgui.ListItem(path=wwe_network.get_video_url(media_id, addon.getSetting('bitrate')))
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
    except ValueError as e:
        xbmcgui.Dialog().notification('Error occurred', str(e.message))
    xbmcplugin.endOfDirectory(addon_handle)

