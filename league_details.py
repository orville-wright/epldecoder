#!/usr/bin/python3
import requests
from requests import Request, Session
import json
import sys
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
USER_SUMMARY_SUBURL = "element-summary/"
LCS_SUBURL = "leagues-classic/"
LEAGUE_H2H_STANDING_SUBURL = "leagues-h2h-standings/"
PLAYERS_INFO_SUBURL = "bootstrap-static"
PLAYERS_INFO_FILENAME = "allPlayersInfo.json"
STANDINGS_URL = "https://fantasy.premierleague.com/api/leagues-classic/"
PAGINATION = "?page_new_entries=1&page_standings=1&phase=1"
#CLASSIC_PAGE = "&le-page=1&ls-page=1"    # 2019/2020 season changes

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
    cl_op_list = {}    # class global accessor : a list of all oponents team ID's in this league
    api_get_status = ""
    username = ""
    password = ""
    my_priv_data = ""
    bootstrap = ""

    def __init__(self, playeridnum, leagueidnum, my_priv_data, bootstrap):
        self.playeridnum = str(playeridnum)
        self.leagueidnum = str(leagueidnum)
        self.bootstrap = bootstrap
        league_details.username = my_priv_data.username
        league_details.password = my_priv_data.password
        league_details.my_priv_data = my_priv_data
        league_details.bootstrap = bootstrap

        logging.info('league_details:: - init: Playerid: %s league num: %s' % (self.playeridnum, self.leagueidnum))
        self.t = requests.Session()
        user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0'}
        API_URL0 = 'https://fantasy.premierleague.com/a/login'
        EXTRACT_URL = FPL_API_URL + LCS_SUBURL + str(leagueidnum) + '/standings/' + PAGINATION

 #new v3.0 cookie hack
        logging.info('get_opponents_squad:: EXTRACT saved cookie from bootstrap for playerid: %s' % self.playeridnum )
        logging.info('get_opponents_squad:: SET cookie: %s' % self.bootstrap.my_cookie )
        self.t.cookies.update({'pl_profile': self.bootstrap.my_cookie})

# Do REST API I/O now...
# 1st get authenticates, but must use critical cookie (i.e. "pl_profile")
# 2nd get does the data extraction if auth succeeds - failure = all JSON dicts/fields are empty
        tx0 = self.t.get( API_URL0, headers=user_agent, auth=HTTPBasicAuth(league_details.username, league_details.password) )
        tx = self.t.get( EXTRACT_URL, headers=user_agent, auth=HTTPDigestAuth(league_details.username, league_details.password) )
        self.auth_status = tx0.status_code
        self.gotdata_status = tx.status_code
        logging.info('league_details:: init - Logon AUTH url: %s' % tx0.url )
        logging.info('league_details:: init - API data get url: %s' % tx.url )

        tx0_auth_cookie = requests.utils.dict_from_cookiejar(self.t.cookies)
        logging.info('league_details:: AUTH login resp cookie: %s' % tx0_auth_cookie['pl_profile'] )

####

        if tx.status_code == 404:    # 404 means this league number does not exists
            logging.info('league_details:: init ERROR - API get failed - league %s does not exist' % leagueidnum )
        else:
            # dict popuated with extractd JSON league data from API GET
            # note: public dict shared by multiple league_details:() methods but *NOT* shared by league_details::monthly_aggr_l_standings()
            self.league_exists = tx.status_code
            self.cl_op_list = {}    # a dict holding a list of all oponents team ID's in this league

            logging.info('league_details:: - init API URL: %s' % EXTRACT_URL )
            t2 = json.loads(tx.text)
            #print ("LEAGUE_DETAILS: ", t2)
            self.league = t2['league']
            self.standings = t2['standings']
            self.results = self.standings['results']
            # self.ne_pending = self.new_entries['results']  # depricated 2019/2020 season
            #self.new_entries = t2['new_entries']

        return

    def my_leagueidnum(self):
        """ extract the league ID number """
        logging.info('league_details.my_leagueidnum()' )
        print (self.league['id'])      # TODO: remove this and CHANGE to -> return(self.league['id'])
        return


    def my_leaguename(self):
        """ extract the Human readable real League Name """
        """ does not print any oujtput. Only returns your info"""

        logging.info('league_details.my_leaguename()' )
        n = self.league['name']
        return n


    def whose_inmy_league(self):
        """ iterate on JSON data instance & display key info about the players in this league """
        # NOTES: this method does NOT display league results. Just opponent teams in this league
        #        at the beginning of the season this fails becasue players are held in new_entires section. NOT results section.
        # this method has the best print format
        logging.info('league_details.whose_inmy_league()' )
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
            logging.info('league_details.monthly_aggr_l_standings() - API get for month: %s' % s_month )
            # should test rx1.status_code here...

            logging.info('league_details.monthly_aggr_l_standings(): URL for get: %s' % LS_URL )
            logging.info('league_details.monthly_aggr_l_standings(): GET status: %s' % rx1.status_code )

            self.m0 = json.loads(rx1.text)
            self.league = self.m0['league']
            self.standings = self.m0['standings']
            self.results = self.standings['results']
            #self.new_entries = self.m0['new_entries']    # depricated 2019/2020 season

            mcount = 0
            for r in self.results:
                #print (".", end="")
                print ( "\t", "Player:", r['player_name'], "Monthly rank:", r['rank'], "Monthly total:", r['total'] )
                #results = col.insert({ 'player_entry': r['entry'], 'player_name': r['entry_name'], 'month': month, 'league': r['league'], 'league_name': league['name']. 'rank': r['rank'], 'month_total': r['total'] })
                mcount += 1
            print ( "\t", mcount, "Players analyzed" )

        return

####
# re-write of the recurrsive league leaderboard listing
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

# TODO: these methods end up doing the same thing...
#       (incl. whose_inmy_league()
#       consolidate and dedupe all 3

    def cleagues_leaderboard(self):    # this was the orignal/OLD recursive league standings report
        """NOT IN USE """
        """Broken & Old : this method does good pre-checks"""

        logging.info('league_details.cleagues_leaderboard()' )
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

    def allmy_cl_lboard(self, this_league):    # list of CLASSIC leagues player is entered in
        # this method sets-up the global class var/dict fofr iterating
        """ cycle thru a list of all my leagues & prints them """
        """ Also populates an class global vaariable/dict (self.cl_op_list) with same info """

        logging.info('league_details.allmy_cl_lboard(): Analyzing league ID: %s' % this_league )    # this_league <- args[]
        #print ( "Details for fav league:", self.league['id'], "(", self.league['name'], ")" )    # this_league <- args[]

        for v in self.results:
            a = str(this_league)
            print ( "Rank: %s Team: %s %s - %s - Gameweek points: %s" % ( \
                    v['rank'], \
                    v['entry'], v['entry_name'], \
                    v['player_name'], \
                    v['event_total'] ))

            league_details.cl_op_list[v['rank']] = v['entry']    #populate class global dict (this league: rank, player_team_id)

            # self.cl_op_list[v['rank']] = v['entry']
            # populate class global dict (this league: rank, player_team_id)
            # TODO: this is where you can pre-populate each league detals instance for faster full scanning analytics later
        return
