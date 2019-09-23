#!/usr/bin/python3
import requests
from requests import Request, Session
import json
import logging
import pandas as pd

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

############################################
# todo: add a method that prints a list of every league this player
#       is enrolled in. Since its only held in the ENTRY data struct.
#
class player_entry:
    """Base class for an OPPONENT (you/anyone) and your base EPL game ENTRY data set"""
    """This works for any valid EPL player/opponent ID in the league"""
    """but can only acesses the public data set (i.e. not current squad info)"""

    current_event = ""
    owner_player_id = ""    # global attribute. Which player owns this player-entry instance
    ds_df_pe0 = ""          # Data science DATA FRAME 0  (fixtures)

    def __init__(self, playeridnum):
        self.playeridnum = str(playeridnum)
        player_entry.owner_player_id = self.playeridnum
        logging.info('player_entry:: - init class instance as player: %s' % self.playeridnum )
        player_entry.ds_df_pe0 = pd.DataFrame(columns=[ 'Index', 'League_name', 'Lid', 'Crank', 'Lrank', 'Moved', 'levelup' ] )

        EXTRACT_URL = FPL_API_URL + ENTRY + self.playeridnum + '/'

        s = requests.Session()
        rx = s.get(EXTRACT_URL)    # basic non-authenticated API request on a player ENTRY
        self.player_exists = rx.status_code
        logging.info('player_entry:: - API url: %s' % rx.url )

        if rx.status_code != 200:    # failed to access public URL for player number
            logging.info('player_entry:: - ERROR GET failed for player %s' % self.playeridnum )
            logging.info('player_entry:: - ERROR GET response code is %s' % self.player_exists )
            return
        else:
            logging.info('player_entry:: - init API GET response code was %s' % self.player_exists )
            # create JSON dict with players ENTRY data, plus other data thats now available
            s2 = json.loads(rx.text)
#            print (s2)
            self.entry = s2
            self.entryid = s2['id']
            self.current_event = s2['current_event']
            self.leagues = s2['leagues']
            self.cleagues = self.leagues['classic']
            self.h2hleagues = self.leagues['h2h']
            player_entry.current_event = self.current_event
        return

    def my_name(self):
        """Get the real human readable first/last name of this person"""
        """Based on the EPL game ENTRY ID number"""

        logging.info('player_entry:: my_name() - Init method' )
        # print ( self.entry['player_first_name'], self.entry['player_last_name'], end="" )
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

    def my_overall_points(self):
        """Get my teams overall points total"""

        logging.info( 'player_entry:: my_overall_points() - Init method' )
        return self.entry['summary_overall_points']

    def my_event_points(self):
        """Get my teams points from the very last game"""

        logging.info( 'player_entry:: my_event_points() - Init method' )
        return self.entry['summary_event_points']

    def my_entry_cleagues(self):    # list of all CLASSIC leagues player is entered in
        """Cycle thru all my Classic Leagues populate data science dataframe"""

        logging.info('player_entry.my_entry_cleagues(): - Init method. scan %s leagues...' % len(self.cleagues) )
        #print ( "Team name: %s" % self.entry['name'] )
        #print (self.entry['name'], "plays in %s leagues" % len(self.cleagues))
        p = 1
        for v in self.cleagues:
            logging.info('player_entry.my_entry_cleagues(): scan league %s...' % p )
            # note: Pandas DataFrame = allfixtures.ds_df0 - allready pre-initalized as EMPYT on __init__
            lrank = v['entry_last_rank']
            crank = v['entry_rank']
            moved =  lrank - crank
            # TODO: add %moved here. (need ot extract total num of players in tis leage 1st)

            if moved == 0:
                levelup = "="
            elif lrank > crank:
                levelup = "+"
            else:
                levelup = "-"

            ds_data0 = [[ \
                        p, \
                        v['name'], \
                        v['id'], \
                        v['entry_rank'], \
                        v['entry_last_rank'],
                        moved, \
                        levelup ]]

            df_temp0 = pd.DataFrame(ds_data0, \
                        columns=[ 'Index', 'League_name', 'Lid', 'Crank', 'Lrank', 'Moved', 'levelup' ], index=[p] )

            player_entry.ds_df_pe0 = player_entry.ds_df_pe0.append(df_temp0)    # append this ROW of data into the DataFrame
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
