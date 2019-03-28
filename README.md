# epldecoder
EPL Fantasy Football website bootstrap API decoder
English Premier League Data Analytics AI platform

Primary use case: As a companion to EPL Fantasy Football League played by 5,000,000+ users worldwide via the web app at the Barclay's EPL website: http://www.premierleague.com/en-gb.html and on mobile devices.

v2.0 of the project is focused on the following priorities...

Live mem JSON ETL (Extract, Translate, Load), rather than save data to files & post processing files.

JSON data feed via API interface. No scraping raw data from: http://www.premierleague.com/en-gb.html.

Understanding all available REST API's provided by EPL website (private API - not public disclosed).

Prototyping & validating the data technolog, toolset & overall JSON data structure.

Processing live API extracted JSON datasets in memory. (moving away from flat file processing).

Continue to push data into MongoDB database to augment logic processing where key data/fields/structures are not preseint in the native JSON dataset that is extracted via the API. Augmenting the dataset with additional info not currently computed or offered.

Make data available, espeically full historical data in non-agrigate form

Notes:
Augment the game decision making process with additional analytical data sets that are sources from other locations. These will be created & stored within a MonggoDB and cross-referenced with the basic game data-set. Today, this is not easy to do via the current game website: http://www.premierleague.com/en-gb.html. Doing this makes deeper team & player analysis more possible (but more complex). and therefore, better team/player decisions are possible. Many of these data sets come from non EPL websites. e.g. FIFA, gambliing sites, footbal stats sites etc.

Also, the MongoDB data source will be used to drive richer analytical charts that are not available on http://www.premierleague.com/en-gb.html, never were available and are very much needed by the 5,000,000+ users of the Barclays EPL website & App.

These charts can graph info based on the standard dataset from the EPL website as well as graph additional advance charts.

That EPL website used to provided a set of charts to users but this service was removed and discontinued. Fantasy Footbal players no longer have any charts/grahing service to suppor their team decisions

A ML/AI engine will also be built and offerd to indiviudal players. A player will be able to teach the ML/AI (via a web app/mopbile app) to emulate his/her individual analytical team decison making style. Thereby automatiing the mundane process of choosinig a squad by churning through pages of weekly data & relying too much on fuzzy personal logic, gut-feel, intution, rumors and voodo on what squad to pick & set-up. This will also allow EPL Fantasy Footbal players to run 1000's of possible permutatioins against potential squads (e.g., who to captain, who to vice-captian, whehn to play a wild card, what to play special options etc...all before the game day cut-off time. 
The ML/AI engine will operate under a set of personalizable & tunable rules that "you" can define and control and do things like ...

Scan for injury rumors, news and info then compoute player not-starting probabilities
Scan for hot & cold trends
Extraqpolate scoring runs and trends and predict possible 'Black Swan' events
Compute best captain probabilities
Compute best & worst games to play/avoid.
Compute highest scoring probability of each game and player scoring probabilities
Propose possible teams, transfers and team configs
...etc, etc

More to come. ~Orville

