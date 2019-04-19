# epldecoder
- (this source doc is formatted in Guthub Markup lang)

EPL Fantasy Football website bootstrap API decoder
English Premier League Data Analytics AI platform

Primary use case: As a companion to EPL Fantasy Football League played by 5,000,000+ users worldwide via the web app at the Barclay's EPL website: http://www.premierleague.com/en-gb.html and on mobile devices.

v2.0 of the project is focused on the following priorities...

1. Live mem JSON ETL (Extract, Translate, Load), rather than save data to files & post processing files.
2. JSON data feed via API interface. No scraping raw data from: http://www.premierleague.com/en-gb.html.
3. Understanding all available REST API's provided by EPL website (private API - not publicly documented by EPL).
4. Prototyping & validating the data technology, toolset & overall JSON data structure accessors.
5. Processing live API extracted JSON datasets in memory. (moving away from flat file processing).
6. Push data into MongoDB database.
7. Augment game decision making logic where key data/fields/structures are not present in the native game JSON dataset.
8. Augmenting the dataset with additional info not currently computed or offered.
9. Make core game data set available, especially full historical data in non-aggregate form

How to run
=================================
## usage:
   epl_bootstrap.py [-h] [-d] [-l LEAGUE] [-p PLAYER] [-q QUERY] [-r] [-v] [-x] -u USERNAME -c PASSWORD [-g GAMEWEEK]

**optional arguments:**
- -c PASSWORD, --password PASSWORD  password for accessing EPL website
- -d, --dbload                      save JSON data into mongodb
- -g GAMEWEEK, --gameweek GAMEWEEK  game week to analyze
- -h, --help                        show this help message and exit
- -l LEAGUE, --league LEAGUE        league entry id - (a league that you want to evaluate)
- -p PLAYER, --player PLAYER        team player id - (a valid user ID registered in the EPL websit)
- -q QUERY, --query QUERY           squad player id - (a valid selectable squad player...eg. Harry Kane's player code)
- -r, --recleague                   recursive league details - (scan every league you are registered in)
- -u USERNAME, --username USERNAME  a valid username for accessing EPL website
- -v, --verbose                     verbose error logging
- -x, --xray                        dump out some raw JSON data dicts & structures

How to find some of the **critical EPL game id's** that are needed for cmd line options...

#
**For example...**
- Username & Password are required
- Player id is required
- league id is optional


#
**Player_ID** - required
>You *must* know your *Player id* (or a player you want work with) from the real EPL website game: http://www.premierleague.com

To find this number...
1. Log on the Fantasy football website game
2. Click on the 'Points' menu option
3. Look up at the browser URL bar. You will see a URL like this...https://fantasy.premierleague.com/a/team/7766554/event/34
4. Your player ID is the number after the word 'team'. e.g. the number '7766554'


>To lookup the player ID of some other game opponent/user, you need to do this...
1. Click on the 'Leagues' menu option
2. Select a league that has an opponents team in it that you are interested in
3. Look up at the browser URL bar. Yo will see a URL like this...https://fantasy.premierleague.com/a/team/33221100/event/34
4. The players ID is the number after the word 'team'. e.g the number '33221100'


#
**League_ID** - optional

To find this number...
1. Click on the "Leagues" menu option
2. Select a league that you are interested in
3. Look up at the browser URL bar. You will see a URL like this...https://fantasy.premierleague.com/a/leagues/standings/255552/classic
4. The league ID is the number after the word 'standings'. e.g. the number '255552'



Notes:
=================================
The goal is to augment the game decision making process with additional analytical data sets that are sources from other locations. These will be created & stored within a MongoDB and cross-referenced with the basic game data-set. Today, this is not easy to do via the current game website: http://www.premierleague.com/en-gb.html. Doing this makes deeper team & player analysis more possible (but more complex). and therefore, better team/player decisions are possible. Many of these data sets come from non EPL websites. e.g. FIFA, gambling sites, football stats sites etc.

Also, the MongoDB data source will be used to drive richer analytical charts that are not available on http://www.premierleague.com/en-gb.html, never were available and are very much needed by the 5,000,000+ users of the Barclays EPL website & App.

These charts can graph info based on the standard dataset from the EPL website as well as graph additional advance charts.

That EPL website used to provided a set of charts to users but this service was removed and discontinued. Fantasy Football players no longer have any charts/graphing service to support their team decisions

A ML/AI engine will also be built and offered to individual players. A player will be able to teach the ML/AI (via a web app/mobile app) to emulate his/her individual analytical team decision making style. Thereby automating the mundane process of choosing a squad by churning through pages of weekly data & relying too much on fuzzy personal logic, gut-feel, intuition, rumors and voodoo on what squad to pick & set-up. This will also allow EPL Fantasy Football players to run 1000's of possible permutations against potential squads (e.g., who to captain, who to vice-captain, when to play a wild card, what to play special options etc...all before the game day cut-off time.
The ML/AI engine will operate under a set of personalize-able & tunable rules that "you" can define and control and do things like ...

- Scan for injury rumors, news and info then compute player not-starting probabilities
- Scan for hot & cold trends
- Extrapolate scoring runs and trends and predict possible 'Black Swan' events
- Compute best captain probabilities
- Compute best & worst games to play/avoid.
- Compute highest scoring probability of each game and player scoring probabilities
- Propose possible teams, transfers and team configs

...etc, etc

#
More to come. ~Orville
