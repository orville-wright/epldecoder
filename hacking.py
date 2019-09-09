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

    #XREF Heat Matrix
            # setup DataFrame
            # column names = player unique id num
            #col_names = [ (priv_playerinfo.ds_df1.sort_values(by='Player', ascending=True)['Uiqid']).values ]
            #ds_hm_df0 = pd.DataFrame({'XXX': ['YES', 'YES', 'YES']} )    # shape the HEATMAP dataframe with preset columns
            #col_names = [ priv_playerinfo.ds_df1.sort_values(by='Player', ascending=True).values ]
            # rown index = opponent team names

            #ds_hm_data3 = { got_him: pd.Series(ds_hm_data0, index=team_id) }
            #hm = { got_him: pd.Series(ds_hm_data0, index=team_id) }
            #ds_hm_df2 = pd.DataFrame( data=ds_hm_data0, columns=got_him )    # shape the HEATMAP dataframe with preset columns
            #ds_hm_df5.insert(loc=0, value=ds_hm_data3 )
            #ds_hm_df1 = ds_hm_df0.insert( loc=0, column=got_him, value=ds_hm_data3 )
#            if z != 0:
                #print ( "Found in: ", z, "teams >>", tl)
#                print ( "Found in: ", tl, z, "teams")
                #print ( ds_hm_df0 )
                #print ( ds_hm_data0 )
#            else:
#                print ( "Unique - not in any opponents squad" )
                #print ( ds_hm_df0 )
                #print ( ds_hm_data0 )
#            print ( "+--------------------------------------------------------+" )
#            z = 0

        #print ( ds_hm_df5 )
        #print ( ds_hm_df5.count() )
        #print ( ds_hm_df5.sum(axis=0) )
        #print ( hm_tr_data0 )
    #hm_tr_data0 = pd.Series( [ds_hm_df5.sum(axis=0)], index='Totals' )          # count up total of each column
    #df_temp0 = pd.DataFrame(hm_tr_data0, columns=hm_tr_data0.index, index=['Totals'] )
    # df_temp9 = pd.DataFrame(hm_tr_data0, columns=col_names, index=['Totals'] )
    #df_temp0 = { hm_tr_data0 }
    #dfs = pd.Series(df_temp0, index=['Totals'] )
        #print ( df_temp9 )
        #print ( hm_tr_data0.index)
