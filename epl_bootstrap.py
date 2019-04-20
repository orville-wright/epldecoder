#!/usr/bin/python3
import requests
from requests import Request, Session
import json
import sys
import unicodedata
import logging
import argparse
from random import randint

from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
from six import iteritems
from six import itervalues

###
# my private classes & methods
from league_details import league_details
from get_opponents_squad import get_opponents_squad
from player_entry import player_entry
from priv_playerinfo import priv_playerinfo

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
# Basic API calls agaist the bootstrap url (..premierleague.com/drf/...) dont require any authentication,
# for any valid game opponent player id. but...if you want explict details about a game player/user team
# then you must authenticate as a vlaid game user. for all API calls (..premierleague.com/drf/...)
#
# Known API endpoint functions
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
    api_get_status = ""

    def __init__(self, playeridnum, username, password):
        self.playeridnum = str(playeridnum)
        self.username = username
        self.password = password
        fpl_bootstrap.username = username    # make USERNAME var global to class instance
        fpl_bootstrap.password = password    # make PASSWORD var global to class instance

        logging.info('fpl_bootstrap:: - create bootstrap ENTRY class instance for player: %s' % self.playeridnum )

        self.epl_team_names = {}    # global dict accessible from wihtin this base class
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


def scan_pe_cache(pe_cache, pe_key):
    """scan the global Player ENTRY instance cache"""
    """for a player id"""
    """Will error is pe_cache is not real dict"""

    if pe_key in pe_cache:
        # print ( "Player ENTRY instance found:", pe_cache[pe_key] )
        return pe_cache[pe_key]
    else:
        pass
        #print ( "NO Player ENTRY instance present" )
    return

####################### main ###########################
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--password', help='password for accessing website', required=True, default='nopassword')
    parser.add_argument('-d','--dbload', help='save JSON data into mongodb', action='store_true', dest='bool_dbload', required=False, default=False)
    parser.add_argument('-g','--gameweek', help='game weeks to analyze', required=False, default=False)
    parser.add_argument('-l','--league', help='league entry id', required=False, default=False)
    parser.add_argument('-p','--player', help='team player id', required=True, default='noplayerid')
    parser.add_argument('-q','--query', help='squad player id', required=False, default=False)
    parser.add_argument('-r','--recleague', help='recursive league details', action='store_true', dest='bool_recleague', required=False, default=False)
    parser.add_argument('-u','--username', help='username for accessing website', required=True, default='iamnobody')
    parser.add_argument('-v','--verbose', help='verbose error logging', action='store_true', dest='bool_verbose', required=False, default=False)
    parser.add_argument('-x','--xray', help='enable all test vars/functions', action='store_true', dest='bool_xray', required=False, default=False)


    args = vars(parser.parse_args())
    print ( " " )
    print ( "########## Initalizing bootstrap dataset ##########" )
    print ( " " )

# ARGS[] pre-processing - set-ip logging before anything else
    if args['bool_verbose'] is True:
        print ( "Enabeling verbose info logging..." )
        logging.disable(0)     # Log level = NOTSET
        print ( "Command line args passed from shell..." )
        print ( parser.parse_args() )
        print ( " " )
    else:
        logging.disable(20)    # Log lvel = INFO

    # now process remainder of cmdline args[]
    username = args['username']
    password = args['password']
    this_player = args['player']
    this_league = args['league']
    rleague = args['bool_recleague']
    xray_testing = args['bool_xray']
    query_player = args['query']
    game_week = args['gameweek']

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

    my_priv_data = priv_playerinfo(this_player, username, password, bootstrap )    # info about ME
    if priv_playerinfo.api_get_status == "FAILED":
        print ( " " )
        print ( "Failed to access private data set for player:", this_player )
        return
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
            fav_league.allmy_cl_lboard(this_league)
            print ( "==========================================================" )
        else:
            print ( "ERROR - bad fav league number entered" )

    print ( " " )
    print ( "======================= my squad =======================" )
    my_priv_data.list_mysquad()
    print ( "==========================================================" )

# if NO -l <LEAGUE ID> flag, then we're not intersted in league analytics
# if YES, then create a leaderbaord for <LEAGUE_ID> with some stats
    if this_league is False:    # only called if user asked to analyze a LEAGUE (-l <LEAGUE_ID>)
        pass
    else:
        print ( " " )
        print ( "===== League (%s) Captain Analytics for gameweek: (%s) ========" % (this_league, game_week) )
        my_priv_data.capt_anlytx()                                        # find MY captain
        #for rank,opp_id in fav_league.cl_op_list.items():                    # method local var/dict
        print ( "Scanning all teams in this league...")

        pe_inst_cache = {}      # global optz cache of all opponent player ENTRY instances
        opp_team_inst = {}      # global optz cache of all player ENTRY & class instance to full squad dataset
        for rank, opp_id in league_details.cl_op_list.items():            # class.global var/dict
            opp_pe_inst = player_entry(opp_id)                            # create instance: player_entry(opp_id)
            opp_sq_anlytx = get_opponents_squad(opp_id, opp_pe_inst, game_week, my_priv_data, bootstrap)    # create inst of squad (for gw event)
            opp_team_inst[opp_id] = opp_sq_anlytx                         # build cache : key = playerid, data = full squad instance
            pe_inst_cache[opp_id] = opp_pe_inst                           # build cache : key = playerid, data = PE instance
            opp_sq_anlytx.opp_squad_captain()                              # now run some CAPTAIN analytics on current instance (sloppy)
        print ( "==========================================================" )

# this function scans your squad, looking for a specific <Player_ID>
# only works if -l <LEAGUE_ID> provided
    if query_player is False:
        print ( "===== not querying for any player =====" )
        print ( " " )
    else:
        find_me = bootstrap.whois_element(int(query_player))
        print ( " ")
        print ( "Current gameweek:", fpl_bootstrap.current_event, "- Analyzing gameweek: ", game_week )
        print ( "Scan opponents squad for:", query_player, end="" )
        print ( " (", end="" )
        print ( find_me, end="" )
        print ( ")" )
        print ( "==========================================================" )
        for oppid, inst in opp_team_inst.items():    # cycle through class instances for each opponents team
            inst.opp_sq_findplayer(query_player)     # very fast. In mem scan. Pre-instantiated from elsewhere
        print ( "==========================================================" )

# deep analytics of my squad
# cycle through every player on my team...
# and then through eveyr player on every team in this leage...
# and report back, which opponent shares the same players that I selected
    if this_league is False:    # only called if user asked to analyze a LEAGUE (-l <LEAGUE_ID>)
        pass
    else:
        print ( " " )
        print ( "=========== Deep squad analytics against my squad =============" )
        for pos in range (0, 15):
            z = 0
            tl = ""
            print ( "Player:", pos, " ", end="" )
            got_him = my_priv_data.get_oneplayer(pos)
            for oid, i in opp_team_inst.items():         # cycle through class instances cache for each opponents team
                if oid != int(i_am.playeridnum):         # skip my team
                    found_him = i.got_player(got_him)    # does this player exists in this squad
                    if found_him == 1:
                        z += 1
                        x = scan_pe_cache(pe_inst_cache, oid)   # pe_inst_cache is a global dict, populated elesewhere !!
                        y = x.my_teamname()
                        tl = tl + y + " "
                    else:
                        pass
            if z != 0:
                print ( "Found in: ", z, "teams >", tl)
            else:
                print ( "Unique player not in any opponents squad" )

            print ( "..." )
            z = 0

# next 10 fixtures
    print ( " " )
    print ( "======================== Fixtures ========================" )
    bootstrap.upcomming_fixtures()
    print ( "### DONE ###" )

if __name__ == '__main__':
    main()
