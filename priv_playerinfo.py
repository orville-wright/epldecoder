#!/usr/bin/python3
import requests
from requests import Request, Session
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
import json
import logging

########################################

FPL_API_URL = "https://fantasy.premierleague.com/api/"
BST = "bootstrap/"
BSS = "bootstrap-static/"
BSD = "bootstrap-dynamic/"
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
#
class priv_playerinfo:
    """Class to access all the private data about a player and his squad picks"""
    """Requires username/password for the player being evaluated"""
    """Defaults to current gameweek"""

    username = ""
    password = ""
    auth_status = ""
    api_get_status = ""
    bst_inst = ""

    def __init__(self, playeridnum, username, password, bootstrap, playerentry):
        self.playeridnum = str(playeridnum)
        self.username = str(username)
        self.password = str(password)
        self.bst_inst = bootstrap
        self.entrydb = playerentry
        priv_playerinfo.username = self.username
        priv_playerinfo.password = self.password
        priv_playerinfo.bst_inst = self.bst_inst

        logging.info('priv_playerinfo:: init class instance for player: %s' % self.playeridnum )
        pp_req = requests.Session()

        # WARNING: This cookie is critical (must be set)
        # It must be updated each year at the start of the season as it is changed each year.
        # TODO: I need to find a smart way to do this systematically in the code (currently manual hard-coded each year)
        #pp_req.cookies.update({'pl_profile': 'eyJzIjogIld6VXNNalUyTkRBM01USmQ6MWZpdE1COjZsNkJ4bngwaGNUQjFwa3hMMnhvN2h0OGJZTSIsICJ1IjogeyJsbiI6ICJBbHBoYSIsICJmYyI6IDM5LCAiaWQiOiAyNTY0MDcxMiwgImZuIjogIkRyb2lkIn19'})

        # cookie hack
        # until I can figurre out how pl_profile cookie is programatically set
        # VERY manual & only works for playe ID's predefined here...
        pl_profile_cookies = { \

                '1212166': 'eyJzIjogIld6VXNNalUyTkRBM01USmQ6MWZpdE1COjZsNkJ4bngwaGNUQjFwa3hMMnhvN2h0OGJZTSIsICJ1IjogeyJsbiI6ICJBbHBoYSIsICJmYyI6IDM5LCAiaWQiOiAyNTY0MDcxMiwgImZuIjogIkRyb2lkIn19', \
                '1995215': 'eyJzIjogIld6SXNNalUyTkRBM01USmQ6MWh5aE9BOmdLcXg0S3RkSGR5UVRXRjUwVjhxZHR4RVNTayIsICJ1IjogeyJpZCI6IDI1NjQwNzEyLCAiZm4iOiAiRHJvaWQiLCAibG4iOiAiQWxwaGEiLCAiZmMiOiA1N319', \
                '1994221': 'eyJzIjogIld6SXNOVGc0T0RnM05WMDoxaHlpdU46MlhhRDZlbkx3YU03WFdtb0tBWEhsYXlESlBnIiwgInUiOiB7ImlkIjogNTg4ODg3NSwgImZuIjogIkRhdmlkIiwgImxuIjogIkJyYWNlIiwgImZjIjogOH19', \
                '1136396': 'eyJzIjogIld6VXNOVGc0T0RnM05WMDoxZnYzYWo6WGkxd1lMMnpLeW1pbThFTTVFeGEzVFdUaWtBIiwgInUiOiB7ImxuIjogIkJyYWNlIiwgImZjIjogOCwgImlkIjogNTg4ODg3NSwgImZuIjogIkRhdmlkIn19' }

        user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0'}
        API_URL0 = 'https://fantasy.premierleague.com/a/login/'
        API_URL1 = FPL_API_URL + MYTEAM + self.playeridnum + '/'

        # 1st get authenticates, but must use critical cookie (i.e. "pl_profile")
        # 2nd get does the data extraction if auth succeeds

        for pl, cookie_hack in pl_profile_cookies.items():
            if pl == self.playeridnum:
                pp_req.cookies.update({'pl_profile': cookie_hack})
                logging.info('priv_playerinfo:: SET pl_profile cookie for userid: %s' % pl )
                logging.info('priv_playerinfo:: SET pl_profile cookie to: %s' % cookie_hack )
                priv_playerinfo.api_get_status = "GOODCOOKIE"
                break    # found this players cookie
            else:
                logging.info('priv_playerinfo:: ERR userid is bad. No cookie found/set: %s' % pl )
                priv_playerinfo.api_get_status = "FAILED"
            # return    #return    # bad style. Need to return useful ERROR code
                      # but global class var is allways set & testable

        if priv_playerinfo.api_get_status == "FAILED":
            return
        else:
            pass
        # only continue down here if the cookie hack sucessfully executed...
        # otherwise, all data extraction will fail.
        rx0 = pp_req.get( API_URL0, headers=user_agent, auth=HTTPBasicAuth(self.username, self.password) )
        rx0_auth_cookie = requests.utils.dict_from_cookiejar(pp_req.cookies)
        logging.info('priv_playerinfo:: AUTH login resp cookie: %s' % rx0_auth_cookie['pl_profile'] )

        rx1 = pp_req.get( API_URL1, headers=user_agent, auth=HTTPDigestAuth(self.username, self.password) )
        self.auth_status = rx0.status_code
        self.gotdata_status = rx1.status_code
        logging.info('priv_playerinfo:: init AUTH url   : %s' % rx0.url )
        logging.info('priv_playerinfo:: init API GET url: %s' % rx1.url )
        logging.info('priv_playerinfo:: init login AUTH resp: %s' % self.auth_status )
        logging.info('priv_playerinfo:: init API GET resp   : %s' % self.gotdata_status )

        if rx0.status_code != 200:    # failed to authenticate
            cookie_debug_rx0 = requests.utils.dict_from_cookiejar(pp_req.cookies)
            logging.info('priv_playerinfo:: init ERROR login AUTH failed resp: %s' % self.auth_status )
            logging.info('priv_playerinfo:: init ERROR resp cookies: %s' % cookie_debug_rx0 )
            priv_playerinfo.auth_status = "FAILED"
            return

        if rx1.status_code != 200:    # API get failed
            cookie_debug_rx1 = requests.utils.dict_from_cookiejar(pp_req.cookies)
            logging.info('priv_playerinfo:: init ERROR API GET failed resp: %s' % self.gotdata_status )
            logging.info('priv_playerinfo:: init ERROR resp cookies: %s' % cookie_debug_rx1 )
            priv_playerinfo.api_get_status = "FAILED"
            return
        else:
            logging.info('priv_playerinfo:: AUTH web login resp status: %s' % self.auth_status )
            logging.info('priv_playerinfo:: GET data read resp status : %s' % self.gotdata_status )
            priv_playerinfo.auth_status = self.auth_status
            priv_playerinfo.auth_status = self.gotdata_status

            t0 = json.loads(rx1.text)       # load the data from rx1
            self.picks = t0['picks']        # contains 15 sub-elements of all 15 players in your current squad
                                            # no real human readable data. All refs to data in other structures
            self.chips = t0['chips']
            self.transfers = t0['transfers']    # data-set of some transfer info

# depricated in 2019/2020 season
#            self.chips = t0['chips']
#            self.entry = t0['entry']        # Full public ENTRY data-set
#            self.leagues = t0['leagues']    # data-set of all my classic leagues
#            self.picks = t0['picks']        # contains 15 sub-elements of all 15 players in your current squad
#                                            # no real human readable data. All refs to data in other structures

            priv_playerinfo.api_get_status = "SUCCESS"
        return

    def my_stats(self):
        """get some basic points & stats info about my team"""

        logging.info( "priv_playerinfo:: my_stats()" )
        #print ( "Team name: %s" % self.entry['name'] )
        print ("My overall points: %s" % self.entrydb.my_overall_points() )
        print ("Points in last game: %s" % self.entrydb.my_event_points() )
        return

    def mysquad_insertdb(self):
        """Extract squad data about my team"""
        ''"squad data is not accessible from base ENTRY structure (which doesn't require auth to access)"""
        """squad data is constrained/contextualized to an event week. Can only be accessed in that form"""

        logging.info( "priv_playerinfo:: mysquad_insertdb()" )
        mclient = MongoClient("mongodb://admin:sanfran1@localhost/admin")
        db = mclient.test1
        print ("Extracting my squad player/position details: ", end="")

        squad = []
        for sp in range (0, 15):              # note: squad_player hard-coded to 14 players per team
            print (sp, end="")
            print (".", end="" )
            squad = self.picks[sp]            # access data heirachery of my squad list of players
            dbcol = db.eplmysquad_ML          # should drop collection before inserting ensuring only 1 set of data is present
                                              # eplmysquad_ML - holds only specific data for Analytics & reporting across multiple teams

            if squad['is_captain'] is True:
               player_type = "Captain"
            elif squad['is_vice_captain'] is True:
               player_type = "Vice captain"
#            elif squad['is_sub'] is True:
#                player_type = "Sub"
            else:
               player_type = "Regular player"
               result = dbcol.insert({ "Team": self.entry['name'], "week": self.entry['current_event'], "Player": squad['element'], "Position": squad['position'], "Player_type": player_type, "Price": squad['selling_price'] })
            #print (".", end="" )
        return

    def list_mysquad(self):
        """Print details about the players in my current squad"""
        # self.bst_inst = bootstrap              # insert core bootstrap database instance ref into parent class attributre
        # priv_bootstrap = self.bst_inst

        logging.info('priv_playerinfo:: list_mysquad() - Analyzing captain for team %s' % self.playeridnum )
        squad = []                            # temp working []
        for sp in range (0, 15):              # note: squad_player hard-coded to 14 players per team
            print ("Squad member:", sp+1, end="")
            print ("...", end="" )

            squad = self.picks[sp]            # access data heirachery of my squad list of players
            if squad['is_captain'] is True:
               player_type = "Captain"
            elif squad['is_vice_captain'] is True:
               player_type = "Vice captain"
#            elif squad['is_sub'] is True:    # seems to have been removed in 2019/2020 season
#                player_type = "Sub"
            else:
               player_type = "Regular player"

            find_me = squad['element']
            player_name = self.bst_inst.whois_element(find_me)            # global handle set once @ start
            self.gw_points = self.bst_inst.element_gw_points(find_me)
            print ( player_name, "(", end="" )
            print ( squad['element'], end="" )
            print ( ")" \
                    # " - @ pos:", squad['position'], \
                    "-", player_type, \
                    "$:", squad['selling_price']/10, \
                    "- points (", end="" )
            print ( self.gw_points, end="" )
            print ( ")" )
        return

    def get_oneplayer(self, player_num):    # 0...15 are only valid squad member positions
        """Pull out of my squad a single player. From a specific squad psotion"""

        sp = int(player_num)
        squad = []
        squad = self.picks[sp]            # access data heirachery of my squad list of players
        if squad['is_captain'] is True:
           player_type = "Captain"
        elif squad['is_vice_captain'] is True:
           player_type = "Vice captain"
#        elif squad['is_sub'] is True:
#            player_type = "Sub"
        else:
           player_type = "Regular player"

        find_me = squad['element']
        player_name = self.bst_inst.whois_element(find_me)            # global handle set once @ start
        self.gw_points = self.bst_inst.element_gw_points(find_me)
        print ( player_name, "(", end="" )
        print ( squad['element'], end="" )
        print ( ")" \
                # " - @ pos:", squad['position'], \
                "-", player_type, \
                # "$:", squad['selling_price']/10, \
                "- points (", end="" )
        print ( self.gw_points, end="" )
        print ( ")" )
        return int(find_me)    # this players payer_id number

    def capt_anlytx(self):
        """examine an oponents team and figure out if he has the same captain as you"""
        logging.info('priv_playerinfo:: capt_anlytx() - Analyzing captain for team %s' % self.playeridnum )

        capt_list = []
        #print ("Scanning my squad members:", end="")
        for ca in range (0, 15):
            #print (".", end="" )
            capt_list = self.picks[ca]
            if capt_list['is_captain'] is True:
                find_me = capt_list['element']
                player_name = self.bst_inst.whois_element(find_me)
                print ( "My captain is: (", end="" )
                print ( capt_list['element'], end="")
                print ( ") -", player_name )
                logging.info('priv_playerinfo.capt_anlytx() - quick exit after %s loops' % ca )
                return    # as soon as you find your captain, exit since there can only be 1

        return
