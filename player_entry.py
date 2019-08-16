#!/usr/bin/python3
import requests
from requests import Request, Session
import json
import logging

# FPL_API_URL = "https://fantasy.premierleague.com/drf/"
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

    def __init__(self, playeridnum):
        self.playeridnum = str(playeridnum)
        logging.info('player_entry:: - init class instance as player: %s' % self.playeridnum )
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

# depricated as of 2019/2020 season
#            self.entry = s2['entry']
#            self.leagues = s2['leagues']
#            self.cleagues = self.leagues['classic']
#            self.h2hleagues = self.leagues['h2h']
#            self.cupleagues = self.leagues['cup']
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
        return  self.entryid

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
        """Cycle thru all my Classic Leagues & print them"""
        """This will not access/print GLOBAL leagues (e.g. EPL Team leagues, Country leagues etc)"""

        # logging.info('player_entry:: my_entry_cleagues(): - Init method. scan league: %s' % this_league )
        #print ( "Team name: %s" % self.entry['name'] )
        #print (self.entry['name'], "plays in %s leagues" % len(self.cleagues))
        p = 1
        for v in self.cleagues:
            print ("", p, "League ID: %s %s - I am ranked: %s" % (v['id'], v['name'], v['entry_rank']))
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
