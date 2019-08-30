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
        allfixtures.ds_df0 = pd.DataFrame(columns=[ 'Hid', 'Home', 'Aid', 'Away', 'POSid', 'GDd', 'GFd', 'GAd', 'Rank'] )
        s = requests.Session()
        user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0'}
        API_URL0 = 'https://fantasy.premierleague.com/a/login'
        API_URL1 = FPL_API_URL + 'fixtures/?event=' + self.eventnum

# WARNING: This cookie must be updated each year at the start of the season as it is changed each year.
        pl_profile_cookies = { \
                '1212166': 'eyJzIjogIld6VXNNalUyTkRBM01USmQ6MWZpdE1COjZsNkJ4bngwaGNUQjFwa3hMMnhvN2h0OGJZTSIsICJ1IjogeyJsbiI6ICJBbHBoYSIsICJmYyI6IDM5LCAiaWQiOiAyNTY0MDcxMiwgImZuIjogIkRyb2lkIn19', \
                '1995215': 'eyJzIjogIld6SXNNalUyTkRBM01USmQ6MWh5aE9BOmdLcXg0S3RkSGR5UVRXRjUwVjhxZHR4RVNTayIsICJ1IjogeyJpZCI6IDI1NjQwNzEyLCAiZm4iOiAiRHJvaWQiLCAibG4iOiAiQWxwaGEiLCAiZmMiOiA1N319', \
                '1994221': 'eyJzIjogIld6SXNOVGc0T0RnM05WMDoxaHlpdU46MlhhRDZlbkx3YU03WFdtb0tBWEhsYXlESlBnIiwgInUiOiB7ImlkIjogNTg4ODg3NSwgImZuIjogIkRhdmlkIiwgImxuIjogIkJyYWNlIiwgImZjIjogOH19', \
                '1136396': 'eyJzIjogIld6VXNOVGc0T0RnM05WMDoxZnYzYWo6WGkxd1lMMnpLeW1pbThFTTVFeGEzVFdUaWtBIiwgInUiOiB7ImxuIjogIkJyYWNlIiwgImZjIjogOCwgImlkIjogNTg4ODg3NSwgImZuIjogIkRhdmlkIn19' }

        for pl, cookie_hack in pl_profile_cookies.items():
            if pl == self.playeridnum:
                s.cookies.update({'pl_profile': cookie_hack})
                logging.info('allfixtures:: SET pl_profile cookie for userid: %s' % pl )
                logging.info('allfixtures:: SET pl_profile cookie to: %s' % cookie_hack )
                allfixtures.api_get_status = "GOODCOOKIE"
                break    # found this players cookie
            else:
                logging.info('allfixtures:: ERR userid is bad. No cookie found/set: %s' % pl )
                allfixtures.api_get_status = "FAILED"

        if allfixtures.api_get_status == "FAILED":
            return
        else:
            pass

# REST API I/O now... - this is a public API endpoint. - No AUTH needed
        rx0 = s.get( API_URL0, headers=user_agent )
        rx1 = s.get( API_URL1, headers=user_agent )
        self.auth_status = rx0.status_code
        self.gotdata_status = rx1.status_code
        logging.info('allfixtures:: - init - Logon AUTH url: %s' % rx0.url )
        logging.info('allfixtures:: - init - API data get url: %s' % rx1.url )

        rx0_auth_cookie = requests.utils.dict_from_cookiejar(s.cookies)
        logging.info('allfixtures:: AUTH login resp cookie: %s' % rx0_auth_cookie['pl_profile'] )

        if rx0.status_code != 200:    # failed to authenticate
            logging.info('allfixtures:: - init ERROR login AUTH failed with resp %s' % self.auth_status )
            return

        if rx1.status_code != 200:    # 404 API get failed
            logging.info('allfixtures:: - init ERROR API get failed with resp %s' % self.gotdata_status )
            return
        else:
            logging.info('allfixtures:: - Login AUTH success resp: %s' % self.auth_status )
            logging.info('allfixtures:: - API data GET resp is   : %s  ' % self.gotdata_status )
            # create JSON dict with players ENTRY data, plus other data thats now available
            # WARNING: This is a very large JSON data structure with stats on every squad/player in the league
            #          Dont load into memory multiple times. Best to insert into mongodb & access from there
            # EXTRACT JSON data/fields...
            # note: entry[] and player[] are not auto loaded when dataset lands (not sure why)
            t0 = json.loads(rx1.text)
            self.fixtures = t0    # entire JSON dict - process current event (could be past/present/future)
            #for XX in range (0..9):

            #print ("JSON ARRAY DUMP:", t0[0] )
            #print ("ALL FIXTURES FOR CURRENT WEEK NUM:", t0)
            #self.game_settings = t0['game_settings']
            #self.phases = t0['phases']
            #self.teams = t0['teams']                    # All details of EPL teams in Premieership league this year
            #self.elements = t0['elements']              # big data-set for every EPL squad player full details/stats
            #self.stats = t0['element_stats']              # big data-set for every EPL squad player full details/stats
            #self.element_types = t0['element_types']
        return

#######################

    def upcomming_fixtures(self, ds_yes_no):
        """Fixtures are messy in the main JSON data model"""
        """There is no simple & readily accessible database that qwuicly available."""
        """You have to build/interrogate your list of fixtures every time"""

#       This JSON structure was destroyed in the 2019/2020 season changes.
        self.datasci = ds_yes_no
        logging.info('allfixtures:: upcomming_fixtures() - init : %s' % ds_yes_no )

        tn_idx = self.bootstrap.list_epl_teams()    # build my nice helper team id/real name dict
        print ( "Show fixtures for gameweek...", self.eventnum )
        for fixture in self.fixtures:         # BROKEN by 2019/2020 JSON changes
            idx_h = int(fixture['team_h'])    # use INT to index into the team-name dict self.t that was populated in list_epl_teams()
            idx_a = int(fixture['team_a'])    # use INT to index into the team-name dict self.t that was populated in list_epl_teams()
# do some analytics on fixtures...
            print ( "GW:", fixture['event'], fixture['kickoff_time'], ") HOME:", self.bootstrap.epl_team_names[idx_h], "vs.", self.bootstrap.epl_team_names[idx_a], "(AWAY)" )
            # print ( "GW:", fixture['event'], "Day:", fixture['event_day'], "(", fixture['kickoff_time'], ") HOME:", self.epl_team_names[idx_h], "vs.", self.epl_team_names[idx_a], "AWAY" )

            #print ( "Gameplay decison: ", end="" )
            if self.datasci == 1:    # 1 = do deep datascience analytics on fixtures
                self.game_decisions(idx_h, idx_a)    # run seperately for each game match
            else:
                pass

        #print ( allfixtures.ds_df0.sort_values(by='Rank', ascending=False) )
        return

    def game_decisions(self, team_h, team_a):
        """Datascience control logic for fixtures analytics and decisions"""

        logging.info('allfixtures:: game_decisions() - init ' )
        self.team_h = team_h
        self.team_a = team_a
        self.temp_idx = ""    # temp var populated by return from team_finder()
        #self.get_standings()         # allways make sure league standings is updated/current before we start

        logging.info('allfixtures::game_decisions() - Finding home team - %s' % self.team_h )
        home = self.team_finder(self.team_h)
        logging.info('allfixtures::game_decisions() - Home team tuple code - %s' % home )

        logging.info('allfixtures::game_decisions() - Finding away team - %s' % self.team_a )
        away = self.team_finder(self.team_a)
        logging.info('allfixtures::game_decisions() - Away team tuple code - %s'% away )
        ds_data_home = self.standings_extractor(home)    # uses football-data.org team ID
        ds_data_away = self.standings_extractor(away)    # ditto
        # teamid, team_full_name, ranking_pos, gf, ga, gd)
        ranking_mismatch = ds_data_home[2] - ds_data_away[2]
        goal_diff_delta = ds_data_home[5] - ds_data_away[5]
        gf_delta = ds_data_home[3] - ds_data_away[3]

        home_team = self.bootstrap.epl_team_names[self.team_h]
        away_team = self.bootstrap.epl_team_names[self.team_a]
        ga_dxa = ds_data_home[4] + ds_data_away[4]
        ga_dxb = int(allfixtures.this_event)
        ga_delta = round(abs(ga_dxa/ga_dxb))
        game_weight = abs(ranking_mismatch) * abs(goal_diff_delta) * abs(gf_delta) * ga_delta
        #game_tag = "'" + str(self.team_h) + '_vs_' + str(self.team_a) + "'"
        game_tag = str(self.team_h) + '_' + str(self.team_a)

# note: Pandas DataFrame = allfixtures.ds_df0 - allready pre-initalized as EMPYT on __init__
        ds_data0 = [[ \
                    self.team_h, \
                    home_team, \
                    self.team_a, \
                    away_team, \
                    abs(ranking_mismatch), \
                    abs(goal_diff_delta), \
                    abs(gf_delta), \
                    ga_delta, \
                    game_weight ]]

        df_temp0 = pd.DataFrame(ds_data0, \
                    columns=[ 'Hid', 'Home', 'Aid', 'Away', 'POSid', 'GDd', 'GFd', 'GAd', 'Rank'], index=[game_tag] )

        allfixtures.ds_df0 = allfixtures.ds_df0.append(df_temp0)    # append this ROW of data into the DataFrame

        # print ("\tLogic - ", "Pos delta:", abs(ranking_mismatch), "GD delta:", abs(goal_diff_delta), "GF delta:", abs(gf_delta), "GA delta:", ga_delta, "Weighting:", game_weight )
        # setup pandas dataframe load
        # print ("\t", "[[", self.team_h, ",", home_team, ",", self.team_a, ",", away_team, ",", abs(ranking_mismatch), ",", abs(goal_diff_delta), ",",  abs(gf_delta), ",", ga_delta, ",", game_weight, "]]" )
# construct pandas dataframe
        # print ("\t", \
        #            "df0 = pd.DataFrame(data_0,", \
        #            "columns=['Hid', 'Home', 'Aid', 'Away', 'POSid', 'GDd', 'GFd', 'GAd', 'Rank'],", \
        #            "index=[", \
        #            game_tag, \
        #            "] )", \
        #            )

        # print ("\t", \
        #            "data_0 = [[", \
        #            self.team_h, ",", \
        #            home_team, ",", \
        #            self.team_a, ",", \
        #            away_team, ",", \
        #            abs(ranking_mismatch), ",", \
        #            abs(goal_diff_delta), ",", \
        #            abs(gf_delta), ",", \
        #            ga_delta, ",", \
        #            game_weight, \
        #            "]]" )

        return

    def get_standings(self):
        """Create a full current league standings database & make avail in gloabl bootstrap instance"""
        """uses https://www.football-data.org API (my free throttled/limited API account """

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
        # print ("GET_STANDINGS:", self.standings_t_table )          # JSON dataset
        #print ("REGULAR_SEASON:", self.regular_season_t )
        return

    def standings_extractor(self, ts):
        """method to extract the standings details for ONE specific team"""
        """as that team is currently ranked in the overall current table"""

        self.se_ts = ts    # team I am intersted in
        logging.info('allfixtures::standings_extractor() - init %s' % self.se_ts )
        standings = []
        standings = self.bootstrap.standings_t       # load latest league standings
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
        """Helper moethod to decode & xref team ID's across multile API's"""
        """across multiple API web services"""
        """call : method with fantas.epl TEAM ID"""
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
