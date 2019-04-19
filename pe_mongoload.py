#!/usr/bin/python3
import requests
from requests import Request, Session
from pymongo import MongoClient

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

########################################################
# this functio was cut-out of main()...
# it was an old dupe of the new class fpl_bootstrap:: that depricates it.
# it has mongoDB insert code, which the new fpl_bootstrap::: does not (yet).
# it kept for history, until MongoDB code is added to fpl_bootstrap::
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
