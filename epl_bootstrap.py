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

########################################################
# This is not a CLASS yet
# but... can be deleted? - depricated by which class?
# fpl_myteam_get is no longer called by any code.
#
# API request of detailed player team info, stats & data
# requires username/password authentication for API access to player dataset
# The JSON dataset can also be...
#     - inserted into the MongoDB collection
#     - Printed in a nice human readable non-JSON format
#
# takes playerid as input data

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


####################### main ###########################
def main():
    parser = argparse.ArgumentParser()
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

    my_priv_data = priv_playerinfo(this_player, username, password, bootstrap )
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
    if this_league is False:
        pass
    else:
        print ( " " )
        print ( "===== League (%s) Captain Analytics for gameweek: (%s) ========" % (this_league, game_week) )
        my_priv_data.capt_anlytx()
    #for rank,opp_id in fav_league.cl_op_list.items():                 # method local var/dict
        for rank, opp_id in league_details.cl_op_list.items():              # class.global var/dict
            opp_pe_inst = player_entry(opp_id)                             # instance: player_entry(opp_id)
            opp_sq_anlytx = get_opponents_squad(opp_id, opp_pe_inst, game_week, my_priv_data, bootstrap)    # create instance of this players squad (for gw event)
            opp_sq_anlytx.opp_squad_captain()                              # now run some CAPTAIN analytics on current instance (sloppy)
        print ( "==========================================================" )

# this function scans your squad, looking for a specific <Player_ID>
# only works if -l <LEAGUE_ID> provided
    if query_player is False:
        print ( "===== not querying for any player =====" )
    else:
        find_me = bootstrap.whois_element(int(query_player))
        print ( " ")
        print ( "Current gameweek:", fpl_bootstrap.current_event, "- Analyzing gameweek: ", game_week )
        print ( "Scanning opponents squad for player:", query_player, end="" )
        print ( " (", end="" )
        print ( find_me, end="" )
        print ( ")" )
        for rank, opp_id in league_details.cl_op_list.items():  # [] <- player_ids in this league
            x_inst = player_entry(opp_id)        # instantiate a full player ENTRY instance
            opp_x_inst = get_opponents_squad(opp_id, x_inst, game_week, my_priv_data, bootstrap)    # create instance of this players squad (for gw event)
            opp_x_inst.opp_sq_findplayer(query_player)
        print ( "==========================================================" )

# next 10 fixtures
    print ( " " )
    print ( "======================== Fixtures ========================" )
    bootstrap.upcomming_fixtures()
    print ( "### DONE ###" )

if __name__ == '__main__':
    main()

# import pdb; pdb.set_trace()
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

# TODO
# convert fpl_myteam_get() to class player_mysquad
# convert get_opponents_squad() to class opponent_pub_view
# arg[dbload] - now does nothing since main() is now 100% class/method orientated
