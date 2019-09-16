#!/usr/bin/python3
import requests
from requests import Request, Session
import json
import logging
import http.client
import pandas as pd

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
LEAGUE_H2H_STANDING_SUBURL = "leagues-h2h-standings/"
PLAYERS_INFO_SUBURL = "bootstrap-static"
PLAYERS_INFO_FILENAME = "allPlayersInfo.json"
STANDINGS_URL = "https://fantasy.premierleague.com/api/leagues-classic/"
PAGINATION = "?page_new_entries=1&page_standings=1&phase=1"
#CLASSIC_PAGE = "&le-page=1&ls-page=1"    # 2019/2020 season changes

#####################################################
# Fixure analytics was a poorly managed & messy JSON dataset
# in the game model. As of 2019/2020 season, they game architects
# seem to have started addressing this and moved all STANDINGS and
# FGIXTURES related data into a less cryptic JSON dataset

class allfixtures:
    """Base class to manage fixtires related info"""
    """This JSON dataset may be publically accessible."""
    """So it doesn't require any auth"""

    # Class Global attributes
    this_event = ""
    api_get_status = ""
    standings_t = ""
    bootstrap = ""
    ds_df0 = ""        # Data science DATA FRAME 0  (fixtures)

    def __init__(self, playerid, bootstrapdb, eventnum):
        self.eventnum = str(eventnum)
        self.playeridnum = playerid
        logging.info('allfixtures:: - create fixtures class instance for gameweek: %s' % self.eventnum )

        allfixtures.bootstrap = bootstrapdb
        allfixtures.this_event = self.eventnum
        # create an empty pandas DataFrame with specific column names pre-defined
        allfixtures.ds_df0 = pd.DataFrame(columns=[ 'Time', 'Hid', 'Home', 'Away', 'Aid', 'RankD', 'GDd', \
                                                  'GFd', 'GAd', 'Hwin', 'Awin', 'HomeA', 'HGA', 'Weight', 'PlayME'] )

        s = requests.Session()
        user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0'}
        API_URL0 = 'https://fantasy.premierleague.com/a/login'
        API_URL1 = FPL_API_URL + 'fixtures/?event=' + self.eventnum

# new v3.0 cookie hack
        logging.info('get_opponents_squad:: EXTRACT saved cookie from bootstrap for playerid: %s' % self.playeridnum )
        logging.info('get_opponents_squad:: SET cookie: %s' % self.bootstrap.my_cookie )
        s.cookies.update({'pl_profile': self.bootstrap.my_cookie})

## Do REST API I/O now...
# 1st get authenticates, but must use critical cookie (i.e. "pl_profile")
# 2nd get does the data extraction if auth succeeds - failure = all JSON dicts/fields are empty
        rx0 = s.get( API_URL0, headers=user_agent )
        rx1 = s.get( API_URL1, headers=user_agent )
        self.auth_status = rx0.status_code
        self.gotdata_status = rx1.status_code
        logging.info('allfixtures:: init - Logon AUTH url: %s' % rx0.url )
        logging.info('allfixtures:: init - API data get url: %s' % rx1.url )

        rx0_auth_cookie = requests.utils.dict_from_cookiejar(s.cookies)
        logging.info('allfixtures:: AUTH login resp cookie: %s' % rx0_auth_cookie['pl_profile'] )

        if rx0.status_code != 200:    # failed to authenticate
            logging.info('allfixtures:: - init ERROR login AUTH failed with resp %s' % self.auth_status )
            return

        if rx1.status_code != 200:    # 404 API get failed
            logging.info('allfixtures:: - init ERROR API get failed with resp %s' % self.gotdata_status )
            return
        else:
            logging.info('allfixtures:: Login AUTH success resp: %s' % self.auth_status )
            logging.info('allfixtures:: API data GET resp is   : %s  ' % self.gotdata_status )
            # create JSON dict with players ENTRY data, plus other data thats now available
            # WARNING: This is a very large JSON data structure with stats on every squad/player in the league
            #          Dont load into memory multiple times. Best to insert into mongodb & access from there
            # EXTRACT JSON data/fields...
            # note: entry[] and player[] are not auto loaded when dataset lands (not sure why)
            t0 = json.loads(rx1.text)
            self.fixtures = t0    # entire JSON dict - process current event (could be past/present/future)
        return

#######################

    def upcomming_fixtures(self, ds_yes_no):
        """Fixtures are messy in the main JSON data model"""
        """There is no simple data set / table quickly available."""
        """You have to interrogate & build your list of fixtures every time"""

        # This JSON structure was destroyed in the 2019/2020 season changes.
        self.datasci = ds_yes_no
        logging.info('allfixtures.upcomming_fixtures() - init : %s' % ds_yes_no )

        tn_idx = self.bootstrap.list_epl_teams()    # build my nice helper team id/real name dict
        for fixture in self.fixtures:         # BROKEN by 2019/2020 JSON changes
            idx_h = int(fixture['team_h'])    # get INT num of HOME team to use as search key for this teams real team-name
            idx_a = int(fixture['team_a'])    # get INT num of AWAY team to use as search key for this teams real team-name
            h_dif = int(fixture['team_h_difficulty'])    # get INT for difficulty factor for HOME team to win this game
            a_dif = int(fixture['team_a_difficulty'])    # get INT for difficulty factor for AWAY team to win this game
            gametime = fixture['kickoff_time']
            # do some analytics on fixtures...
            if self.datasci == 1:    # 1 = do deep datascience analytics on fixtures
                self.game_decisions(idx_h, idx_a, h_dif, a_dif, gametime)    # run seperately for each individual game fixture/match
            else:
                pass
                print ( "GW:", fixture['event'], fixture['kickoff_time'], \
                        "HOME:", self.bootstrap.epl_team_names[idx_h], \
                        "vs.", self.bootstrap.epl_team_names[idx_a], "(AWAY)" )

        return

    def game_decisions(self, team_h, team_a, h_dif, a_dif, gametime):
        """Datascience logic for fixtures analytics and decisions"""
        """Build out a Pandas DataFrame table to formulate a decision on"""
        """which games are good to play, highest probability of big scores, etc"""

        logging.info('allfixtures.game_decisions() - init ' )
        self.team_h = team_h
        self.team_a = team_a
        self.h_dif = h_dif
        self.a_dif = a_dif
        self.gt = gametime
        self.hga = 1
        self.hgs = 1
        self.hgc = 1
        self.hgp = 1
        self.hga_teamname = "Team name missing"
        self.temp_idx = ""    # temp var populated by return from team_finder()
        #self.get_standings()         # allways make sure league standings is updated/current before we start

        logging.info('allfixtures.game_decisions() - Finding home team - %s' % self.team_h )
        home = self.team_finder(self.team_h)
        logging.info('allfixtures.game_decisions() - Home team tuple code - %s' % home )

        logging.info('allfixtures.game_decisions() - Finding away team - %s' % self.team_a )
        away = self.team_finder(self.team_a)
        logging.info('allfixtures.game_decisions() - Away team tuple code - %s'% away )
        ds_data_home = self.standings_extractor(home)    # uses football-data.org team ID
        ds_data_away = self.standings_extractor(away)    # ditto

        # team standings pandas DataFrame column layout
        # [ index, gametime, home_ID, home_name, away_name, away_id, table_rank_missmatch
        # goal_dif, goal_for_diff, goal_against_diff, home_win_prob, away_win_prob, calculated_weighting_rank ]

        # Each teams difficulty factor for winning this game.
        # NOTE: Raw numbers are set by the league for each game pairing. I am uniquely calculating the probability factor
        # <1 means easier to win, >1 means difficult to win, 1 = 50-50 even chance
        h_win_prob = round( abs(a_dif / h_dif),2 )
        a_win_prob = round( abs(h_dif / a_dif),2 )
        h_win = False
        a_win = False
        #
        # Compute Home Game Advantage
        # STATISTICAL model underpinning the decision making process...
        # see epldecoder WIKI.

        if h_win_prob == a_win_prob:    # 50-50 equal dificulty level
            h_win = False
            a_win = False
            self.hga = 0

        if h_win_prob > a_win_prob:    # Home team has an advantage
            h_win = True
            a_win = False
            t, h, a = self.get_standings()    # get latest standings & game stats. ONLY h is used here!
            for s in range(0, 20):    # scan 20 teams
                if h[s]['team']['id'] == home:    # looking for team id
                    self.htn = h[s]['team']['name']
                    self.hgs = h[s]['goalsFor']
                    self.hgc = h[s]['goalsAgainst']
                    self.hgp = h[s]['playedGames']

            self.hga = (self.hgs - self.hgc) / self.hgp

        if a_win_prob > h_win_prob:    # Away team has` advantage
            h_win = False
            a_win = True
            self.hga = 0

        ranking_mismatch = ds_data_home[2] - ds_data_away[2]
        goal_diff_delta = abs(ds_data_home[5] - ds_data_away[5])
        gf_delta = ds_data_home[3] - ds_data_away[3]
        if goal_diff_delta == 0:
            goal_diff_delta = 1

        # Team names dataset
        home_team = self.bootstrap.epl_team_names[self.team_h]
        away_team = self.bootstrap.epl_team_names[self.team_a]

        ga_dxa = ds_data_home[4] + ds_data_away[4]
        ga_dxb = int(allfixtures.this_event)
        ga_delta = round(abs(ga_dxa/ga_dxb))
        game_weight = abs(ranking_mismatch) * abs(goal_diff_delta) * abs(gf_delta) * ga_delta
        #game_tag = "'" + str(self.team_h) + '_vs_' + str(self.team_a) + "'"
        game_tag = str(self.team_h) + '_' + str(self.team_a)

        if self.hga > 0:
            playme = ( game_weight * self.hga ) + (( h_win_prob * ranking_mismatch ) * 10 )
        else:
            playme = game_weight + (( h_win_prob * ranking_mismatch ) * 10 )

# note: Pandas DataFrame = allfixtures.ds_df0 - allready pre-initalized as EMPYT on __init__
        ds_data0 = [[ \
                    self.gt, \
                    self.team_h, \
                    home_team, \
                    away_team, \
                    self.team_a, \
                    abs(ranking_mismatch), \
                    abs(goal_diff_delta), \
                    abs(gf_delta), \
                    ga_delta, \
                    h_win_prob, \
                    a_win_prob, \
                    h_win, \
                    self.hga, \
                    game_weight, \
                    abs(playme) ]]

        df_temp0 = pd.DataFrame(ds_data0, \
                    columns=[ \
                    'Time', 'Hid', 'Home', 'Away', 'Aid', \
                    'RankD', 'GDd', 'GFd', 'GAd', 'Hwin', \
                    'Awin', 'HomeA', 'HGA', 'Weight', 'PlayME' ], \
                    index=[game_tag] )

        allfixtures.ds_df0 = allfixtures.ds_df0.append(df_temp0)    # append this ROW of data into the DataFrame
        return

    def get_standings(self):
        """Create a full current league standings database & make avail in gloabl bootstrap instance"""
        """uses https://www.football-data.org API (my free throttled/limited API account """
        """Does not output anything. Just refreshes the BOOTSTRAP fixtures dataset."""

        connection = http.client.HTTPConnection('api.football-data.org')
        headers = { 'X-Auth-Token': '01232ee1842c428291d3a04091e25916' }              # my private API token (throtteled @ 10 calls/min)
        connection.request('GET', '/v2/competitions/PL/standings', None, headers )    # EPL standings
        t1 = json.loads(connection.getresponse().read().decode())
        logging.info('allfixtures:: get_standings() - init')
        # quickly addressible elements
        self.filters = t1['filters']
        self.competition = t1['competition']
        self.season = t1['season']
        self.standings = t1['standings']
        self.regular_season_t = self.standings[0]    # standings totals
        self.regular_season_h = self.standings[1]    # standings home
        self.regular_season_a = self.standings[2]    # standings away
        self.standings_t_table = self.regular_season_t['table']    # data
        self.standings_h_table = self.regular_season_h['table']    # data
        self.standings_a_table = self.regular_season_a['table']    # data

        self.bootstrap.standings_t = self.regular_season_t    # save standings dict as class gloabl accessor
        #print ("TOTALS:", self.standings_t_table )          # JSON dataset
        #print ("HOME_TOTALS:", json.dumps(self.regular_season_h, indent=2, sort_keys=True) )
        #print ("AWAY_TOTALS:", self.regular_season_a )
        return (self.standings_t_table, self.standings_h_table, self.standings_a_table)

    def standings_extractor(self, ts):
        """method to extract the standings details for ONE specific team"""
        """as that team is currently ranked in the overall current table"""

        self.se_ts = ts    # team I am intersted in
        logging.info('allfixtures::standings_extractor() - init %s' % self.se_ts )
        standings = []
        standings = self.bootstrap.standings_t       # BUG - assumes current week - FIX load latest league standings
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
            if stp_teamid == self.se_ts:
                #print ( "\tTeam: ", stp_team, " ", end="" )    # use EPL bootstrap team NAMES
                #print ( "Ranked: ", pos+1, " ", end="" )
                #print ( "GF: ", stp_gf, " ", end="" )
                #print ( "GA: ", stp_ga, " ", end="" )
                #print ( "GD: ", stp_gd)
                # create a tuple on the fly, with all key data science data in it
                ds_data = 'dsd_' + str(stp_teamid)
                # print ( "Building TUPLE name:", ds_data )
                ds_data = ()
                ds_data = (stp_teamid, stp_team, pos+1, stp_gf, stp_ga, stp_gd)
            else:
                pass

        return ds_data    # tuple containg data science ready data

    def team_finder(self, tf):
        """Helper moethod to decode & xref team ID's across multile API's & data services"""
        """call : method with fantasy.epl TEAM ID"""
        """Returns : football-data.org TEAM ID"""

        # we now utilize mukltiple API's as data sources & those API's do *NOT* use a
        # standardized ID_number for each team. - (must be updated @ start of each season.
        # 0 = www://football-data.org TEAM ID code - (immutable for ever)
        # 1 = www://fantasy.premierleague.com TEAM ID code - (immutable for ever)
        # 2 = www://fantasy.premierleague.com  TEAM ID index for this season (changes every season)

        # WARNING: fantasy.EPL doesnt use teamID much. it uses team index (which is int(index) in its JSON )
        # tuple: very fast but immutable : foorball-data.com-teamID, epl-teamid, bootstrap-teamid
        #
        # table delow is only relevent for 2019/2020 season
        self.teamid_xlt = ( \
                        57, 3, 1, \
                        58, 7, 2, \
                        1044, 91, 3, \
                        397, 36, 4, \
                        328, 90, 5, \
                        61, 8, 6, \
                        354, 31, 7, \
                        62, 11, 8, \
                        338, 13, 9, \
                        64, 14, 10, \
                        65, 43, 11, \
                        66, 1, 12, \
                        67, 4, 13, \
                        68, 45, 14, \
                        356, 49, 15, \
                        340, 20, 16, \
                        73, 6, 17, \
                        346, 57, 18, \
                        563, 21, 19, \
                        76, 39, 20)
        self.tf = tf
        logging.info('allfixtures::team_finder() - init %s' % self.tf )
        for tx in range (0, 59, 3):    # 20 teams x 3 tupl elements per team
            if self.teamid_xlt[tx+2] == self.tf:        # testing on fantasy.epl team ID
                a = self.teamid_xlt[tx]
                return a    # football-data_teamID, EPL_teamID
            else:
                pass    # keep looking for this team in tuple
        return
