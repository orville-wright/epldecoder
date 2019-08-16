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

# my private classes & methods
from fpl_bootstrap import fpl_bootstrap
from league_details import league_details
from get_opponents_squad import get_opponents_squad
from player_entry import player_entry
from priv_playerinfo import priv_playerinfo

# logging setup
logging.basicConfig(level=logging.INFO)

# FPL_API_URL = "https://fantasy.premierleague.com/drf/"
FPL_API_URL = "https://fantasy.premierleague.com/api/"
BST = "bootstrap"
BSS = "bootstrap-static"
BSD = "bootstrap-dynamic"
MYTEAM = "my-team/"
ENTRY = "entry/"
ME = "me/"
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
# https://fantasy.premierleague.com/drf/bootstrap-dynamic    # should use this for initial login & cookie decode/hacking
#
# https://fantasy.premierleague.com/drf/entry/1980723
# https://fantasy.premierleague.com/drf/event/23/live
# https://fantasy.premierleague.com/drf/entry/1980723/event/23/picks

############################################
# Global methods for main()

def scan_pe_cache(pe_cache, pe_key):
    """scan the global Player ENTRY instance cache"""
    """for a player id"""
    """Will error is pe_cache is not real dict"""

    if pe_key in pe_cache:
        # print ( "Player ENTRY instance found:", pe_cache[pe_key] )
        return pe_cache[pe_key]
    else:
        return 0
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
    bootstrap = fpl_bootstrap(this_player, username, password)         # create an instance of main player database
    i_am = player_entry(this_player)                      # create instance of players basic ENTRY data-set (publically viewable stuff)

#    print ( "My name is:", i_am.entry['player_first_name'], i_am.entry['player_last_name'] )
    print ( "My name is:", i_am.my_name() )
    print ( "My teams name is:", i_am.my_teamname() )
    print ( "My team ID is:", i_am.my_id() )
#print ( "My Username:", username )
#print ( "My Passowrd:", password )

#    print ( "Current gameweek is:", fpl_bootstrap.current_event )
    print ( "Current gameweek is:", player_entry.current_event )

    print ( "Analyzing gameweek: ", end="" )
    if game_week is False:
        print ( fpl_bootstrap.current_event )    # default to current gameweek
        game_week = fpl_bootstrap.current_event
    else:
        print ( game_week )                      # otherwise, use the gameweek supplied in args[]

    my_priv_data = priv_playerinfo(this_player, username, password, bootstrap, i_am )    # info about ME
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


# This is inaccurate. Its looking at your active live current squad
# point earned is irrelevant becauset they will be what that player earned in the last game.
# probably should be showing squad for last game
    print ( " " )
    print ( "========================== my squad ===========================" )
    print ( "============= Warning: this is your active squad ==============" )
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
# cycle through every player on my squad...(yor artive current squad)
# cycle through eveyr player on every team in **this_leage**...(for the last game)
# report back, which opponent shares the same squad players e.g your squad <==> opponents
    if this_league is False:    # only called if user asked to analyze a LEAGUE (-l <LEAGUE_ID>)
        pass
    else:
        print ( " " )
        print ( "=========== Deep squad analytx for my active squad =============" )
        print ( "===================== For league (", end="" )
        print ( this_league, end="" )
        print ( ") ======================" )
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

            print ( "+--------------------------------------------------------+" )
            z = 0

# next 10 fixtures
    print ( " " )
    print ( "======================== Fixtures ========================" )
    bootstrap.get_standings()        # should do this early, or things will fail
#    bootstrap.upcomming_fixtures()

    # bootstrap.game_decisions(328, 338)    # no longer makes sense

    print ( " " )
    print ( "### DONE ###" )

if __name__ == '__main__':
    main()
