#!/usr/bin/python3

# import pdb; pdb.set_trace()

# I cant recall what this section is supposed to do
# This is cool code, but its very complicated & doesnt work properly from a results/output perspective.
#if rleague is True:    # recursively list league details for player (all players in this league and leaderboard for this league)
#    print ( "### doing rleague... " )
#    p = {}             # working dict holds list of player ENTRY instance pointers
#    for x in fav_league.results:                    # order is random, not guaranteed to == source order
#        p[x['entry']] = player_entry(x['entry'])    # key = playerid, data = Entry instance pointer for playerid
#        for y,z in p.items():
#            z.my_teamname()
#            print ( " (", end="" )
#            z.my_name()
#            print ( ")" )
            #z.my_entry_cleagues()
            #z.allmy_cl_lboard(fav_league)
#            print ( "========================================================" )


#for rank,opp_id in fav_league.cl_op_list.items():
#    x = player_entry(opp_id)
#    print ( "Team ID: ", x.my_id(), " Team name: ", x.my_teamname(), " Owner: ", x.my_name() )

#fpl_myteam_get(this_player)   # currently hard-coded player ID
#bootstrap.list_epl_teams()


    # Pandas & Numpy select/query hacking...
    #print ( player_entry.ds_df_pe0.query( ' Lid == 479703 ' ) )    # only do after fixtures datascience dataframe has been built
    #print ( allfixtures.ds_df0[(allfixtures.ds_df0['Rank'] > 1000) ] )

#    pa =  league_details.ds_df_ld0[(league_details.ds_df_ld0['Rank'] == 1) ]
#    pd =  pa.Total.iloc[0]
#    pb =  pa[ (pa['Rank'] == 1) ]
#    pc =  pb.Total.iloc[0]
#    pe = league_details.ds_df_ld0['Total'].to_numpy()

    #pb.index.name = 'i'
    # pb = pb.drop('Rank', axis=1)
    # pa.to_numpy()

#    print ( "TO_NUMPY:", pa.to_numpy() )
#    print ( " " )
#    print ( "PANDAS DF select:", pa['Total'] )
    #px = pb['Total']
    #print ( "PX[1]:", px.iloc[0] )
#    print ( "Pa:", pa )
#    print ( "Pb", pb )
#    print ( "Pc:", pc )
#    print ( "Pd:", pd )
#    print ( "Pe:", pe )

    #print ( league_details.ds_df_ld0.assign(xxx=pa['Total'] + 1000 ) )
#    print ( league_details.ds_df_ld0.assign(xxx=league_details.ds_df_ld0['Total'] - pc ) )

    # pa.drop('Rank', axis=1)    # this works
    #print ( "PANDAS:", pa['Total'].drop('idx', axis=1) )
