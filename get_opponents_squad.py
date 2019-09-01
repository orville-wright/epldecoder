#!/usr/bin/python3
import requests
from requests import Request, Session
from requests.auth import HTTPBasicAuth
from requests.auth import HTTPDigestAuth
import json
import logging

FPL_API_URL = "https://fantasy.premierleague.com/drf/"
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

####
# Get the full squad player/position list for any team
#
# This function extracts team data from a strict API URL
# eg:  https://fantasy.premierleague.com/a/team/1980723/event/23
#      not the public ENTRY data set (squad data is not in that data set)

# WARNINGS:
# 1. could be Network/API expensive if called recurrsively on multiple players/oponents
#    becasue a full html JSON API extract must be done per player
# 2. Currently considers "you" as an opponent
#    (i.e no checks to exclude "you". need smarter way to know this)
#
class get_opponents_squad:
    """Base class to access any player/opponent team sqaud list & data """
    """note: can only access historical squad data from last game back (which is public data) """
    """must be called with a sucessfully populated instance of Player_ENTRY() """
    bst_inst = ""
    api_get_status = "PRIVATE"

    def __init__(self, player_idnum, pe_live_inst, event_id, my_priv_data, bootstrap):
        # Base bootstrap API calls (..premierleague.com/drf/...) dont require authentication
        # but, if you want explict details about a team, you must authenticate your API call

        PLAYER_ENTRY = str(player_idnum)
        self.bst_inst = bootstrap
        self.pe_live_inst = pe_live_inst              # player ENTRY instance for this player - critical for de-ref'ing data
        self.username = my_priv_data.username      # username from global class var
        self.password = my_priv_data.password      # password from global class var
        self.playeridnum = player_idnum
        get_opponents_squad.bst_inst = self.bst_inst
#        self.password = priv_playerinfo.password      # password from global class var

        logging.info('get_opponents_squad:: Init class. Auth API get priv player data for: %s' % PLAYER_ENTRY )
        s1 = requests.Session()
        user_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0'}
        API_URL0 = 'https://fantasy.premierleague.com/a/login/'
        API_URL1 = FPL_API_URL + MYTEAM + str(self.playeridnum) + '/'
        EXTRACT_URL = FPL_API_URL + ENTRY + PLAYER_ENTRY + "/event/" + str(event_id) + "/picks/"

# new v3.0 cookie hack
        logging.info('get_opponents_squad:: EXTRACT saved cookie from bootstrap for playerid: %s' % self.playeridnum )
        logging.info('get_opponents_squad:: SET cookie: %s' % self.bootstrap.my_cookie )
        s1.cookies.update({'pl_profile': self.bst_inst.my_cookie})

# Do REST API I/O now...
# 1st get authenticates, but must use critical cookie (i.e. "pl_profile")
# 2nd get does the data extraction if auth succeeds - failure = all JSON dicts/fields are empty
        resp3 = s1.get('https://fantasy.premierleague.com/a/login', headers=user_agent, auth=HTTPBasicAuth(self.username, self.password))
        resp4 = s1.get(EXTRACT_URL, headers=user_agent, auth=HTTPDigestAuth(self.username, self.password))
        self.auth_status = resp3.status_code                   # class gloabl var
        self.gotdata_status = resp4.status_code                # class global var

        if resp3.status_code == 200:                           # initial username/password AUTH
            logging.info('get_opponents_squad(): - Init - Auth succeess for player: %s' % PLAYER_ENTRY )
            logging.info('get_opponents_squad(): - Init class - get URL: %s' % EXTRACT_URL )
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
        self.t3 = self.t0['picks']    # [] has 15 sub-elements of all 15 players in your current squad
                                      # but no nice human readable data. its All refs to data in other []
        return                        # instantiation done & succeded


# Class methods

    def opp_squad_captain(self):
        """extract info about the captain of this oponents squad"""
        """does work on someone eleses squad other than yours."""

        logging.info('get_opponents_squad.opp_squad_captain() - Enter' )
        t7 = []                                           # temp working dict to hold this users squad players
        oppt_tname = self.pe_live_inst.my_teamname()      # accessor to resolve additional ref'd player ENTRY data
        pe_playerid = self.pe_live_inst.owner_player_id
        for player_num in range (0, 15):                  # note: hard-coded 14 players in a team
            t7 = self.t3[player_num]                      # scanning each squad player details (not likley to ever change)
            if t7['is_captain'] is False:
                pass
            elif t7['is_captain'] is True:                    # is this squad player the CAPTAIN?:
                find_me = t7['element']                       # get unique player ID for squad player
                capt_name = self.bst_inst.whois_element(find_me)  # scan main payer data set - each time (!!slow-ish ~600 entities )
                capt_gw_points = self.bst_inst.element_gw_points(find_me)    # raw points exlcuding bonus/multipliers/deductions
                # print ( pe_playerid, "(", end="" )
                print ( "Team:", oppt_tname, end="" )
                print ( " - Captain:", t7['element'], \
                        "@ pos:", t7['position'], \
                        "-", capt_name, end="" )
                print ( " (gameweek points:", capt_gw_points, end="" )
                print ( ")" )

                logging.info('get_opponents_squad.opp_squad_captain() - found captain - quick exit after %s loops' % player_num )
                return                                            # exit as soon as captain is located

        print ( "Failed to locate CAPTAIN in squad", self.t1['entry'], oppt_tname )
        logging.info('get_opponents_squad.opp_squad_captain() - Failed to locate captain with element ID: %s' % find_me )
        return

        #!! needs to be fast by re-using player_entry inst

    def opp_sq_findplayer(self, f_playerid):
        """Scan a players ENTRY and searchs his current squad for a specific player ID"""

        fp_id = int(f_playerid)                           # must use INT for tests
        oppt_tname = self.pe_live_inst.my_teamname()      # accessor to resolve additional ref'd player ENTRY data
        p_name = self.bst_inst.whois_element(fp_id)       # scans main data set - each time (!!slow-ish ~600 entities )
        t7 = []                                           # temp working dict to hold this users squad players
        for player_num in range (0, 15):                  # note: hard-coded 14 players in a team
            t7 = self.t3[player_num]                      # scanning each squad player details (not likley to ever change)
            if t7['element'] == fp_id:
                # TODO: load results into dict & sort by total points, then print in desc order
                # print ("Team:", self.t1['entry'], \
                print ( "Team:", oppt_tname, \
                        #"- Week:", self.t2['id'], \
                        "- FOUND:", t7['element'], \
                        "**", p_name, \
                        "@ pos:", t7['position'] )
                logging.info('get_opponents_squad:: opp_sq_findplayer() - found player - quick exit after %s loops' % player_num )
                return
            else:
                #print ( ".", end="" )
                pass

#        print ( "Team:", self.t1['entry'], \
        print ( "Team:", oppt_tname, \
                #"- Week:", self.t2['id'], \
                "- NOT IN this squad" )
                #, fp_id, \
                #p_name )
        return

    def got_player(self, f_playerid):
        """Scan a players ENTRY and report back some info"""

        fp_id = int(f_playerid)
        for player_num in range (0, 15):
            t7 = self.t3[player_num]
            if t7['element'] == fp_id:
                return 1    # found player in opponents squad
            else:
                pass        # keep scanning...

        return 0            # did not find player in opponents squad

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
