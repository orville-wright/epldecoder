#!/usr/bin/python3
import requests
from requests import Request, Session
import json
import sys
import unicodedata
import logging
import http.client

from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
from six import iteritems
from six import itervalues

# logging setup
logging.basicConfig(level=logging.INFO)

FPL_API_URL = "https://fantasy.premierleague.com/api/"
BSS = "bootstrap-static/"
BSD = "bootstrap-dynamic/"
MYTEAM = "my-team/"
ENTRY = "entry/"
ME = "me/"
USER_SUMMARY_SUBURL = "element-summary/"
LCS_SUBURL = "leagues-classic/"
#LCS_SUBURL = "leagues-classic-standings/"
LEAGUE_H2H_STANDING_SUBURL = "leagues-h2h-standings/"
PLAYERS_INFO_SUBURL = "bootstrap-static"
PLAYERS_INFO_FILENAME = "allPlayersInfo.json"
#STANDINGS_URL = "https://fantasy.premierleague.com/drf/leagues-classic-standings/"
STANDINGS_URL = "https://fantasy.premierleague.com/api/leagues-classic/"
PAGINATION = "?page_new_entries=1&page_standings=1&phase=1"
#CLASSIC_PAGE = "&le-page=1&ls-page=1"

############################################
# note: Must be authourized by credentials
#
class fpl_bootstrap:
    """Base class for extracting the core game ENTRY dataset"""
    """This class requires valid credentials"""
    """but does not contain the full player private ENTRY dataset"""

    # Class Global attributes
    username = ""
    password = ""
    current_event = ""
    api_get_status = ""
    standings_t = ""
    epl_team_names = {}
    my_cookie = ""

    def __init__(self, playeridnum, username, password):
        self.playeridnum = str(playeridnum)
        self.username = username
        self.password = password
        fpl_bootstrap.username = username    # make USERNAME var global to class instance
        fpl_bootstrap.password = password    # make PASSWORD var global to class instance

        logging.info('fpl_bootstrap:: - create bootstrap ENTRY class instance for player: %s' % self.playeridnum )

        self.epl_team_names = {}    # global PRIVATE helper dict accessible from within this base class
        s = requests.Session()
        user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0'}
        API_URL0 = 'https://fantasy.premierleague.com/a/login'
#        API_URL0 = 'https://fantasy.premierleague.com/'
        API_URL1 = FPL_API_URL + BSS

# WARNING: This cookie must be updated each year at the start of the season as it is changed each year.
# 2018 cookie - ({'pl_profile': 'eyJzIjogIld6VXNNalUyTkRBM01USmQ6MWZpdE1COjZsNkJ4bngwaGNUQjFwa3hMMnhvN2h0OGJZTSIsICJ1IjogeyJsbiI6ICJBbHBoYSIsICJmYyI6IDM5LCAiaWQiOiAyNTY0MDcxMiwgImZuIjogIkRyb2lkIn19'})
# 2019 cookie - ({'pl_profile': 'eyJzIjogIld6VXNNalUyTkRBM01USmQ6MWVOWUo4OjE1QWNaRW5EYlIwM2I4bk1HZDBqX3Z5VVk2WSIsICJ1IjogeyJsbiI6ICJBbHBoYSIsICJmYyI6IDgsICJpZCI6IDI1NjQwNzEyLCAiZm4iOiAiRHJvaWQifX0='})
# 2019 worked - ({'pl_profile': 'eyJzIjogIld6VXNNalUyTkRBM01USmQ6MWZpdE1COjZsNkJ4bngwaGNUQjFwa3hMMnhvN2h0OGJZTSIsICJ1IjogeyJsbiI6ICJBbHBoYSIsICJmYyI6IDM5LCAiaWQiOiAyNTY0MDcxMiwgImZuIjogIkRyb2lkIn19'})
        pl_profile_cookies = { \
                '1212166': 'eyJzIjogIld6VXNNalUyTkRBM01USmQ6MWZpdE1COjZsNkJ4bngwaGNUQjFwa3hMMnhvN2h0OGJZTSIsICJ1IjogeyJsbiI6ICJBbHBoYSIsICJmYyI6IDM5LCAiaWQiOiAyNTY0MDcxMiwgImZuIjogIkRyb2lkIn19', \
                '1995215': 'eyJzIjogIld6SXNNalUyTkRBM01USmQ6MWh5aE9BOmdLcXg0S3RkSGR5UVRXRjUwVjhxZHR4RVNTayIsICJ1IjogeyJpZCI6IDI1NjQwNzEyLCAiZm4iOiAiRHJvaWQiLCAibG4iOiAiQWxwaGEiLCAiZmMiOiA1N319', \
                '1994221': 'eyJzIjogIld6SXNOVGc0T0RnM05WMDoxaHlpdU46MlhhRDZlbkx3YU03WFdtb0tBWEhsYXlESlBnIiwgInUiOiB7ImlkIjogNTg4ODg3NSwgImZuIjogIkRhdmlkIiwgImxuIjogIkJyYWNlIiwgImZjIjogOH19', \
                '1136396': 'eyJzIjogIld6VXNOVGc0T0RnM05WMDoxZnYzYWo6WGkxd1lMMnpLeW1pbThFTTVFeGEzVFdUaWtBIiwgInUiOiB7ImxuIjogIkJyYWNlIiwgImZjIjogOCwgImlkIjogNTg4ODg3NSwgImZuIjogIkRhdmlkIn19' }

        for pl, cookie_hack in pl_profile_cookies.items():
            if pl == self.playeridnum:
                s.cookies.update({'pl_profile': cookie_hack})
                logging.info('fpl_bootstrap:: FOUND - cookie for playerid: %s' % pl )
                logging.info('fpl_bootstrap:: SET - cookie to: %s' % cookie_hack )
                fpl_bootstrap.api_get_status = "GOODCOOKIE"
                fpl_bootstrap.my_cookie = cookie_hack    # save cookie as instance accessor
                break    # found this players cookie
            else:
                logging.info('fpl_bootstrap:: NO MATCH - playerid/cookie: %s' % pl )
                fpl_bootstrap.api_get_status = "FAILED"

        if fpl_bootstrap.api_get_status == "FAILED":
            logging.info('fpl_bootstrap:: - FAIL - No cookie for player: %s EXITING... %s' % pl )
            return
        else:
            pass

# REST API I/O now... - 1st get authenticates, but must use critical cookie (i.e. "pl_profile")
# 2nd get does the data extraction if auth succeeds - failure = all JSON dicts/fields are empty
        rx0 = s.get( API_URL0, headers=user_agent, auth=HTTPBasicAuth(self.username, self.password) )
        rx1 = s.get( API_URL1, headers=user_agent, auth=HTTPDigestAuth(self.username, self.password) )
        self.auth_status = rx0.status_code
        self.gotdata_status = rx1.status_code
        logging.info('fpl_bootstrap:: - init - Logon AUTH url: %s' % rx0.url )
        logging.info('fpl_bootstrat:: - init - API data get url: %s' % rx1.url )

        rx0_auth_cookie = requests.utils.dict_from_cookiejar(s.cookies)
        logging.info('fpl_bootstrap:: AUTH login resp cookie: %s' % rx0_auth_cookie['pl_profile'] )

        if rx0.status_code != 200:    # failed to authenticate
            logging.info('fpl_bootstrap:: - init ERROR login AUTH failed with resp %s' % self.auth_status )
            return

        if rx1.status_code != 200:    # 404 API get failed
            logging.info('fpl_bootstrap:: - init ERROR API get failed with resp %s' % self.gotdata_status )
            return
        else:
            logging.info('fpl_bootstrap:: - Login AUTH success resp: %s' % self.auth_status )
            logging.info('fpl_bootstrap:: - API data GET resp is   : %s  ' % self.gotdata_status )
            # create JSON dict with players ENTRY data, plus other data thats now available
            # WARNING: This is a very large JSON data structure with stats on every squad/player in the league
            #          Dont load into memory multiple times. Best to insert into mongodb & access from there
            # EXTRACT JSON data/fields...
            # note: entry[] and player[] are not auto loaded when dataset lands (not sure why)
            t0 = json.loads(rx1.text)
            self.events = t0['events']
            self.game_settings = t0['game_settings']
            self.phases = t0['phases']
            self.teams = t0['teams']                    # All details of EPL teams in Premieership league this year
            self.elements = t0['elements']              # big data-set for every EPL squad player full details/stats
            self.stats = t0['element_stats']              # big data-set for every EPL squad player full details/stats
            self.element_types = t0['element_types']

# DELETE ME : THis JSON model was depricated in 2019/2020 season
            #self.elements = t0['elements']              # big data-set for every EPL squad player full details/stats
            # self.player = t0['player']                  # initially empty
            #self.element_types = t0['element_types']
            #self.next_event = t0['next-event']          # global accessor within data-set (do not modify)
            #self.phases = t0['phases']
            #self.stats = t0['stats']
            #self.game_settings = t0['game-settings']
            #self.current_event = t0['current-event']    # global accessor in class (do not modify)
            #self.teams = t0['teams']                    # All details of EPL teams in Premieership league this year
            #self.stats_options = t0['stats_options']
            #self.entry = t0['entry']                    # initially empty
            #self.next_event_fixtures = t0['next_event_fixtures']    # array of the next 10 fixtures (could be played across multiple days)
            #self.events = t0['events']

            fpl_bootstrap.current_event = self.current_event    # set class global var so current week is easily accessible
        return

    def whois_element(self, elementid):
        """Scan main bootstrap data-set for a specific EPL squad player ID"""
        """and get the real firstname/last name of this EPL player"""

        self.element_target = str(elementid)
        logging.info('fpl_bootstrap:: whois_element() - scan target: %s' % elementid )
        for element in self.elements:
            if element['id'] == elementid:
                self.first_name = element['first_name']        # extract the pertinent data
                self.last_name = element['second_name']        # extract the pertinent data
                return self.first_name+" "+self.last_name
            else:
                pass
        return

    def what_team_name(self, elementid):
        """Scan main bootstrap data-set for a specific EPL squad player ID"""
        """and get the real TEAM name that this EPL player is a member of"""

        logging.info('fpl_bootstrap.what_team_name() - scan target: %s' % elementid )
        # get this players team code - explicitly address exact
        # find_him = int(elementid-1)
        # his_team = self.elements[find_him]['team_code']

        self.element_target = str(elementid)
        logging.info('fpl_bootstrap.what_team_name() - scan target: %s' % elementid )
        for element in self.elements:
            if element['id'] == elementid:
                self.his_team = element['team_code']
                break    # fast exit once we have the team code
            else:
                pass

# laxy bad code...no check for failure

        for element in self.teams:
            if element['code'] == self.his_team:
                # self.long_name = element['name']        # extract the data
                self.short_name = element['short_name']        # extract the  data
                return self.short_name
            else:
                pass
        return

    def element_gw_points(self, elementid):
        """get the GAMEWEEK poinmts of an EPL player reff'd by an element ID number"""

        self.e_target = str(elementid)
        logging.info('fpl_bootstrap:: element_gw_points() - scan target: %s' % self.e_target )
        #xxxx = self.elements[elementid]
        for element in self.elements:
            if element['id'] == elementid:
                self.gw_points_raw = element['event_points']    # note: raw points total, exlcuding bonus, multipliers & deductions
                return self.gw_points_raw
            else:
                pass
        return

    def list_epl_teams(self):
        """BUILD a small private class helper dict that holds epl team ID and real names"""
        """this dict is accessible via the base class fpl_bootstrap"""

        # this method makes sense to belong to BOOTSTRAP class
        logging.info('fpl_bootstrap:: list_epl_teams() - init' )    # setup a dict of team IDs + NAMES for easy reference
        for team_name in self.teams:        # a core section in the JSON bootstrap model
            #print ( "Team:", team_name['id'], team_name['short_name'], team_name['name'] )
            self.epl_team_names[team_name['id']] = team_name['name']    # populate the class dict, which is accessible within the class fpl_bootstrap()
        return


    def my_cookie(self):
        """Small helper method to output this users cookie that must be used"""
        """for any authentication operations"""

        logging.info('fpl_bootstrap.my_cookie() - cookie pl_profile: %s' % fpl_bootstrap.my_cookie )
        return fpl_bootstrap.my_cookie
