#!/usr/bin/python3
import requests
from requests import Request, Session
import json
import sys
import unicodedata
import logging
import argparse
from random import randint
import pandas as pd

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
from fixtures import allfixtures

# logging setup
logging.basicConfig(level=logging.INFO)

FPL_API_URL = "https://fantasy.premierleague.com/api/"
BSS = "bootstrap-static"
BSD = "bootstrap-dynamic"
MYTEAM = "my-team/"
ENTRY = "entry/"
ME = "me/"
USER_SUMMARY_SUBURL = "element-summary/"
LCS_SUBURL = "leagues-classic/"
#LCS_SUBURL = "leagues-classic-standings/"
LEAGUE_H2H_STANDING_SUBURL = "leagues-h2h-standings/"
PLAYERS_INFO_SUBURL = "bootstrap-static"
PLAYERS_INFO_FILENAME = "allPlayersInfo.json"
STANDINGS_URL = "https://fantasy.premierleague.com/api/leagues-classic/"
#STANDINGS_URL = "https://fantasy.premierleague.com/drf/leagues-classic-standings/"
PAGINATION = "?page_new_entries=1&page_standings=1&phase=1"
#CLASSIC_PAGE = "&le-page=1&ls-page=1"

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
        return pe_cache[pe_key]    # player entry instance
    else:
        return 0    # NO Player ENTRY instance present
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
    rleague = args['bool_recleague']    # Currently DSIABLED. Needs new code
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

    print ( "Current gameweek is:", player_entry.current_event )    # allways get current event from player-entry

    print ( "Analyzing gameweek: ", end="" )    # if the user wants to look back in time at the non-current gameweek
    if game_week is False:
        print ( player_entry.current_event, "*using DEF/current" )    # default to current gameweek
        game_week = player_entry.current_event
    else:
        print ( game_week, "**USER provided" )                      # otherwise, use the gameweek supplied in args[]

    my_priv_data = priv_playerinfo(this_player, username, password, bootstrap, i_am )    # info about ME
    if priv_playerinfo.api_get_status == "FAILED":
        print ( " " )
        print ( "Failed to access private data set for player:", this_player )
        return
    else:
        my_priv_data.my_stats()
        print ( " " )

# show some info & stats about the leaguies that this player is registered in
# ONLY executes if -l option provided...
    print (i_am.entry['name'], "plays in", len(i_am.cleagues), "leagues" )
    print ( "============================ All my leagues ============================" )
    i_am.my_entry_cleagues()
    print ( player_entry.ds_df_pe0.sort_values(by='Index', ascending=False) )    # only do after fixtures datascience dataframe has been built
    print ( "========================================================================" )

    if this_league is False:
        print ( "" )
    else:
        #print (i_am.entry['name'], "plays in", len(i_am.cleagues), "leagues" )
        print ( " " )
        fav_league = league_details(this_player, this_league, my_priv_data, bootstrap)    # populate an instance of my classic leagues
        if fav_league.league_exists != 404:
            i_am.my_entry_cleagues()
            print ( "========================================= League leaderbord ================================================" )
            print ( "=========================================", fav_league.my_leaguename(), "", end="" )
            for P in range(65 - len(fav_league.my_leaguename()) ):
                print ( "=", end="" )
                # pretty print leaderboard title
            print ( " " )
            fav_league.allmy_cl_lboard(this_league)
            # only do after fixtures datascience dataframe has been built
            lx0 = league_details.ds_df_ld0[(league_details.ds_df_ld0['Rank'] == 1) ]     # select the TOP #1 ranked player
            lx1 = lx0.Total.iloc[0]    # extract the total points of the top ranked player
            lx2 = league_details.ds_df_ld0.assign(Pts_behind=lx1 - league_details.ds_df_ld0['Total'] ) # lx3 =
            lx3 = lx2.sort_values(by='moved', ascending=False)     # sort new DF by MOST improoved     # lx2 = lx3
            lx3 = lx3.reset_index(drop=True)   # reset index becasue we use it in new column asignment # lx2 = lx2
            print ( lx3.assign(Topmvr=lx3.index+1).sort_values(by='Rank', ascending=True) )    # add new column for TOP mover & resort back to RANK # lx2
            print ( "============================================================================================================" )
        else:
            print ( "ERROR - Cant build League leaderbord. BAD league number entered!" )

# ONLY executes if -l option provided...otherwise we're NOT intersted in league analytics
# if YES, then create a leaderbaord for <LEAGUE_ID> with some captain stats
    if this_league is False:    # only called if user asked to analyze a LEAGUE (-l <LEAGUE_ID>)
        pass
    else:
        print ( " " )
        #print ( "===== League (%s) Captain Analytics for gameweek: (%s) ========" % (this_league, game_week) )
        print ( "==================== Captain Analytics for gameweek:", game_week, "====================" )
        print ( "====================", fav_league.my_leaguename(), "", end="" )
        for P in range(53 - len(fav_league.my_leaguename()) ):
            print ( "=", end="" )
            # pretty print leaderboard title
        print ( " " )
        cid, cn = my_priv_data.my_capt_info()                                 # find MY captain
        print ( "My captain is:", cid, "-", cn, "..." )
        ds_cap_df0 = pd.DataFrame(columns=[ 'Team', 'Cap_name', 'ID', 'Pos', 'GWpts' ] )    # shape a new pandas dataframe
        pe_inst_cache = {}      # global optz cache of all opponent player ENTRY instances
        opp_team_inst = {}      # global optz cache of all player ENTRY & class instance to full squad dataset
        for rank, opp_id in league_details.cl_op_list.items():            # class.global var/dict
            opp_pe_inst = player_entry(opp_id)                            # create instance: player_entry(opp_id)
            opp_sq_anlytx = get_opponents_squad(opp_id, opp_pe_inst, game_week, my_priv_data, bootstrap)    # create inst of squad (for gw event)
            opp_team_inst[opp_id] = opp_sq_anlytx                         # build cache : key = playerid, data = full squad instance
            pe_inst_cache[opp_id] = opp_pe_inst                           # build cache : key = playerid, data = PE instance
            xx = opp_sq_anlytx.opp_squad_captain()                        # now run some CAPTAIN analytics on current instance (sloppy)
            #ds_data0 = [[ xx[0], xx[1], xx[2], xx[3], xx[4] ]]    # a fully structured dict returned to us
            #print ( xx )
            ds_data0 = { opp_id: xx }    # shapre the pandas dataframe correctly
            df_temp0 = pd.DataFrame.from_dict( ds_data0, orient='index', columns=[ 'Team', 'Cap_name', 'ID', 'Pos', 'GWpts' ] )
            ds_cap_df0 = ds_cap_df0.append(df_temp0)    # append this ROW of data into the DataFrame
        print ( ds_cap_df0.sort_values(by='GWpts', ascending=False) )
        print ( "==========================================================================" )

# This is inaccurate. Its looking at your active live current squad (i.e. NOT gameweek sensative)
# points earned is ~ irrelevant becauset it is that each player earned in the last game.
# probably should be showing squad for a specific gameweek game
    print ( " " )
    print ( "========================== my squad ===========================" )
    print ( "============= Warning: this is your active squad ==============" )
    my_priv_data.list_mysquad()
    # print ( priv_playerinfo.ds_df1 )    # only do after fixtures datascience dataframe has been built
    print ( priv_playerinfo.ds_df1.sort_values(by='PtsLG', ascending=False) )    # only do after fixtures dataframe has been pre-built
    print ( "==========================================================" )

# Deep analytics of my squad
# NOTE: only triggered if user asked to analyze a LEAGUE (-l <LEAGUE_ID>)
#       This makes sense because the user wants deeper league performance stats.
# LOGIC: 1. cycle through every player in my squad...(active current squad)
#        2. cycle through every player, on every opponents team, in **this_leage**
#        3. for the last game (TODO: need to make this code gameweek sensitive)
#        4. output - where your squad members are shared/across/intersects with other opponent(s) squad members

    if this_league is False:
        pass
    else:
        ds_hm_df5 = pd.DataFrame()
        print ( " " )
        print ( "========================= Deep squad analytics for my active squad ===========================" )
        print ( "=========================", fav_league.my_leaguename(), "", end="" )
        for P in range(67 - len(fav_league.my_leaguename()) ):
            print ( "=", end="" )
            # pretty print leaderboard title
        print ( " " )
        for pos in range (0, 15):
            ds_hm_data0 = []
            opp_team_id = []
            opp_team_name = []
            #print ( "Player:", pos+1, " ", end="" )
            got_him = my_priv_data.get_oneplayer(pos)    # cycle trhough all players on MY TEAM - WARNING: prints out some info also
            for oid, i in opp_team_inst.items():         # cycle through cached class instances of each OPPONENTS team
                if oid != int(i_am.playeridnum):         # skip *my team* in the cached class instances
                    found_him = i.got_player(got_him)    # does this player exists in this OPPONENTS squad
                    if found_him == 1:                   # returns 1 if this player exists in this squad
                        x = scan_pe_cache(pe_inst_cache, oid)   # get pe_inst from pre-populated player entry instance cache
                        y = x.my_teamname()
                        opp_team_id.append(x.my_id())
                        opp_team_name.append(x.my_teamname())
                        ds_hm_data0.append(1)
                    else:
                        ds_hm_data0.append(0)
                        x = scan_pe_cache(pe_inst_cache, oid)   # get pe_inst from pre-populated player entry instance cache
                        opp_team_id.append(x.my_id())
                        opp_team_name.append(x.my_teamname())
                        pass
            # COLUMN total logic
            ds_hm_data3 = (pd.Series(ds_hm_data0, index=opp_team_name) )       # setup a series as data for COLUMN insertion
            ds_hm_df5.insert(loc=0, value=ds_hm_data3, column=got_him )        # inset COLUMN
        # create new ROW of COLUMN totals
        hm_tr_data0 = pd.Series( ds_hm_df5.sum(axis=0), name='X-ref TOTALS' )   # setup new ROW = count of COLUMN totals
        ds_hm_df5 = ds_hm_df5.append(hm_tr_data0)    # append this ROW into existing DataFrame as FINAL row
        # ROW total logic
        new_col = pd.DataFrame(ds_hm_df5.sum(axis=1))    # compute ROW totals for ouput as a new COLUMN
        # create new COLUMN of ROW totals
        ds_hm_df5 = ds_hm_df5.assign( TOTAL=new_col )    # add new ROW into existing DataFrame
        print ( ds_hm_df5 )
        print ( "==============================================================================================" )


# this function scans ALL of your OPPONENTS squads in a league
# looking for a specific <Player_ID>
# and analyzes if that player is present in an OPPONENTS squad
# NOTE: only triggered if -l <LEAGUE_ID> provided by user
    print ( " " )
    print ( " " )
    print ( " " )
    if query_player is False:
        print ( "===== not querying for any player =====" )
        print ( " " )
    else:
        print ( " " )
        find_me = bootstrap.whois_element(int(query_player))
        print ( "=========== Analysing all opponents squads for 1 player:", find_me, "===========" )
        print ( "Current gameweek:", player_entry.current_event, "- Analyzing gameweek: ", game_week )
        print ( "Scanning all opponents squads..." )
        for oppid, inst in opp_team_inst.items():    # cycle through class instances for each opponents team
            inst.opp_sq_findplayer(query_player)     # very fast. In mem scan. Pre-instantiated from elsewhere

        print ( "==========================================================" )


# Show the next 10 fixtures
    print ( " " )
    next_event = player_entry.current_event + 1
    print ( "==================== Fixture Analytics ====================" )
    print ( "==================== Gameweek:", next_event, "====================" )
    these_fixtures = allfixtures(i_am.playeridnum, bootstrap, next_event )
    these_fixtures.get_standings()        # no output - update latest dataset - standings/ranking. Should do this early, or things will fail
    these_fixtures.upcomming_fixtures(1)    # 0 = NO, 1 = YES datascience anqalytics for fixtures
    print ( allfixtures.ds_df0.sort_values(by='PlayME', ascending=False) )    # only do after fixtures datascience dataframe has been built
    print ( " " )
    print ( "### DONE ###" )

if __name__ == '__main__':
    main()
