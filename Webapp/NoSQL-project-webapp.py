import streamlit as st
from pymongo import MongoClient
import pandas as pd
import numpy as np
import plotly_express as px
import plotly.graph_objects as go
import copy
import json
import re
import time
import pycountry
import os.path

st.title('Projet GDELT')

#########################################################################
#############################    Functions    ###########################
#########################################################################

def connect_mongo(collection_name):

    client = MongoClient("mongodb://gdeltuser:gdeltpass@172.31.24.60:27017,172.31.28.231:27017,172.31.25.118:27017/gdelt." + collection_name + "?replicaSet=rsGdelt", readPreference='primaryPreferred')

    db = client['gdelt']
    collection = db[collection_name]
    return db, collection

def read_mongo(collection, query={}, no_id=True):
    """ Read from Mongo and Store into DataFrame """

    # Make a query to the specific DB and Collection
    cursor = collection.find(query)

    # Expand the cursor and construct the DataFrame
    df =  pd.DataFrame(list(cursor))

    # Delete the _id
    if no_id:
        del df['_id']

    return df

def iso(country):
    pays = pycountry.countries.get(alpha_2=country.upper())
    if pays is not None:
        if country.upper() != 'RS':
            return pays.alpha_3
        else:
            return 'RUS'
    else:
        return ''

#########################################################################
#############################    Queries    ###########################
#########################################################################
def query1(year="2019", month="[0-9][0-9]", day="[0-9][0-9]", country="\w", language="\w"):
    _, collection_q1 = connect_mongo('query1')
    if type(month) == list :
        month = "|".join(month)
    if type(day) == list :
        day = "|".join(day)
    query1_params = {"jour": {"$regex": year + month + day}, "pays": {"$regex": country}, "langue": {"$regex": language}}
    df_q1 = read_mongo(collection_q1, query1_params)
    return df_q1

def query2(source, year="2019", month ="[0-9][0-9]" , day = "[0-9][0-9]") :
    db, collection = connect_mongo('query2')
    if type(month) == list :
        month = "|".join(month)
    if type(day) == list :
        day = "|".join(day)
    query2_params =  {"ActionGeo_CountryCode": source, "Year": year, "Month" : {"$regex": month}, "Day": {"$regex":day}}
    df_q2 = read_mongo(collection, query2_params)
    df_q2 = df_q2.sort_values(by = "numMentions", ascending = False)
    return df_q2

def query3(source, year="2019", month ="[0-9][0-9]" , day = "[0-9][0-9]") :
    db, collection = connect_mongo('query3')
    if type(month) == list :
        month = "|".join(month)
    if type(day) == list :
        day = "|".join(day)
    query3_params =  {'SourceCommonName':source, "Year": year, "Month" : {"$regex": month}, "Day": {"$regex":day}}
    df_q3 = read_mongo(collection, query3_params)
    return df_q3

def query4(country1, country2, year="2019", month="[0-9][0-9]", day="[0-9][0-9]"):
    db, collection = connect_mongo('query4')
    if type(month) == list :
        month = "|".join(month)
    if type(day) == list :
        day = "|".join(day)
    query4_params = {'Actor1Geo_CountryCode': country1, 'Actor2Geo_CountryCode': country2, "Year": year,
                     "Month": {"$regex": month}, "Day": {"$regex": day}}

    df_q4 = read_mongo(collection, query4_params, no_id=False)
    return df_q4
#########################################################################
###########################    Visualization    #########################
#########################################################################

navigation = st.sidebar.radio("Navigation",('Home','Question 1', 'Question 2','Question 3', 'Question 4'))

if navigation=='Home':
    st.markdown(r'''
    ------------------------
    # Intro
    ------------------------

    *" The Global Database of Events, Language, and Tone (GDELT), est une initiative pour construire un catalogue de comportements et de croyances sociales à travers le monde, reliant chaque personne, organisation, lieu, dénombrement, thème, source d’information, et événement à travers la planète en un seul réseau massif qui capture ce qui se passe dans le monde, le contexte, les implications ainsi que la perception des gens sur chaque jour".*

    Cette base de données a eu beaucoup d’utilisations, pour mieux comprendre l’évolution et l’impact de la crise financière du 2008 (Bayesian dynamic financial networks with time-varying predictors) ou analyser l’évolution des relations entre des pays impliquées dans des conflits (Massive Media Event Data Analysis to Assess World-Wide Political Conflict and Instability ).

    L’objectif du projet est de concevoir un système qui permet d’analyser le jeu de donnees GDELT et ses sources de donnees.

    ------------------------
    # Objectif
    ------------------------

    L’objectif de ce projet est de proposer un système de stockage distribué, résilient et performant sur AWS pour repondre aux question suivantes:
    * afficher le nombre d’articles/évènements qu’il y a eu pour chaque triplet (jour, pays de l’évènement, langue de l’article).
    * pour un pays donné en paramètre, affichez les évènements qui y ont eu place triées par le nombre de mentions (tri décroissant); permettez une agrégation par jour/mois/année
    * pour une source de donnés passée en paramètre (gkg.SourceCommonName) affichez les thèmes, personnes, lieux dont les articles de cette sources parlent ainsi que le le nombre d’articles et le ton moyen des articles (pour chaque thème/personne/lieu); permettez une agrégation par jour/mois/année.
    * dresser la cartographie des relations entre les pays d’après le ton des articles : pour chaque paire (pays1, pays2), calculer le nombre d’article, le ton moyen (aggrégations sur Année/Mois/Jour, filtrage par pays ou carré de coordonnées)

    ''')

elif navigation=='Question 1':

    st.markdown(
        "Afficher le nombre d’articles/évènements qu’il y a eu pour chaque triplet (jour, pays de l’évènement, langue de l’article).")

    month1 = st.sidebar.multiselect("Mois :", ["01","02","03", "04","05","06","07","08","09","10","11","12"])
    day1 = st.sidebar.multiselect("Jour :", ["01","02","03", "04","05","06","07","08","09","10","11","12",
                                          "13","14","15", "16","17","18","19","20","21","22","23","24", "25","26","27","28", "29", "30"])

    year1 = st.sidebar.selectbox('Year', ['2019', '2018'])
    country1 = st.sidebar.text_input("Country")
    language1 = st.sidebar.text_input("language")

    df_q1 = query1(year=year1, month=month1, day=day1, country=country1, language=language1)

    df_q1['iso']=df_q1['pays'].apply(iso)

    df_q1_agg_country = df_q1.groupby("iso").sum().reset_index()
    df_q1_agg_lang = df_q1.groupby("langue").sum().reset_index()

    df_q1_agg_country['Couverture médiatique'] = df_q1_agg_country.numArticles / df_q1_agg_country.numEvent

    st.dataframe(df_q1)

    if country1 != "" and language1 != "":
        st.markdown("Nombre d'articles selon le nombre d'événement")
        fig = px.scatter(df_q1, x="numArticles", y="numEvent")
        st.plotly_chart(fig)

    if country1 == "":
        st.markdown("**Couverture médiatique:**")
        fig = px.choropleth(df_q1_agg_country, locations="iso", color="Couverture médiatique",
                            range_color=[4.5,7], color_continuous_scale="RdYlGn")
        st.plotly_chart(fig)

        st.markdown("**Top 10 pays:**")
        fig = px.bar(df_q1_agg_country[df_q1_agg_country['iso']!=''].sort_values("numArticles", ascending=False)[:10], x="iso", y="numArticles")
        st.plotly_chart(fig)

    st.markdown("**Top 10 langues:**")
    fig = px.bar(df_q1_agg_lang.sort_values("numArticles", ascending=False)[:10], x='langue', y='numArticles')
    st.plotly_chart(fig)


elif navigation=='Question 2':

    st.markdown("Pour un pays donné en paramètre, affichez les évènements qui y ont eu place triées par le nombre de mentions (tri décroissant); permettez une agrégation par jour/mois/année")
    source = st.sidebar.text_input('Pays :', "FR")
    graph = st.sidebar.checkbox("Afficher graphiques",False)
    year = st.sidebar.selectbox("Année :", ["2019","2018"])
    month = st.sidebar.multiselect("Mois :", ["01","02","03", "04","05","06","07","08","09","10","11","12"])
    day = st.sidebar.multiselect("Jour :", ["01","02","03", "04","05","06","07","08","09","10","11","12",
                                          "13","14","15", "16","17","18","19","20","21","22","23","24", "25","26","27","28", "29", "30"])

    if graph :
        db, collection = connect_mongo('query2')
        df_q2_temps = read_mongo(collection, {"Year": year, "Month": {"$regex" : "01|02|03"}})
        df = df_q2_temps.groupby(["ActionGeo_CountryCode","Month"]).agg({"numMentions":"sum"}).reset_index()
        df['iso']=df['ActionGeo_CountryCode'].apply(iso)

    #source = st.sidebar.selectbox('Pays :', ["US", "FR", "EN"])
    df_q2 = query2(source, year=year, month=month, day=day).copy()
    st.dataframe(df_q2)
    #df = px.data.gapminder()


    #df = df_q2.groupby(["ActionGeo_CountryCode","Month"]).agg({"numMentions":"sum"}).reset_index()
    if graph :
        st.title("Pour aller plus loin ... ")
        fig = px.choropleth(df, locations="iso", color="numMentions", animation_frame="Month", range_color=[0,2000], width=800, height=800)
        st.plotly_chart(fig)


elif navigation=='Question 3':

    st.markdown('Pour une source de donnés passée en paramètre, affichez les thèmes, personnes, lieux dont les articles de cette source parlent ainsi que le nombre d’articles et le ton moyen des articles (pour chaque thème/personne/lieu); permettez une agrégation par jour/mois/année.')

    source = st.sidebar.text_input('Source name','lemonde.fr')
    month = st.sidebar.multiselect("Month", ["01","02","03", "04","05","06","07","08","09","10","11","12"])
    day = st.sidebar.multiselect("Day", ["01","02","03", "04","05","06","07","08","09","10","11","12",
                                      "13","14","15", "16","17","18","19","20","21","22","23","24",
                                      "25","26","27","28", "29", "30"])

    year = st.sidebar.selectbox('Year', ['2019','2018'])

    df_q3 = query3(source, year=year, month = month , day = day)

    df_themes = df_q3.set_index('GKGRECORDID').join(df_q3.set_index('GKGRECORDID').Themes.apply(pd.Series).stack().reset_index(level=0).rename(columns={0:'Theme'}).set_index('GKGRECORDID')).reset_index()
    df_persons = df_q3.set_index('GKGRECORDID').join(df_q3.set_index('GKGRECORDID').Persons.apply(pd.Series).stack().reset_index(level=0).rename(columns={0:'Person'}).set_index('GKGRECORDID')).reset_index()
    df_countries =df_q3.set_index('GKGRECORDID').join(df_q3.set_index('GKGRECORDID').Countries.apply(pd.Series).stack().reset_index(level=0).rename(columns={0:'Country'}).set_index('GKGRECORDID')).reset_index()

    tone_country = df_countries.groupby('Country').mean().reset_index()
    tone_person = df_persons.groupby('Person').mean().reset_index()
    tone_theme = df_themes.groupby('Theme').mean().reset_index()

    country = tone_country.set_index('Country').join(df_countries.Country.value_counts())
    country = country.rename(columns={'Country':'Number of articles'})
    country.reset_index(inplace=True)
    country.dropna(inplace=True)

    person = tone_person.set_index('Person').join(df_persons.Person.value_counts())
    person = person.rename(columns={'Person':'Number of articles'})
    person.reset_index(inplace=True)

    theme = tone_theme.set_index('Theme').join(df_themes.Theme.value_counts())
    theme = theme.rename(columns={'Theme':'Number of articles'})
    theme.reset_index(inplace=True)

    st.markdown("**Requêtes basiques:**")

    st.write(country.sort_values("Number of articles", ascending=False))
    st.write(person.sort_values("Number of articles", ascending=False))
    st.write(theme.sort_values("Number of articles", ascending=False))

    #fig = px.scatter(country, x="Tone", y="Number of articles", color='Country')
    #st.plotly_chart(fig)
    country['iso']=country['Country'].apply(iso)

    st.markdown("**Ton moyen par pays :**")

    fig = px.choropleth(country, locations="iso", color="Tone", range_color=[-10,10],
                        color_continuous_scale="RdYlGn")
    st.plotly_chart(fig)

    st.markdown("**Top 10 pays par nombre d'articles :**")
    fig = px.bar(x=df_countries.Country.value_counts().index[:10], y=df_countries.Country.value_counts().values[:10])
    st.plotly_chart(fig)

    #fig = px.scatter(person, x="Tone", y="Number of articles", color='Person')
    #st.plotly_chart(fig)

    st.markdown("**Top 10 personnes par nombre d'articles :**")
    fig = px.bar(x=df_persons[df_persons.Person != ''].Person.value_counts().index[:10], y=df_persons.Person.value_counts().values[:10])
    st.plotly_chart(fig)

    #fig = px.scatter(theme, x="Tone", y="Number of articles", color='Theme')
    #st.plotly_chart(fig)

    st.markdown("**Top 10 thèmes par nombre d'articles :**")
    fig = px.bar(x=df_themes[df_themes.Theme != ''].Theme.value_counts().index[:10], y=df_themes.Theme.value_counts().values[:10])
    st.plotly_chart(fig)

elif navigation=='Question 4':

    st.markdown("dresser la cartographie des relations entre les pays d’après le ton des articles : pour chaque paire (pays1, pays2), calculer le nombre d’article, le ton moyen (aggrégations sur Année/Mois/Jour, filtrage par pays ou carré de coordonnées)")

    st.markdown("Aggrégations sur jour: ")
    country1 = st.sidebar.selectbox('Country1', ['US', 'CH', 'FR', 'GB', 'CN', 'JP'])
    country2 = st.sidebar.selectbox('Country2', ['FR', 'US', 'CH', 'GB', 'CN', 'JP'])

    year = st.sidebar.selectbox("Année :", ["2019","2018"])
    month = st.sidebar.multiselect("Mois :", ["01","02","03", "04","05","06","07","08","09","10","11","12"])
    day = st.sidebar.multiselect("Jour :", ["01","02","03", "04","05","06","07","08","09","10","11","12",
                                            "13","14","15", "16","17","18","19","20","21","22","23","24", "25","26","27","28", "29", "30"])

    df_q4 = query4(country1=country1, country2=country2, year=year, month=month, day=day)
    df_q4_final = pd.DataFrame(df_q4,
                               columns=['Year', 'Month', 'Day', 'Actor1Geo_CountryCode', 'Actor2Geo_CountryCode', 'avg_AvgTone',
                                        'sum_NumArticles', 'min_Actor1Geo_Long', 'min_Actor1Geo_lat', 'max_Actor1Geo_Long', 'max_Actor1Geo_Lat', 'min_Actor2Geo_Long', 'min_Actor2Geo_lat', 'max_Actor2Geo_Long', 'max_Actor2Geo_Lat', 'SQLDATE'])
    df_q4_final['SQLDATE'] = df_q4_final['SQLDATE'].astype('datetime64[ns]')
    df_q4_final = df_q4_final.sort_values(by=['Year', 'Month', 'Day'])
    df_q4_final = df_q4_final.reset_index(drop=True)
    st.dataframe(df_q4_final)

    st.markdown("  ")
    st.markdown("Average Tone Trend to show the relationship:")
    # fig = px.line(x=df_q4_final["SQLDATE"], y=df_q4_final["avg_AvgTone"])
    # df_q4_final_1 = pd.DataFrame(df_q4_final, columns=["SQLDATE", "avg_AvgTone"])
    #
    # fig = px.line(df_q4_final_1, title='Average Tone Trend Between ' + country1 + ' and ' + country2)
    fig1 = px.line(x=df_q4_final["SQLDATE"], y=df_q4_final["avg_AvgTone"], title='Average Tone Trend Between ' + country1 + ' -> ' + country2)
    st.plotly_chart(fig1)

    st.markdown("  ")
    st.markdown("Number of Articles:")
    fig2 = px.line(x=df_q4_final["SQLDATE"], y=df_q4_final["sum_NumArticles"],
                   title='Number of Articles ' + country1 + ' -> ' + country2)
    st.plotly_chart(fig2)

    print("")
