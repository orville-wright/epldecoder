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

FPL_API_URL = "https://fantasy.premierleague.com/drf/"
BST = "bootstrap"
BSS = "bootstrap-static"
BSD = "bootstrap-dynamic"
MYTEAM = "my-team/"
ENTRY = "entry/"
USER_SUMMARY_SUBURL = "element-summary/"
LCS_SUBURL = "leagues-classic-standings/"
LEAGUE_H2H_STANDING_SUBURL = "leagues-h2h-standings/"
PLAYERS_INFO_SUBURL = "bootstrap-static"
PLAYERS_INFO_FILENAME = "allPlayersInfo.json"
STANDINGS_URL = "https://fantasy.premierleague.com/drf/leagues-classic-standings/"
CLASSIC_PAGE = "&le-page=1&ls-page=1"

############################################
# note: Must be authourized by credentials
#
class fpl_bootstrap:
    """Base class for extracting the core game ENTRY dataset"""
    """This class requires valid credentials"""
    """but does not contain the full player private ENTRY dataset"""
    username = ""
    password = ""
    current_event = ""
    api_get_status = ""
    standings_t = ""


    def __init__(self, playeridnum, username, password):
        self.playeridnum = str(playeridnum)
        self.username = username
        self.password = password
        fpl_bootstrap.username = username    # make USERNAME var global to class instance
        fpl_bootstrap.password = password    # make PASSWORD var global to class instance

        logging.info('fpl_bootstrap:: - create bootstrap ENTRY class instance for player: %s' % self.playeridnum )

        self.epl_team_names = {}    # global helper dict accessible from wihtin this base class
        s = requests.Session()
        user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0'}
        API_URL0 = 'https://fantasy.premierleague.com/a/login'
        API_URL1 = FPL_API_URL + BST

# WARNING: This cookie must be updated each year at the start of the season as it is changed each year.
# 2018 cookie - ({'pl_profile': 'eyJzIjogIld6VXNNalUyTkRBM01USmQ6MWZpdE1COjZsNkJ4bngwaGNUQjFwa3hMMnhvN2h0OGJZTSIsICJ1IjogeyJsbiI6ICJBbHBoYSIsICJmYyI6IDM5LCAiaWQiOiAyNTY0MDcxMiwgImZuIjogIkRyb2lkIn19'})
# 2019 cookie - ({'pl_profile': 'eyJzIjogIld6VXNNalUyTkRBM01USmQ6MWVOWUo4OjE1QWNaRW5EYlIwM2I4bk1HZDBqX3Z5VVk2WSIsICJ1IjogeyJsbiI6ICJBbHBoYSIsICJmYyI6IDgsICJpZCI6IDI1NjQwNzEyLCAiZm4iOiAiRHJvaWQifX0='})
# 2019 worked - ({'pl_profile': 'eyJzIjogIld6VXNNalUyTkRBM01USmQ6MWZpdE1COjZsNkJ4bngwaGNUQjFwa3hMMnhvN2h0OGJZTSIsICJ1IjogeyJsbiI6ICJBbHBoYSIsICJmYyI6IDM5LCAiaWQiOiAyNTY0MDcxMiwgImZuIjogIkRyb2lkIn19'})
        pl_profile_cookies = { \
                '1212166': 'eyJzIjogIld6VXNNalUyTkRBM01USmQ6MWZpdE1COjZsNkJ4bngwaGNUQjFwa3hMMnhvN2h0OGJZTSIsICJ1IjogeyJsbiI6ICJBbHBoYSIsICJmYyI6IDM5LCAiaWQiOiAyNTY0MDcxMiwgImZuIjogIkRyb2lkIn19', \
                '1136396': 'eyJzIjogIld6VXNOVGc0T0RnM05WMDoxZnYzYWo6WGkxd1lMMnpLeW1pbThFTTVFeGEzVFdUaWtBIiwgInUiOiB7ImxuIjogIkJyYWNlIiwgImZjIjogOCwgImlkIjogNTg4ODg3NSwgImZuIjogIkRhdmlkIn19' }

        for pl, cookie_hack in pl_profile_cookies.items():
            if pl == self.playeridnum:
                s.cookies.update({'pl_profile': cookie_hack})
                logging.info('fpl_bootstrap:: SET pl_profile cookie for userid: %s' % pl )
                logging.info('fpl_bootstrap:: SET pl_profile cookie to: %s' % cookie_hack )
                fpl_bootstrap.api_get_status = "GOODCOOKIE"
                break    # found this players cookie
            else:
                logging.info('fpl_bootstrap:: ERR userid is bad. No cookie found/set: %s' % pl )
                fpl_bootstrap.api_get_status = "FAILED"

        if fpl_bootstrap.api_get_status == "FAILED":
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
            self.elements = t0['elements']              # big data-set for every EPL squad player full details/stats
            self.player = t0['player']                  # initially empty
            self.element_types = t0['element_types']
            self.next_event = t0['next-event']          # global accessor within data-set (do not modify)
            self.phases = t0['phases']
            self.stats = t0['stats']
            self.game_settings = t0['game-settings']
            self.current_event = t0['current-event']    # global accessor in class (do not modify)
            self.teams = t0['teams']                    # All details of EPL teams in Premieership league this year
            self.stats_options = t0['stats_options']
            self.entry = t0['entry']                    # initially empty
            self.next_event_fixtures = t0['next_event_fixtures']    # array of the next 10 fixtures (could be played across multiple days)
            self.events = t0['events']

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

    def upcomming_fixtures(self):
        """the bootstrap database holds a list of the next 10 gameweek fixtures"""
        """its just a quick way to  what fixtures are approaching in the near future"""

        logging.info('fpl_bootstrap:: upcomming_fixtures() - init' )
        tn_idx = fpl_bootstrap.list_epl_teams(self)    # build my nice helper team id/real name dict
        print ( "Next 10 fixtures..." )
        for fixture in self.next_event_fixtures:
            idx_h = int(fixture['team_h'])    # use INT to index into the team-name dict self.t that was populated in list_epl_teams()
            idx_a = int(fixture['team_a'])    # use INT to index into the team-name dict self.t that was populated in list_epl_teams()
# do some analytics on fixtures...
            #h_rank
            #a_rank
            #rank_missmatch = h_rank - a_rank    # bigger number = large disparity, more probability of big scoring game
            #h_gdiff   - noit stored anywhere in bootstrap JSON datatset
            #a_gdiff   - noit stored anywhere in bootstrap JSON datatset
            #gd_missmatch = h_gdiff - a_gdiff    # bigger delta = larg disparity, team are more missmatched in scoring/skill/power
            print ( "GW:", fixture['event'], "Day:", fixture['event_day'], "(", fixture['kickoff_time_formatted'], ") HOME:", self.epl_team_names[idx_h], "vs.", self.epl_team_names[idx_a], "AWAY" )
            #print ( "Gameplay decison: ", end="" )
            self.game_decisions(idx_h, idx_a)
            #print ( "Home team:", self.epl_team_names[idx_h] )
            #print ( "Away team:", self.epl_team_names[idx_a] )
            #print ( "Home team:", idx_h )
            #print ( "Away team:", idx_a )
        return

    def list_epl_teams(self):
        """populate a small private class helper dict that holds epl team ID and real names"""
        """this dict is accessible via the base class fpl_bootstrap"""

        logging.info('fpl_bootstrap:: list_epl_teams() - init' )    # setup a dict of team IDs + NAMES for easy reference
        for team_name in self.teams:
            #print ( "Team:", team_name['id'], team_name['short_name'], team_name['name'] )
            self.epl_team_names[team_name['id']] = team_name['name']    # populate the class dict, which is accessible within the class fpl_bootstrap()
        return

    def get_standings(self):
        """Create a full current league standings database & make avail in gloabl bootstrap instance"""
        """uses https://www.football-data.org API (my free throttled/limited API account """

        connection = http.client.HTTPConnection('api.football-data.org')
        headers = { 'X-Auth-Token': '01232ee1842c428291d3a04091e25916' }              # my private API token (throtteled @ 10 calls/min)
        connection.request('GET', '/v2/competitions/PL/standings', None, headers )    # EPL standings
        t1 = json.loads(connection.getresponse().read().decode())
        #print (t1)
        logging.info('fpl_bootstrap:: get_standings() - init')
        #    t1 = json.loads(rx1.text)
        self.filters = t1['filters']
        self.competition = t1['competition']
        self.season = t1['season']
        self.standings = t1['standings']
        self.regular_season_t = self.standings[0]    # standings totals
        self.regular_season_h = self.standings[1]    # standings home
        self.regular_season_a = self.standings[2]    # standings away
        self.standings_t_table = self.regular_season_t['table']    # data
        self.standings_h_table = self.regular_season_h['table']    # data
        self.standings_a_table = self.regular_season_h['table']    # data

        fpl_bootstrap.standings_t = self.regular_season_t    # save standings dict as class gloabl accessor
        return

    def game_decisions(self, team_h, team_a):
        logging.info('fpl_bootstrap:: game_decisions() - init ' )
        #self.get_standings()         # allways make sure league standings is updated/current before we start
        # thhis dict is needed becasue we are using mukltiple API's as data sources & those API's do *NOT*
        # use a standardized ID_number to represent each team. - (must be updated @ start of each season).
        # elements - 0 = www://football-data.org , 1 = www://fantasy.premierleague.com

        #WARNING: *** EPL doesnt use teamID much. it uses team code (which is int(index) in its JSON struct )
        # tuple: very fast but immutable : foorball-data.com-teamID, epl-teamid, bootstrap-teamid
        self.teamid_xlt = (1044, 91, 2, \
                        57, 3, 1, \
                        397, 36, 3, \
                        328, 90, 4, \
                        715, 97, 5, \
                        61, 8, 6, \
                        354, 31, 7, \
                        62, 11, 8, \
                        63, 54, 9, \
                        394, 38, 10, \
                        338, 13, 11, \
                        64, 14, 12, \
                        65, 43, 13, \
                        66, 1, 14, \
                        67, 4, 15, \
                        340, 20, 16, \
                        73, 8, 17, \
                        346, 57, 18, \
                        563, 21, 19, \
                        76, 39, 20)

        e = self.team_finder(team_h)
        self.standings_extractor(e)
        f = self.team_finder(team_a)
        self.standings_extractor(f)
        return

    def team_finder(self, tf):
        self.tf = tf
        logging.info('game_decisions.team_finder() - init ', self.tf )
        for tx in range (0, 59, 3):    # 20 teams x 3 tuplr elements per team
            #print ("Team: ", teamid_xlt[tx], " - Code: ", teamid_xlt[tx+2])
            if self.teamid_xlt[tx+2] == self.tf:
                a = self.teamid_xlt[tx]
                b = self.teamid_xlt[tx+1]
                return a    # football-data_teamID, EPL_teamID
            else:
                pass    # keep looking for this team in tuple

        return

    def standings_extractor(self, ts):
        self.ts = ts
        logging.info('game_decisions.standings_extractor() - init ', self.ts )
        standings = []
        standings = fpl_bootstrap.standings_t       # load latest league standings
        standings_table = standings['table']    # a single JSON []array with all 20 teams
        for pos in range (0, 20):
            stp = standings_table[pos]          # array indexed by INT numerical section (0...20), not a named key
            stp_team = stp['team']['name']      # sub array with 3 data members (id, name, crestUrl)
            stp_teamid = stp['team']['id']
            stp_pg = stp['playedGames']         # number of games played
            stp_w = stp['won']
            stp_d = stp['draw']
            stp_l = stp['lost']
            stp_pts = stp['points']
            stp_gf = stp['goalsFor']
            stp_ga = stp['goalsAgainst']
            stp_gd = stp['goalDifference']
            if stp_teamid == ts:
                #if teamid_xlt[tx+2] == team_h:
                #home_team = teamid_xlt[tx]
                print ( "Team: ", self.epl_team_names[self.ts], end="" )    # use EPL bootstrap team NAMES
                print ( "GF: ", stp_gf)
                print ( "GA: ", stp_ga)
                print ( "GD: ", stp_gd)
            else:
                pass

            #game_delta = pos - pos
            #gd_delta = stp_gd - stp_gd
            #best_game = game_delta*gd_delta
            #print ( "POS: ", pos+1, " ", stp_team, "API ID: ", stp_teamid, "Points: ", stp_pts, "Games played: ", stp_pg, "Goal Diff: ", stp_gd)
        return
