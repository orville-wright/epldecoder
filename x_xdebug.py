#!/usr/bin/python3

##########
# DEBUG function
# currently not called my any code
#
# cycle through a list of leagues and extract the monthly standings statistics
# then insert then into the mongoDB collection

def X_my_league_stands(player_idnum, league):
    logging.info('my_league_stands(): extract standings for league: %s' % league)
    PLAYER_ENTRY = str(player_idnum)
    s1 = requests.Session()
    s1.cookies.update({'pl_profile': 'eyJzIjogIld6VXNNalUyTkRBM01USmQ6MWVOWUo4OjE1QWNaRW5EYlIwM2I4bk1HZDBqX3Z5VVk2WSIsICJ1IjogeyJsbiI6ICJBbHBoYSIsICJmYyI6IDgsICJpZCI6IDI1NjQwNzEyLCAiZm4iOiAiRHJvaWQifX0='})

    user_agent = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5;Windows NT)'}
    EXTRACT_URL = FPL_API_URL + MYTEAM + PLAYER_ENTRY

    # 1st get does the authentication, but must use the critical cookie (i.e. "pl_profile")
    # 2nd get does the real data extraction once the auth succeeds
    print ("my_league_stands(): Authenticating API to extract details of player:", PLAYER_ENTRY, "...", end="")
    resp0 = s1.get('https://fantasy.premierleague.com/a/login', headers=user_agent, auth=HTTPBasicAuth(priv_playerinfo.username, priv_playerinfo.password))
    print (resp0.status_code)

    mclient = MongoClient("mongodb://admin:sanfran1@localhost/admin")
    db = mclient.test1
    col = db.eplstand_permonth    # mongoDB collection

    print (" ")
    print ("Extract stats for all players in league:", league )           # python3 formatted

    month_code = {'1': 'Overall', '2': 'Aug', '3': 'sep', '4': 'Oct', '5': 'Nov', '6': 'Dec', '7': 'Jan', '8': 'Feb', '9': 'Mar' }

    for month in range (2, 8):           # hard coded 7 months
        # month 1=current month
        # 2=aug, 3=sept, 4=oct, 5=nov, 6=dec, 7=jan, 8=feb, 9=mar, 10=apr

        print ("\t", "Month:", month_code[str(month)], "", end="")
        # dynamically built the API url for each month
        s_month = str(month)
        LEAGUE_STATS_URL = STANDINGS_URL + league + '?phase=' + s_month + CLASSIC_PAGE

        resp2 = s1.get(LEAGUE_STATS_URL, headers=user_agent, auth=HTTPDigestAuth(priv_playerinfo.username, priv_playerinfo.password))

        # should test resp2.status_code here...
        m0 = json.loads(resp2.text)
        m1 = m0['new_entries']
        m2 = m0['league']
        m3 = m0['standings']
        m4 = m3['results']
        mcount = 0

        for results_data in m4:
            print (".", end="")
            #print ("Player:", results_data['player_name'], "Monthly rank:", results_data['rank'], "Monthly total:", results_data['total'])
            results = col.insert({ 'player_entry': results_data['entry'], 'player_name': results_data['entry_name'], 'month': month, 'league': results_data['league'], 'league_name': m2['name'], 'rank': results_data['rank'], 'month_total': results_data['total'] })
            mcount += 1
        print ("", mcount, "Players")

    return

#####
# DEBUG function
# currently not called my any code
#
# inset the data: a JSON dict and its key/value pair data into a MongoDB collection
# entry:   JSON dict
#          mongodb collection name
#
def X_dbstore_entry(m_json_dict, m_colname):
    logging.info('dbstore_enrty(): insert data into collection: %s' % m_colname )
    mclient = MongoClient("mongodb://admin:sanfran1@localhost/admin")
    db = mclient.test1
    col = db[m_colname]
    # collection = db.'m_colname'

    # cycle thought the JSON dicy key/value pairs 1-by-1 and insert them to the mongo database
    # note: there may be a smart mongo/JSON way to do this in a single operation without
    # looping though each individual dict key - (which could be slow for a very large source dict)
    #
    # note: args['bool_xray'] is a global var

    if args['bool_dbload'] is True:
        logging.info('dbstore_enrty(): cycling thru JSON dict key/values...')
        print (m_colname,)
        for key, value in m_json_dict.items():
            #print ("KEY: %s - VALUE: %s") % (key, value)
            sys.stdout.write('.')
            result = col.insert({key: value})
    else:
        logging.info('dbstore_enrty(): no DB insert requested')
    print (" ")

    # testing only
    # activated by -x arg
    if args['bool_xray'] is True:
        logging.info('dbstore_entry(): Read MongoDB collection: %s' % m_colname)
        for doc in col.find({}):
            print(doc)
    else:
        logging.info('dbstore_entry(): NO xray requested')

    return

####
# DEBUG function
# currently not called my any code
#
# mongo query
# how to extract the players name and exclude the mono unique _id field...
#     db.eplentry.findOne( { player_last_name: {$exists: true } }, { _id: 0} )
#
# a test function
# testing that mongo is working fine...
#
# This function created 500 random entries in a mongo collection (named 'reviews') in the test1 database
# and then print out the contents of the collection directly from the database

def X_mongo_1():
    logging.info('mongo_1()' )
    mclient = MongoClient("mongodb://admin:sanfran1@localhost/admin")
    db = mclient.test1
    col = db.reviews

    names = ['Kitchen','Animal','State', 'Tastey', 'Big','City','Fish', 'Pizza','Goat', 'Salty','Sandwich','Lazy', 'Fun']
    company_type = ['LLC','Inc','Company','Corporation']
    company_cuisine = ['Pizza', 'Bar Food', 'Fast Food', 'Italian', 'Mexican', 'American', 'Sushi Bar', 'Vegetarian']

    for x in xrange(1, 501):
        #result = db.reviews.insert({
        result = col.insert({
            'name' : names[randint(0, (len(names)-1))] + ' ' + names[randint(0, (len(names)-1))]  + ' ' + company_type[randint(0, (len(company_type)-1))],
            'rating' : randint(1, 5),
            'cuisine' : company_cuisine[randint(0, (len(company_cuisine)-1))]
            })

        #print('Created {0} of 100 as {1}'.format(x,result))
    for doc in db.reviews.find({}):
        print(doc)

    return
