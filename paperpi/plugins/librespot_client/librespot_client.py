#!/usr/bin/env python3
# coding: utf-8




import logging






import requests
from epdlib.Screen import Update
from dictor import dictor
from copy import copy






try:
    from . import layout
    from . import constants
except ImportError:
    import layout
    import constants






logger = logging.getLogger(__name__)






def update_function(self):
    logging.info(f'update_function for plugin {self.name}, version {constants.version}')    
    is_updated = False
    # make a shallow copy so the data object can be updated through the procedure
    data = copy(constants.data)
    priority = 2**15
    failure = (is_updated, data, priority)

    # add a play_state attribute
    if not hasattr(self, 'play_state'):
        self.play_state = 'None'
    
    # add the idle timer on first run
    if not hasattr(self, 'idle_timer'):
        logging.debug(f'adding idle_timer of class `Update()`')
        self.idle_timer = Update()    
        
    # fetch token    
    logging.debug(f'fetching API access token from librespot player {self.config["player_name"]}')
    logging.debug(f'requesting spotify API access scope: {constants.spot_scope}')        
    try:
        token = requests.post(constants.libre_token_url)
    except requests.ConnectionError as e:
        logging.error(f'cannot proceed: failed to pull Spotify token from librespot at url: {constants.libre_token_url}')
        logging.error(f'{e}')
        return failure
    # check token
    logging.debug('checking API access token')
    if token.status_code == 200:
        logging.debug('token OK')
        try:
            headers = {'Authorization': 'Bearer ' + token.json()['token']}
        except JSONDecodeError as e:
            logging.error(f'failed to decode token JSON object: {e}')
            return failure
    else:
        logging.info(f'cannot proceed: no token available from librespot status: {token.status_code}')
        return failure
    
    # use the token to fetch player information from spotify
    logging.debug('fetch player status from Spotify')
    if 'Authorization' in headers:
        player_status = requests.get(constants.spot_player_url, headers=headers)
    else:
        logging.error(f'cannot proceed: no valid Authroization token found in response from librespot: {headers}')
        return failure    
    
    logging.debug('checking player_status')
    if player_status.status_code == 200:
        try:
            logging.debug('gathering json data')
            player_json = player_status.json()
        except JSONDecodeError as e:
            logging.error(f'cannot proceed: failed to decode player status JSON object: {e}')
            return failure
                
        # bail out if the player name does not match
        if not dictor(player_json, 'device.name').lower() == self.config['player_name'].lower():
            logging.info(f'{self.config["player_name"]} is not active: no data')
            return failure
    else:
        logging.info(f'{self.config["player_name"]} does not appear to be available')
        return failure
        
    # map spotify keys to local values
    for key in constants.spot_map:
        data[key] = dictor(player_json, constants.spot_map[key])

    if 'artwork_url' in data and 'id' in data:
        data['coverart'] = self.cache.cache_file(url=data['artwork_url'], file_id=data['id'])

    playing = dictor(player_status.json(), 'is_playing')
    if playing is True:
        logging.debug(f'{self.config["player_name"]} is playing')
        data['mode'] = 'play'
        # if the data has changed, bump the priority 
        if self.data == data:
            logging.debug('data matches')
            priority = self.max_priority
        else:
            logging.debug('data does not match')
            priority = self.max_priority - 1
            
        self.play_state = 'play'
        is_updated = True
        
    elif playing is False:
        data['mode'] = 'pause'
        ## moving from "play" to "pause", decrease priority
        if self.play_state == 'play':
            self.idle_timer.update()
            priority = self.max_priority + 1
        
        # if the idle timer has expired, decrease priority
        if self.idle_timer.last_updated > self.config['idle_timeout']:
            priority = self.max_priority + 3
        else:
            priority = self.max_priority + 1

        self.play_state = 'pause'        
        is_updated = True
        
    else:
        self.plays_state = None
        data['mode'] = None
        priority = 2**15
        is_updated = False
    
    logging.info(f'priority set to: {priority}')
    return is_updated, data, priority






# u, d, p = update_function(self)
# # if u != self.data:
# self.data = d
# print(f'idle timer: {self.idle_timer.last_updated}, idle_timeout {self.config["idle_timeout"]}')
# print(p)
# print(d)
# # print('*'*50)
# # print(self.data)






# from SelfDummy import SelfDummy
# from CacheFiles import CacheFiles

# logger.root.setLevel('DEBUG')
# logging.debug('foo')

# self = SelfDummy()
# self.max_priority = 0
# self.config = {'player_name': 'Spocon-Spotify',
#                'idle_timeout': 5}
# self.cache = CacheFiles()















