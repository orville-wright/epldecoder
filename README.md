# epldecoder
EPL Fantasy Football website bootstrap API decoder
English Premier League Data Analytics AI platform

Primary use case: As a companion to EPL Fantasy Football League played by 5,000,000+ users worldwide via the web app at the Barclay's EPL website: http://www.premierleague.com/en-gb.html and on mobile devices.

v2.0 of the project is focused on the following priorities...

ETL (Extract, Translate, Load)

Extracting data via scraping raw data from: http://www.premierleague.com/en-gb.html

Investigating any available REST API's provided by EPL website.

Prototyping & validating the data scraping technology & toolset

Initially using SCRAPY (http://doc.scrapy.org/en/latest/intro/overview.html)

Translating the web data into a format that is more usable

Iesting Data Models for key datasets

Loading data in a NoSQL MongoDB database

Make all data available, espeically full historical data in non-agrigate form

Augmenting the dataset with additional info not currently computed or offered

Notes:
Eventually the project will provide full access to the dataset via a service to EPL Fantasty footbal players via a website and a mobile app (tablet and phone, iOS and Android).

Additional analytical data sets will be created within MonggoDB that are not available on the current website: http://www.premierleague.com/en-gb.html making deeper team & player analysis possible. and therefore, better team/player decisions possible.

Also, the MongoDB data source will be use to drive rich analytical charts that are not available on http://www.premierleague.com/en-gb.html, never were available and are very much needed by the 5,000,000 users of the Barclays EPL website & App.

These charts can graqph info based on the standard dataset from the EPL website as well as graph additional advance charts.

That EPL website used to provided a set of charts to users but this service was removed and discontinued. Fantasy Footbal players no longer have any charts/grahing service to suppor their team decisions

An AI enging will also be offered. This engine will operate under a set of personalizable & tunable rules that "you" can define and control. The AI will...

Scan for injury rumors, news and info then compoute player not-starting probabilities
Scan for hot & cold trends
Extraqpolate scoring runs and trends and predict possible 'Black Swan' events
Compute best captain probabilities
Compute best & worst games to play/avoid.
Compute highest scoring probability of each game and player scoring probabilities
Propose possible teams, transfers and team configs
...etc, etc

More to come. ~Orville

