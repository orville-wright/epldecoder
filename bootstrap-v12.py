#!/usr/bin/python3
import requests
from requests import Request, Session
import json
import sys
import unicodedata
import logging
import argparse
from random import randint
from pymongo import MongoClient
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
from six import iteritems
from six import itervalues

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

# warning: 
# code is now written for Python3
# and is 100% object/method
#
############################################
# API calls agaist the bootstrap url (..premierleague.com/drf/...) dont require any authentication, for any valid player id
# but, if you want explict details about a players team, then you must authenticate as that user
# for all remaining API calls (..premierleague.com/drf/...)
#
# Known API functions
#
# League standings:
# 'https://fantasy.premierleague.com/drf/leagues-classic-standings/<player-id>?phase=1&le-page=1&ls-page=1'
#
# Player detailed stats:
# https://fantasy.premierleague.com/drf/element-summary/<player-number>
#
# User base account info:
# https://fantasy.premierleague.com/drf/my-team/<player-id>
#
# https://fantasy.premierleague.com/drf/bootstrap
# https://fantasy.premierleague.com/drf/bootstrap-static
# https://fantasy.premierleague.com/drf/bootstrap-dynamic
#
# https://fantasy.premierleague.com/drf/entry/1980723
# https://fantasy.premierleague.com/drf/event/23/live
# https://fantasy.premierleague.com/drf/entry/1980723/event/23/picks

############################################
# todo: add a method that access the core BOOTSTRAP data set
#       for this player/team.
# note: Must be authourized by credentials
#
class fpl_bootstrap:
    """Base class for extracting the core game ENTRY dataset"""
    """This class requires valid credentials"""
    """but does not contain the full player private ENTRY dataset"""
    username = ""
    password = ""
    current_event = ""

    def __init__(self, playeridnum, username, password):
        self.playeridnum = str(playeridnum)
        self.username = username
        self.password = password
        fpl_bootstrap.username = username    # make USERNAME var global to class instance
        fpl_bootstrap.password = password    # make PASSWORD var global to class instance

        logging.info('fpl_bootstrap:: - create bootstrap ENTRY class instance for player: %s' % self.playeridnum )

        self.epl_team_names = {}    # global dict accessible from wihtin this base class
        s = requests.Session()

        # WARNING: This cookie must be updated each year at the start of the season as it is changed each year.
        #s.cookies.update({'pl_profile': 'eyJzIjogIld6VXNNalUyTkRBM01USmQ6MWZpdE1COjZsNkJ4bngwaGNUQjFwa3hMMnhvN2h0OGJZTSIsICJ1IjogeyJsbiI6ICJBbHBoYSIsICJmYyI6IDM5LCAiaWQiOiAyNTY0MDcxMiwgImZuIjogIkRyb2lkIn19'})
        s.cookies.update({'pl_profile': 'eyJzIjogIld6VXNNalUyTkRBM01USmQ6MWVOWUo4OjE1QWNaRW5EYlIwM2I4bk1HZDBqX3Z5VVk2WSIsICJ1IjogeyJsbiI6ICJBbHBoYSIsICJmYyI6IDgsICJpZCI6IDI1NjQwNzEyLCAiZm4iOiAiRHJvaWQifX0='})

        user_agent = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5;Windows NT)'}
        API_URL0 = 'https://fantasy.premierleague.com/a/login'
        API_URL1 = FPL_API_URL + BST

        # 1st get authenticates, but must use critical cookie (i.e. "pl_profile")
        # 2nd get does the data extraction if auth succeeds

        rx0 = s.get( API_URL0, headers=user_agent, auth=HTTPBasicAuth(self.username, self.password) )
        rx1 = s.get( API_URL1, headers=user_agent, auth=HTTPDigestAuth(self.username, self.password) )
        self.auth_status = rx0.status_code
        self.gotdata_status = rx1.status_code
        logging.info('fpl_bootstrap:: - init - Logon AUTH url: %s' % rx0.url )
        logging.info('fpl_bootstrat:: - init - API data get url: %s' % rx1.url )

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
            #
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

#current-event



    def upcomming_fixtures(self):
        """the bootstrap database holds a list of the next 10 gameweek fixtures"""
        """its just a quick way to  what fixtures are approaching in the near future"""

        logging.info('fpl_bootstrap: :upcomming_fixtures()...' )
        tn_idx = fpl_bootstrap.list_epl_teams(self)
        print ( "Next 10 fixtures..." )
        for fixture in self.next_event_fixtures:
            idx_h = int(fixture['team_h'])    # use INT to index into the team-name dict self.t that was populated in list_epl_teams()
            idx_a = int(fixture['team_a'])    # use INT to index into the team-name dict self.t that was populated in list_epl_teams()
            print ( "Game week:", fixture['event'], "Game day:", fixture['event_day'], "(", fixture['kickoff_time_formatted'], ") Teams - HOME:", self.epl_team_names[idx_h], "vs.", self.epl_team_names[idx_a], "AWAY" )
            #print ( "Home team:", self.t[idx_h] )
            #print ( "Away team:", self.t[idx_a] )
        return


    def list_epl_teams(self):
        """populate a small dict that holds epl team ID and real names"""
        """this dict is accessible via the base class fpl_bootstrap"""

        logging.info('fpl_bootstrap:: list_epl_teams()...setup a dict of team IDs + NAMES for easy reference' )
        for team_name in self.teams:
            #print ( "Team:", team_name['id'], team_name['short_name'], team_name['name'] )
            self.epl_team_names[team_name['id']] = team_name['name']    # populate the class dict, which is accessible within the class fpl_bootstrap()
        return

############################################
# todo: add a method that prints a list of every league this player
#       is enrolled in. Since its only held in the ENTRY data struct.
#
class player_entry:
    """Base class for an OPPONENT (you/anyone) and your base EPL game ENTRY data set"""
    """This works for any valid EPL player/opponent ID in the league"""
    """but can only acesses the public data set (i.e. not current squad info)"""

    def __init__(self, playeridnum):
        self.playeridnum = str(playeridnum)
        logging.info('player_entry:: - init class instance as player: %s' % self.playeridnum )
        EXTRACT_URL = FPL_API_URL + ENTRY + self.playeridnum

        s = requests.Session()
        rx = s.get(EXTRACT_URL)    # basic non-authenticated API request on a player ENTRY
        self.player_exists = rx.status_code
        logging.info('player_entry:: - API url: %s' % rx.url )

        if rx.status_code != 200:    # failed to access public URL for player number
            logging.info('player_entry:: - ERROR GET failed for player %s' % self.playeridnum )
            logging.info('player_entry:: - ERROR GET response code is %s' % self.player_exists )
            return
        else:
            # create JSON dict with players ENTRY data, plus other data thats now available
            logging.info('player_entry:: - init API GET response code was %s' % self.player_exists )
            s2 = json.loads(rx.text)
            self.entry = s2['entry']
            self.leagues = s2['leagues']
            self.cleagues = self.leagues['classic']
            self.h2hleagues = self.leagues['h2h']
            self.cupleagues = self.leagues['cup']
            self.current_event = self.entry['current_event']
        return

    def my_name(self):
        """Get the real human readable first/last name of this person"""
        """Based on the EPL game ENTRY ID number"""

        logging.info('player_entry:: my_name() - Init method' )
        #print ( self.entry['player_first_name'], self.entry['player_last_name'], end="" )
        return self.entry['player_first_name'] + " " + self.entry['player_last_name']

    def my_id(self):
        """Get the EPL game ENTRY ID of me"""

        logging.info( 'player_entry:: my_id() - Init method' )
        #print ( self.entry['id'], end="" )
        return  self.entry['id']

    def my_teamname(self):
        """Get the name of my team"""

        logging.info( 'player_entry:: my_teamname() - Init method' )
        #print ( self.entry['name'], end="" )
        return self.entry['name']

    def my_entry_cleagues(self):    # list of all CLASSIC leagues player is entered in
        """Cycle thru all my Classic Leagues & print them"""
        """This will not access/print GLOBAL leagues (e.g. EPL Team leagues, Country leagues etc)"""

        logging.info('player_entry:: my_entry_cleagues(): - Init method. scan league: %s' % this_league )
        #print ( "Team name: %s" % self.entry['name'] )
        #print (self.entry['name'], "plays in %s leagues" % len(self.cleagues))
        p = 1
        for v in self.cleagues:
            print ("", p, "League ID: %s %s - I am ranked: %s" % (v['id'], v['name'], v['entry_rank']))
            p += 1
        return

    def entry_insertdb(self):
        """Insert game player ENTRY data into MongoDB"""

        logging.info( 'player_entry:: entry_insertdb(): - Init method. MongoDB col insert: eplentry' )
        mclient = MongoClient("mongodb://admin:sanfran1@localhost/admin")
        db = mclient.test1
        col = db.eplentry    # mongoDB collection

        self.entry['kit'] = 'DATA_SANITIZED'           # delete kit element. its a messy uneeded embeded compound sub-doc data set
        r = col.insert( { 'entry': self.entry } )      # insert ENTRY record into DB in 1 operation. (a compound doc)

        # todo: restructure this insert into a nice vanilla row (not a compound doc)
        # now load the DB with this teams squad details...
        # which can only be done if we know what EVENT week ID we are currently in

        #opponent_id = self.entry['id']
        #event_id = self.entry['current_event']
        print (" ")

        return

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

    def __init__(self, playeridnum, username, password):
        self.playeridnum = str(playeridnum)
        self.username = str(username)
        self.password = str(password)
        priv_playerinfo.username = self.username
        priv_playerinfo.password = self.password

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
                '1136396': 'eyJzIjogIld6VXNOVGc0T0RnM05WMDoxZnYzYWo6WGkxd1lMMnpLeW1pbThFTTVFeGEzVFdUaWtBIiwgInUiOiB7ImxuIjogIkJyYWNlIiwgImZjIjogOCwgImlkIjogNTg4ODg3NSwgImZuIjogIkRhdmlkIn19' }

        user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0'}
        API_URL0 = 'https://fantasy.premierleague.com/a/login'
        API_URL1 = FPL_API_URL + MYTEAM + self.playeridnum

        # 1st get authenticates, but must use critical cookie (i.e. "pl_profile")
        # 2nd get does the data extraction if auth succeeds

        for pl, cookie_hack in pl_profile_cookies.items():
            if pl == self.playeridnum:
                pp_req.cookies.update({'pl_profile': cookie_hack})
                logging.info('priv_playerinfo:: SET pl_profile cookie to: %s' % cookie_hack )
        
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
            self.chips = t0['chips']
            self.entry = t0['entry']        # Full public ENTRY data-set
            self.leagues = t0['leagues']    # data-set of all my classic leagues 
            self.picks = t0['picks']        # contains 15 sub-elements of all 15 players in your current squad
                                            # no real human readable data. All refs to data in other structures
        return

    def my_stats(self):
        """get some basic points & stats info about my team"""

        logging.info( "priv_playerinfo:: my_stats()" )
        #print ( "Team name: %s" % self.entry['name'] )
        print ("My overall points: %s" % self.entry['summary_overall_points'])
        print ("Points in last game: %s" % self.entry['summary_event_points'])
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
            elif squad['is_sub'] is True:
                player_type = "Sub"
            else:
               player_type = "Regular player"
               result = dbcol.insert({ "Team": self.entry['name'], "week": self.entry['current_event'], "Player": squad['element'], "Position": squad['position'], "Player_type": player_type, "Price": squad['selling_price'] })
            #print (".", end="" )
        return

    def list_mysquad(self):
        """Print details about the players in my current squad"""

        logging.info('priv_playerinfo:: list_mysquad() - Analyzing captain for team %s' % self.playeridnum )
        squad = []                            # temp working []
        for sp in range (0, 15):              # note: squad_player hard-coded to 14 players per team
            print ("\tSquad member:", sp+1, end="")
            print ("...", end="" )

            squad = self.picks[sp]            # access data heirachery of my squad list of players
            if squad['is_captain'] is True:
               player_type = "Captain"
            elif squad['is_vice_captain'] is True:
               player_type = "Vice captain"
            elif squad['is_sub'] is True:
                player_type = "Sub"
            else:
               player_type = "Regular player"

            find_me = squad['element']
            player_name = bootstrap.whois_element(find_me)            # global handle set once @ start
            self.gw_points = bootstrap.element_gw_points(find_me)
            print ( player_name, "(", end="" )
            print ( squad['element'], end="" )
            print ( ") - @ pos:", squad['position'], \
                    "-", player_type, \
                    "$:", squad['selling_price']/10, \
                    "- points (", end="" )
            print ( self.gw_points, end="" )
            print ( ")" )
        return

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
                player_name = bootstrap.whois_element(find_me)
                print ( "My captain is:", capt_list['element'], player_name )
                logging.info('priv_playerinfo:: capt_anlytx() - quick exit after %s loops' % ca )
                return    # as soon as you find your captain, exit since there can only be 1

        return

########################################################
# This is not a CLASS yet
#
# API request of detailed player team info, stats & data
# requires username/password authentication for API access to player dataset
# The JSON dataset can also be...
#     - inserted into the MongoDB collection
#     - Printed in a nice human readable non-JSON format
#
# SHould be easy to convert to a CLASS, as it only takes playerid as input data
#
# I think this can be deleted?

def fpl_myteam_get(player_idnum):
    # API calls agaist the bootstrap url (..premierleague.com/drf/...) dont require any authentication, for any valid player id
    # but, if you want explict private details about a team, then you must authenticate for your (..premierleague.com/drf/...) API calls

    PLAYER_ENTRY = str(player_idnum)
    logging.info('fpl_myteam_get(): Authenticated get for player: %s' % PLAYER_ENTRY )

    s1 = requests.Session()
    s1.cookies.update({'pl_profile': 'eyJzIjogIld6VXNNalUyTkRBM01USmQ6MWVOWUo4OjE1QWNaRW5EYlIwM2I4bk1HZDBqX3Z5VVk2WSIsICJ1IjogeyJsbiI6ICJBbHBoYSIsICJmYyI6IDgsICJpZCI6IDI1NjQwNzEyLCAiZm4iOiAiRHJvaWQifX0='})

    user_agent = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5;Windows NT)'}
    EXTRACT_URL = FPL_API_URL + MYTEAM + PLAYER_ENTRY

    # 1st get does the authentication, but must use the critical cookie (i.e. "pl_profile")
    # 2nd get does the real data extraction

    resp0 = s1.get('https://fantasy.premierleague.com/a/login', headers=user_agent, auth=HTTPBasicAuth(priv_playerinfo.username, priv_playerinfo.password))
    resp1 = s1.get(EXTRACT_URL, headers=user_agent, auth=HTTPDigestAuth(priv_playerinfo.username, priv_playerinfo.password))

    print (" ")
    print ("fpl_myteam_get(): Authenticating API...", end="")
    if resp0.status_code == 200:
        print ("Succeeded as player:", PLAYER_ENTRY)
        #print ("API URL:", resp0.request.url)
    else:
        print ("Failed for player:", PLAYER_ENTRY)
        print ("###################### resp0 ########################################")
        logging.info('### fpl_myteam_get(): URL GET url: %s' % resp0.url )
        logging.info('### fpl_myteam_get(): URL GET history: %s' % resp0.history )
        logging.info('### fpl_myteam_get(): Status_code: %s' % resp0.status_code )
        #logging.info('### fpl_myteam_get(): resp-headers: %s' % resp0.headers )
        logging.info('### fpl_myteam_get(): req-headers: %s' % resp0.request.headers )
        print ("#####################################################################")

    if resp1.status_code == 200:
        if args['bool_dbload'] is True:
            logging.info('fpl_myteam_get(): mongoDB col inserts: eplmysquad, eplmysquad_ML')
            print ("Team data successfully extracted")
            print ("API URL:", resp1.request.url)

            t0 = json.loads(resp1.text)
            t1 = t0['chips']
            t2 = t0['entry']
            t3 = t0['leagues']
            t4 = t0['picks']    # this section contains 15 sub-elements of all 15 players selected in your current squad
                                # but there is no nice human readable data. its All references to data in other collections

            print (" ")
            print ("My team name is: %s" % t2['name'])
            print ("My overall points: %s" % t2['summary_overall_points'])
            print ("Points in last game: %s" % t2['summary_event_points'])
            print (" ")

            mclient = MongoClient("mongodb://admin:sanfran1@localhost/admin")
            db = mclient.test1
            #col_1 = db.eplmysquad_RAW                            # eplmysquad - holds ALL data extracted from API call for my-team only
            print ("Extracting my squad player/position details: ", end="")
            t7 = []

            for player_num in range (0, 15):                     # note: hard-coded 14 players in a team
                #result = col_1.insert({ 'player_id': player_num, 'player_stats': t4[player_num] })    # inserts entire enbeded element in 1 inset
                print (player_num, end="")                       # python3 formatted
                print (".", end="" )

                t7 = t4[player_num]
                col_2 = db.eplmysquad_ML    # should drop collection before inserting ensuring only 1 set of data is present
                                            # eplmysquad_ML - holds only specific data for doing Analytics & reporting across multiple teams

                if t7['is_captain'] is True:
                   player_type = "Captain"
                elif t7['is_vice_captain'] is True:
                   player_type = "Vice captain"
                elif t7['is_sub'] is True:
                    player_type = "Sub"
                else:
                   player_type = "Regular player"

                result = col_2.insert({ "Team": t2['name'], "week": t2['current_event'], "Player": t7['element'], "Position": t7['position'], "Player_type": player_type, "Price": t7['selling_price'] }) 

                print (".", end="" )

        else:
            print ("fpl_myteam_get(): no DB insert requested")

    else:
        print ("fpl_myteam_get(): Extraction of team data failed")
        print ("################# resp1 error dump ##################################")
        logging.info('### fpl_myteam_get(): URL GET url: %s' % resp1.url )
        logging.info('### fpl_myteam_get(): URL GET history: %s' % resp1.history )
        logging.info('### fpl_myteam_get(): Status_code: %s' % resp1.status_code )
        if args['bool_xray'] is True:
            logging.info('### fpl_myteam_get(): resp-headers: %s' % resp1.headers )
            logging.info('### fpl_myteam_get(): req-headers: %s' % resp1.request.headers )
        else:
            logging.info('### fpl_myteam_get(): text: %s' % resp1.text )
        print ("#####################################################################")

    if args['bool_dbload'] is True:
       print (" ")

    # XRAY option doe degug/tetsing 
    # activated by -x arg
    if args['bool_xray'] is True:
        logging.info('fpl_myteam_get(): dump squad JSON data') 
        print ("My current squad looks like this...")
        for player_num in range (0, 15):
            #for stat, data in t4[player_num].iteritems():
            # for (key, value) in iteritems(heights):
            for (stat, data) in iteritems(t4[player_num]):
                print ("Player:", player_num, stat, ":", data)
    else:
        logging.info('fpl_myteam_get(): NO xray requested')

    return

####
# Get the full squad player/position list for any team
#
# This function extracts team data from a strict API URL
# eg:  https://fantasy.premierleague.com/a/team/1980723/event/23
#      not the public ENTRY data set (squad data is not in that data set) 

# WARNINGS:
# 1. could be Network/API expensive if called recurrsively on multiple players/oponents
# 2. Currently considers "you" as an opponent
#    (i.e no checks to exclude "you". need smarter way to know this) 
# 
class get_opponents_squad:
    """Base class to access any player/opponent team sqaud list & data """
    """note: can only access historical squad data from last game back (which is public data) """
    """must be called with a sucessfully populated instance of Player_ENTRY() """

    def __init__(self, player_idnum, pe_live_inst, event_id):
        # Base bootstrap API calls (..premierleague.com/drf/...) dont require authentication
        # but, if you want explict details about a team, you must authenticate your API call

        PLAYER_ENTRY = str(player_idnum)
        self.pe_live_inst = pe_live_inst              # player ENTRY instance for this player - critical for de-ref'ing data
        self.username = priv_playerinfo.username      # username from glocal class var
        self.password = priv_playerinfo.password      # password from global class var

        logging.info('get_opponents_squad(): - Inst class. Auth API get priv player data for: %s' % PLAYER_ENTRY )
        s1 = requests.Session()

        # this will fail
        # need to add cookie hack
        s1.cookies.update({'pl_profile': 'eyJzIjogIld6VXNNalUyTkRBM01USmQ6MWVOWUo4OjE1QWNaRW5EYlIwM2I4bk1HZDBqX3Z5VVk2WSIsICJ1IjogeyJsbiI6ICJBbHBoYSIsICJmYyI6IDgsICJpZCI6IDI1NjQwNzEyLCAiZm4iOiAiRHJvaWQifX0='})

        user_agent = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5;Windows NT)'}

        # https://fantasy.premierleague.com/drf/entry/0123456/event/01/picks
        EXTRACT_URL = FPL_API_URL + ENTRY + PLAYER_ENTRY + "/event/" + str(event_id) + "/picks"

        # 1st get does the authentication, but must use the critical cookie (i.e. "pl_profile")
        # 2nd get does the real data extraction
        resp3 = s1.get('https://fantasy.premierleague.com/a/login', headers=user_agent, auth=HTTPBasicAuth(self.username, self.password))
        resp4 = s1.get(EXTRACT_URL, headers=user_agent, auth=HTTPDigestAuth(self.username, self.password))

        self.auth_status = resp3.status_code                   # class gloabl var
        self.gotdata_status = resp4.status_code                # class global var

        if resp3.status_code == 200:                           # initial username/password AUTH
            logging.info('get_opponents_squad(): - Inst class. Auth succeess for target player: %s' % PLAYER_ENTRY )
            logging.info('get_opponents_squad(): - Inst class. get URL: %s' % EXTRACT_URL )
        else:
            print ("Auth failed for player:", PLAYER_ENTRY)
            print ("###################### resp0 ########################################")
            logging.info('### get_opponents_squad(): URL GET url: %s' % resp3.url )
            logging.info('### get_opponents_squad(): URL GET history: %s' % resp3.history )
            logging.info('### get_opponents_squad(): Status_code: %s' % resp3.status_code )
            logging.info('### get_opponents_squad(): resp-headers: %s' % resp3.headers )
            logging.info('### get_opponents_squad(): req-headers: %s' % resp3.request.headers )
            print ("#####################################################################")
            return

        self.t0 = json.loads(resp4.text)
        self.t4 = self.t0['automatic_subs']
        self.t1 = self.t0['entry_history']
        self.t2 = self.t0['event']
        self.t3 = self.t0['picks']    # [] has 15 sub-elements of all 15 players in your current squad
                                      # but no nice human readable data. its All refs to data in other []
        return                        # instantiation done & succeded

    def opp_squad_dbload(self):
        """ load some of an opponents squad data into a MongoDB """

        if self.gotdata_status == 200:                          # read of data set
            logging.info('get_opponents_squad():: opp_squad_dbload() - Squad data sucessfull extracted')
            logging.info('get_opponents_squad():: opp_squad_dbload() - API URL: %s' % resp4.request.url)

            logging.info('get_opponents_squad():: opp_squad_dbload() - mongoDB col inserts: eplopsquad_ML')
            mclient = MongoClient("mongodb://admin:sanfran1@localhost/admin")
            db = mclient.test1
            col_2 = db.eplopsquad_ML
            print ("Insert week", str(event_id), "squad player/position data for oponent:", PLAYER_ENTRY)
            t7 = []                                         # temp [] for scaning each players data
            print ("Squad member: ", end="")
            for player_num in range (0, 15):                # note: hard-coded 14 players in a team
                print (player_num, end="")                  # python3 formatted
                print (".", end="" )
                t7 = self.t3[player_num]                    # temp [] dict to scan squad players

                if t7['is_captain'] is True:                # setting player type in prep for MongoDB inserts
                   player_type = "Captain"
                elif t7['is_vice_captain'] is True:
                   player_type = "Vice captain"
                else:
                   player_type = "Regular player"

                #print ("get_opponents_squad(): Team:", t1['entry'], "Week:", \
                #        t2['id'], "Player:", t7['element'], "Position:", \
                #        t7['position'], "Player_type:", player_type)

                result = col_2.insert({ "Team": t1['entry'], \
                        "week": t2['id'], \
                        "Player": t7['element'], \
                        "Position": t7['position'], \
                        "Player_type": player_type })
            return
        else:
            print ( "Can't insert data into MongoDB due to HTML get failure" )
        return


    def opp_squad_captain(self): 
        """extract info about the captain of this oponents squad"""

        logging.info('get_opponents_squad:: opp_squad_captain() - Enter' )
        t7 = []                                           # temp working dict to hold this users squad players
        oppt_tname = self.pe_live_inst.my_teamname()      # accessor to resolve additional ref'd player ENTRY data
        for player_num in range (0, 15):                  # note: hard-coded 14 players in a team
            t7 = self.t3[player_num]                      # scanning each squad player details (not likley to ever change)
            if t7['is_captain'] is False:
                pass
            elif t7['is_captain'] is True:                    # is this squad player the CAPTAIN?:
                find_me = t7['element']                       # get unique player ID for squad player
                capt_name = bootstrap.whois_element(find_me)  # scan main payer data set - each time (!!slow-ish ~600 entities )
                capt_gw_points = bootstrap.element_gw_points(find_me)    # raw points exlcuding bonus/multipliers/deductions
                print ( self.t1['entry'], "(", end="" )
                print ( oppt_tname, end="" )
                print ( ") - Week:", self.t2['id'], \
                        "- Captain is:", t7['element'], \
                        "@ pos:", t7['position'], \
                        "-", capt_name, end="" )
                print ( " (points:", capt_gw_points, end="" )
                print ( ")" )

                logging.info('get_opponents_squad:: opp_squad_captain() - found captain - quick exit after %s loops' % player_num )
                return                                            # exit as soon as captain is located

        print ( "Failed to locate CAPTAIN in squad", self.t1['entry'], oppt_tname )
        logging.info('get_opponents_squad:: opp_squad_captain() - Failed to locate captain with element ID: %s' % find_me )
        return

        #!! needs to be fast by re-using player_entry inst

    def opp_sq_findplayer(self, f_playerid): 
        """Scan a players ENTRY and searchs his squad for a specific player ID"""

        fp_id = int(f_playerid)                           # must use INT for tests
        oppt_tname = self.pe_live_inst.my_teamname()      # accessor to resolve additional ref'd player ENTRY data
        p_name = bootstrap.whois_element(fp_id)      # scans main data set - each time (!!slow-ish ~600 entities )
        t7 = []                                           # temp working dict to hold this users squad players
        for player_num in range (0, 15):                  # note: hard-coded 14 players in a team
            t7 = self.t3[player_num]                      # scanning each squad player details (not likley to ever change)
            if t7['element'] == fp_id:
                print ("Opponent:", self.t1['entry'], \
                        oppt_tname, \
                        "- Week:", self.t2['id'], \
                        "- HAS:", t7['element'], \
                        "**", p_name, \
                        "@ pos:", t7['position'] )
                logging.info('get_opponents_squad:: opp_sq_findplayer() - found player - quick exit after %s loops' % player_num )
                return
            else:
                #print ( ".", end="" )
                pass

        print ( "Opponent:", self.t1['entry'], \
                oppt_tname, \
                "- Week:", self.t2['id'], \
                "- not in squad:", fp_id, \
                p_name )
        return

        #!! needs to be fast by re-using player_entry inst

##########
# cycle through a list of leagues and extract the monthly standings statistics
# then insert then into the mongoDB collection

def X_my_league_stands(player_idnum, league):
    logging.info('my_league_stands(): extract standings for league: %s' % league)
    PLAYER_ENTRY = str(player_idnum)
    s1 = requests.Session()
    s1.cookies.update({'pl_profile': 'eyJzIjogIld6VXNNalUyTkRBM01USmQ6MWVOWUo4OjE1QWNaRW5EYlIwM2I4bk1HZDBqX3Z5VVk2WSIsICJ1IjogeyJsbiI6ICJBbHBoYSIsICJmYyI6IDgsICJpZCI6IDI1NjQwNzEyLCAiZm4iOiAiRHJvaWQifX0='})

    user_agent = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5;Windows NT)'}
    EXTRACT_URL = FPL_API_URL + MYTEAM + PLAYER_ENTRY

    # 1st get does the authentication, but must use the critical cookie (i.e. "pl_profile")
    # 2nd get does the real data extraction once the auth succeeds
    print ("my_league_stands(): Authenticating API to extract details of player:", PLAYER_ENTRY, "...", end="")
    resp0 = s1.get('https://fantasy.premierleague.com/a/login', headers=user_agent, auth=HTTPBasicAuth(priv_playerinfo.username, priv_playerinfo.password))
    print (resp0.status_code)

    mclient = MongoClient("mongodb://admin:sanfran1@localhost/admin")
    db = mclient.test1
    col = db.eplstand_permonth    # mongoDB collection

    print (" ")
    print ("Extract stats for all players in league:", league )           # python3 formatted

    month_code = {'1': 'Overall', '2': 'Aug', '3': 'sep', '4': 'Oct', '5': 'Nov', '6': 'Dec', '7': 'Jan', '8': 'Feb', '9': 'Mar' }

    for month in range (2, 8):           # hard coded 7 months
        # month 1=current month
        # 2=aug, 3=sept, 4=oct, 5=nov, 6=dec, 7=jan, 8=feb, 9=mar, 10=apr

        print ("\t", "Month:", month_code[str(month)], "", end="")
        # dynamically built the API url for each month
        s_month = str(month)
        LEAGUE_STATS_URL = STANDINGS_URL + league + '?phase=' + s_month + CLASSIC_PAGE

        resp2 = s1.get(LEAGUE_STATS_URL, headers=user_agent, auth=HTTPDigestAuth(priv_playerinfo.username, priv_playerinfo.password))

        # should test resp2.status_code here...
        m0 = json.loads(resp2.text)
        m1 = m0['new_entries']
        m2 = m0['league']
        m3 = m0['standings']
        m4 = m3['results']
        mcount = 0

        for results_data in m4:
            print (".", end="")
            #print ("Player:", results_data['player_name'], "Monthly rank:", results_data['rank'], "Monthly total:", results_data['total'])
            results = col.insert({ 'player_entry': results_data['entry'], 'player_name': results_data['entry_name'], 'month': month, 'league': results_data['league'], 'league_name': m2['name'], 'rank': results_data['rank'], 'month_total': results_data['total'] })
            mcount += 1
        print ("", mcount, "Players")

    return

#####
#
# inset the data: a JSON dict and its key/value pair data into a MongoDB collection
# entry:   JSON dict
#          mongodb collection name
# 
def X_dbstore_entry(m_json_dict, m_colname):
    logging.info('dbstore_enrty(): insert data into collection: %s' % m_colname )
    mclient = MongoClient("mongodb://admin:sanfran1@localhost/admin")
    db = mclient.test1
    col = db[m_colname]
    # collection = db.'m_colname'

    # cycle thought the JSON dicy key/value pairs 1-by-1 and insert them to the mongo database
    # note: there may be a smart mongo/JSON way to do this in a single operation without
    # looping though each individual dict key - (which could be slow for a very large source dict)
    #
    # note: args['bool_xray'] is a global var

    if args['bool_dbload'] is True:
        logging.info('dbstore_enrty(): cycling thru JSON dict key/values...')
        print (m_colname,)
        for key, value in m_json_dict.items():
            #print ("KEY: %s - VALUE: %s") % (key, value)
            sys.stdout.write('.')
            result = col.insert({key: value})
    else:
        logging.info('dbstore_enrty(): no DB insert requested')
    print (" ")

    # testing only
    # activated by -x arg
    if args['bool_xray'] is True:
        logging.info('dbstore_entry(): Read MongoDB collection: %s' % m_colname)
        for doc in col.find({}):
            print(doc)
    else:
        logging.info('dbstore_entry(): NO xray requested')

    return

####
# mongo query
# how to extract the players name and exclude the mono unique _id field...
#     db.eplentry.findOne( { player_last_name: {$exists: true } }, { _id: 0} )
#
# a test function
# testing that mongo is working fine...
#
# This function created 500 random entries in a mongo collection (named 'reviews') in the test1 database
# and then print out the contents of the collection directly from the database

def X_mongo_1():
    logging.info('mongo_1()' )
    mclient = MongoClient("mongodb://admin:sanfran1@localhost/admin")
    db = mclient.test1
    col = db.reviews

    names = ['Kitchen','Animal','State', 'Tastey', 'Big','City','Fish', 'Pizza','Goat', 'Salty','Sandwich','Lazy', 'Fun']
    company_type = ['LLC','Inc','Company','Corporation']
    company_cuisine = ['Pizza', 'Bar Food', 'Fast Food', 'Italian', 'Mexican', 'American', 'Sushi Bar', 'Vegetarian']

    for x in xrange(1, 501):
        #result = db.reviews.insert({
        result = col.insert({
            'name' : names[randint(0, (len(names)-1))] + ' ' + names[randint(0, (len(names)-1))]  + ' ' + company_type[randint(0, (len(company_type)-1))],
            'rating' : randint(1, 5),
            'cuisine' : company_cuisine[randint(0, (len(company_cuisine)-1))] 
            })

        #print('Created {0} of 100 as {1}'.format(x,result))
    for doc in db.reviews.find({}):
        print(doc)

    return

######################
# Class that gives better control and visibility into league details for a specific player
# This way you can have multiple instances of league data for multple players
# without needing to temporarily store the data (its addressible in each instance)
#
# note; This class does not get the base core ENTRY league details. Only the specific league
#       It extracts...
#                      1. all league details
#                      2. for specific league ID
#                      3. and a specific pagination data set within the league results
#                      4. looking into the favourite league you designated
#
#       To get all leagues that this player is enrolled in, you need to access the
#       ENTRY class, as thats the only place where that data structure exists & then
#       dig into the rewults data pages for that league
#
class league_details:
    """A base league class that extracts data from the payers PRIVATE dataset"""
    cl_op_list = {}    # class global var/dict holds a list of all oponents team ID's in this league

    def __init__(self, playeridnum, leagueidnum):
        self.playeridnum = str(playeridnum)
        self.leagueidnum = str(leagueidnum)
        logging.info('class:legue_details() - init: Playerid: %s league num: %s' % (self.playeridnum, self.leagueidnum))
        EXTRACT_URL = FPL_API_URL + LCS_SUBURL + str(leagueidnum) + '?phase=1&le-page=1&ls-page=1'
        self.t = requests.Session()
        tx = self.t.get(EXTRACT_URL)
        self.league_exists = tx.status_code
        self.cl_op_list = {}    # a dict holding a list of all oponents team ID's in this league
        

        if tx.status_code == 404:    # 404 means this league number does not exists
            logging.info('legue_details:: init -  ERROR API get failed - league %s does not exist' % leagueidnum )
        else:
            # dict popuated with extractd JSON league data from API GET
            # note: public dict shared by multiple league_details:() methods but *NOT* shared by league_details::monthly_aggr_l_standings()

            logging.info('legue_details:: - init: API URL: %s' % EXTRACT_URL )
            t2 = json.loads(tx.text)
            self.new_entries = t2['new_entries']
            self.ne_pending = self.new_entries['results']
            self.league = t2['league']
            self.standings = t2['standings']
            self.results = self.standings['results']
        return

    def my_leagueidnum(self):
        """ extract the league ID number """
        logging.info('league_details:: my_leagueidnum()' )
        print (self.league['id'])      # TODO: remove this and CHANGE to -> return(self.league['id'])
        return


    def my_leaguename(self):
        """ extract the Human readable real League Name """
        logging.info('league_details:: my_leaguename()' )
        print (self.league['name'])    # TODO: remove this and CHANGE to -> return(self.league['name'])
        return


    def whose_inmy_league(self):
        """ iterate on JSON data instance & display key info about the players in this league """
        # NOTES: this method does NOT display league results. Just opponent teams in this league
        #        at the beginning of the season this fails becasue players are held in new_entires section. NOT results section.
        # this method has the best print format
        logging.info('league_details:: whose_inmy_league()' )
        #
        # first check in new_entries[results] becasue...
        #   1. at beginning of the season, all players are temporarily held in here until the game oficially starts
        #   2. any new players joining this league during the season will also be tmeporarily held here until the next game starts
        print ("Opponents & teams in my favourite league:", self.league['name'], "(", self.league['id'], ")" )
        print ( "===================== League leaderboard ========================" )
        for value in self.results:
            print ("\tRanked:", value['rank'], \
                    "-", value['player_name'], \
                    "-", "Team ID:", value['entry'],\
                    "(", value['entry_name'], ")", \
                    "- points:", value['total'])
        return


    def monthly_aggr_l_standings(self):
        """"method to cycle through all the monthly aggregated league standings results for this player """
        mclient = MongoClient("mongodb://admin:sanfran1@localhost/admin")
        db = mclient.test1
        col = db.eplstand_permonth            # mongoDB collection
        month_code = {'1': 'Overall', '2': 'Aug', '3': 'sep', '4': 'Oct', '5': 'Nov', '6': 'Dec', '7': 'Jan', '8': 'Feb', '9': 'Mar' }
        print ("Monthly stats for teams in my fav league:", self.league['name'], "(", self.leagueidnum, ")" )

        # NOTE: at beginning of season this fails because result section does NOT exists yet
        for month in range (1, 9):            # hard coded 7 months  (note: month 1 = the current month + overall standings)
            print ( " " )                     # note: class instantiation pre-populates current month stats data (month 1)
            print ("Month:", month_code[str(month)])
            s_month = str(month)
            LS_URL = STANDINGS_URL + self.leagueidnum + '?phase=' + s_month + CLASSIC_PAGE

            rx1 = self.t.get(LS_URL)
            month_data_exists = rx1.status_code
            logging.info('method:mylegue_standings() - API get for month: %s' % s_month )
            # should test rx1.status_code here...

            logging.info('league_details:: monthly_aggr_l_standings(): URL for get: %s' % LS_URL )
            logging.info('league_details:: monthly_aggr_l_standings(): GET status: %s' % rx1.status_code )

            self.m0 = json.loads(rx1.text)
            self.new_entries = self.m0['new_entries']
            self.league = self.m0['league']
            self.standings = self.m0['standings']
            self.results = self.standings['results']

            mcount = 0
            for r in self.results:
                #print (".", end="")
                print ( "\t", "Player:", r['player_name'], "Monthly rank:", r['rank'], "Monthly total:", r['total'] )
                #results = col.insert({ 'player_entry': r['entry'], 'player_name': r['entry_name'], 'month': month, 'league': r['league'], 'league_name': league['name']. 'rank': r['rank'], 'month_total': r['total'] })
                mcount += 1
            print ( "\t", mcount, "Players analyzed" )

        return


####
#
# this is a re-write of the recurrsive league leaderboard listing
#
# in development...still doesnt do much
#
# design:
# 1. find a list of all the league I am entered into
# 2. list all the teams that are in those leagues (that I'm copmepting against)
#    player_entry.my_entry_cleagues() already does this
#    warning: some leages have millions of players in them (so limit to 100)
# 3. produce leaderboard list performance rank of all teams in each league. #1, #2, #3 ....
#    note: player_entry.my_entry_cleagues() does not do this. It just prints my rank position in the league
# old: r_whose_inmy_league
#
# note: this method only does a leaderboard for my primary cleague. NOT all leagues

# TODO: these 3 methods are all the same...
#       (incl. whose_inmy_league()
#       consolidate and dedupe all 3

    def cleagues_leaderboard(self):    # this was the orignal/OLD recursive league standings report
        """NOT IN USE """
        """this method does good pre-checks"""

        logging.info('league_details:: cleagues_leaderboard()' )
        #print ("Analyzing league: ", self.league['name'] )

        event_id = i_am.current_event                    # current week event num
        if ( event_id is None ):    # test if season hasn't started yet
            print ( "\tLeague:", self.league['name'], "has not started yet - pending teams are..." ) 
            return

        for p in self.ne_pending:    # new players & all players in the pre-season are temporarily held here
            print ( "\tPlayer team ID:", p['id'], "-", p['player_first_name'], p['player_last_name'], "-", p['entry_name'] )

        if ( not self.results ):    # test if league results[] is empty
            print ( "\tLeague:", self.league['name'], "has no results to show yet!" )
        else:
            #print ( "\tLeaderboard results here...." )
            #for p in self.results:    # cycle through all of the results entries
            for p in fav_league.results:
                idx = p['id']
                league_details.cl_op_list[idx] = p['id']     # insert into global class var/dict (a nice quick list)
                print ( "\tRank:", p['rank'], "Team ID:", p['id'], "-", p['entry_name'], "(", p['player_name'], ") -", p['event_total'] )
        return

    def allmy_cl_lboard(self):    # list of CLASSIC leagues player is entered in
        # this method sets-up the global class var/dict fofr iterating
        """ cycle thru a list of all my leagues & prints them """
        """ Also populates an class global vaariable/dict (self.cl_op_list) with same info """

        logging.info('league_details:: allmy_cl_lboard(): Analyzing league ID: %s' % this_league )    # this_league <- args[]
        #print ( "Details for fav league:", self.league['id'], "(", self.league['name'], ")" )    # this_league <- args[]

        for v in self.results:
            a = str(this_league)
            print ( "\t Rank: %s Team: %s %s - %s - Gameweek points: %s" % ( \
                    v['rank'], \
                    v['entry'], v['entry_name'], \
                    v['player_name'], \
                    v['event_total'] ))

            league_details.cl_op_list[v['rank']] = v['entry']    #populate class global dict (this league: rank, player_team_id)

            #self.cl_op_list[v['rank']] = v['entry']    #populate class global dict (this league: rank, player_team_id)
            # TODO: this is where you can pre-populate the each league detals instance for faster full scanning analytics later
        return

###########################################
# Main()
#
parser = argparse.ArgumentParser(description='List out basic details for a player')
parser.add_argument('-d','--dbload', help='save JSON data into mongodb', action='store_true', dest='bool_dbload', required=False, default=False)
parser.add_argument('-l','--league', help='league entry id', required=False, default=False)
parser.add_argument('-p','--player', help='team player id', required=False, default='noplayerid')
parser.add_argument('-q','--query', help='squad player id', required=False, default=False)
parser.add_argument('-r','--recleague', help='recursive league details', action='store_true', dest='bool_recleague', required=False, default=False)
parser.add_argument('-v','--verbose', help='verbose error logging', action='store_true', dest='bool_verbose', required=False, default=False)
parser.add_argument('-x','--xray', help='enable all test vars/functions', action='store_true', dest='bool_xray', required=False, default=False)
parser.add_argument('-u','--username', help='username for accessing website', required=True, default='iamnobody')
parser.add_argument('-c','--password', help='password for accessing website', required=True, default='nopassword')
parser.add_argument('-g','--gameweek', help='game weeks to analyze', required=False, default=False)

args = vars(parser.parse_args())

print ( " " )
print ( "########## Initalizing bootstrap dataset ##########" )
print ( " " )

################
# ARGS[] pre-processing
#
if args['bool_verbose'] is True:
    print ( "Enabeling verbose info logging..." )
    logging.disable(0)     # Log level = NOTSET
    print ( "Command line args passed from shell..." )
    print ( parser.parse_args() )
    print ( " " )
else:
    logging.disable(20)    # Log lvel = INFO

username = args['username']
password = args['password']
this_player = args['player']
this_league = args['league']
rleague = args['bool_recleague']
xray_testing = args['bool_xray']
query_player = args['query']
game_week = args['gameweek']

# ARGS[] processing done
#################

# load in main bootstrap data set.
# THis is a big JSON dataset. Every EPL squad player and his data/stats etc.
bootstrap = fpl_bootstrap(this_player, args['username'], args['password'])         # create an instance of main player database
i_am = player_entry(this_player)                      # create instance of players basic ENTRY data-set (publically viewable stuff)

print ( "My name is:", i_am.entry['player_first_name'], i_am.entry['player_last_name'] )
print ( "My teams name is:", i_am.entry['name'] )
print ( "My team ID is:", i_am.playeridnum )
#print ( "My Username:", username )
#print ( "My Passowrd:", password )

print ( "Current gameweek is:", fpl_bootstrap.current_event )
print ( "Analyzing gameweek: ", end="" )
if game_week is False:
    print ( fpl_bootstrap.current_event )    # default to current gameweek
    game_week = fpl_bootstrap.current_event
else:
    print ( game_week )                      # otherwise, use the gameweek supplied in args[]

my_priv_data = priv_playerinfo(this_player, username, password )
if priv_playerinfo.api_get_status == "FAILED":
    print ( " " )
    print ( "Failed to access private data set for player:", this_player ) 
else:
    my_priv_data.my_stats()
    print ( " " )

if this_league is False:
    print ( "No fav league provided. Not showing Fav league LEADERBOARD" )
    print (i_am.entry['name'], "plays in", len(i_am.cleagues), "leagues" )
    print ( "======================= my leagues =======================" )
    i_am.my_entry_cleagues()
    print ("==========================================================" )
else:
    fav_league = league_details(this_player, this_league)    # populate an instance of my classic leagues
    if fav_league.league_exists != 404:
        print ( " " )
        print (i_am.entry['name'], "plays in", len(i_am.cleagues), "leagues" )
        print ( "======================= my leagues =======================" )
        i_am.my_entry_cleagues()
        print ( " ")
        print ( "============== League leaderbord for %s ==============" % this_league )
        #fav_league.whose_inmy_league()    # classic league leaderboard
        fav_league.allmy_cl_lboard()
        print ( "==========================================================" )
    else:
        print ( "ERROR - bad fav league number entered" )

print ( " " )
print ( "======================= my squad =======================" )
my_priv_data.list_mysquad()
print ( "==========================================================" )

if this_league is False:
    pass
else:
    print ( " " )
    print ( "============== Squad Analytics for gameweek: %s ==============" % game_week )
    my_priv_data.capt_anlytx()
    #for rank,opp_id in fav_league.cl_op_list.items():                 # method local var/dict
    for rank, opp_id in league_details.cl_op_list.items():              # class.global var/dict
        opp_pe_inst = player_entry(opp_id)                             # instance: player_entry(opp_id)
        opp_sq_anlytx = get_opponents_squad(opp_id, opp_pe_inst, game_week)    # create instance of this players squad (for gw event)
        opp_sq_anlytx.opp_squad_captain()                              # now run some CAPTAIN analytics on current instance (sloppy)
    print ( "==========================================================" )

print ( " " )
print ( "======================== Fixtures ========================" )
bootstrap.upcomming_fixtures()

print ( "===== HACKING =====" )
if query_player is False:
    print ( "===== not querying for any player =====" )
else:
    find_me = bootstrap.whois_element(int(query_player))
    print ( "Current gameweek:", fpl_bootstrap.current_event, "- Analyzing gameweek: ", game_week )
    print ( "Scanning for squad player:", query_player, end="" )
    print ( " (", end="" )
    print ( find_me, end="" )
    print ( ")" )
    for rank, opp_id in league_details.cl_op_list.items():  # [] <- player_ids in this league
        x_inst = player_entry(opp_id)        # instantiate a full player ENTRY instance
        opp_x_inst = get_opponents_squad(opp_id, x_inst, game_week )
        opp_x_inst.opp_sq_findplayer(query_player)

    print ( "==========================================================" )

# I cant recall what this section is supposed to do
# This is cool code, but its very complicated & doesnt work properly from a results/output perspective.
#if rleague is True:    # recursively list league details for player (all players in this league and leaderboard for this league)
#    print ( "### doing rleague... " )
#    p = {}             # working dict holds list of player ENTRY instance pointers
#    for x in fav_league.results:                    # order is random, not guaranteed to == source order
#        p[x['entry']] = player_entry(x['entry'])    # key = playerid, data = Entry instance pointer for playerid
#        for y,z in p.items():
#            z.my_teamname()
#            print ( " (", end="" )
#            z.my_name()
#            print ( ")" )
            #z.my_entry_cleagues()
            #z.allmy_cl_lboard(fav_league)
#            print ( "========================================================" )

# HACKING...

#for rank,opp_id in fav_league.cl_op_list.items():
#    x = player_entry(opp_id)
#    print ( "Team ID: ", x.my_id(), " Team name: ", x.my_teamname(), " Owner: ", x.my_name() )

#fpl_myteam_get(this_player)   # currently hard-coded player ID
#bootstrap.list_epl_teams()

print ( "### DONE ###" )

# todo
# convert fpl_myteam_get() to class player_mysquad
# convert get_opponents_squad() to class opponent_pub_view
# arg[dbload] - now does nothing since main() is now 100% class/method orientated
