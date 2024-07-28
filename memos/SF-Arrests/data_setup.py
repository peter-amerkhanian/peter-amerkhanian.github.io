import pandas as pd
from datetime import datetime
from sodapy import Socrata
import os

shelter_in_place = datetime(2020, 3, 17, 0, 1)

def load_data():
    #| output: false
    pickle_file = 'main_data.pkl'
    if not os.path.exists(pickle_file):
        # Read data from API
        client = Socrata("data.sfgov.org", None)
        results = client.get("wg3w-h783", limit=int(1e7))
        df = pd.DataFrame.from_records(results)
        df.to_pickle(pickle_file)
        print("Data successfully written to pickle file.")
    else:
        # Read data from existing pickle file
        df = pd.read_pickle(pickle_file)
        print("Data successfully loaded from pickle file.")
    return df

def datetime_processing(df):
    if df['incident_datetime'].dtype == 'object':
        df['incident_datetime'] = pd.to_datetime(
            df['incident_datetime'], format="%Y-%m-%dT%H:%M:%S.%f")
        df['report_datetime'] = pd.to_datetime(
            df['report_datetime'], format="%Y-%m-%dT%H:%M:%S.%f")
    else:
        pass
    df = df.sort_values(by="incident_datetime")
    df['YEAR'] = df['incident_datetime'].dt.year
    df['MONTH'] = df['incident_datetime'].dt.month
    df = df.drop(['incident_year', 'incident_time', 'incident_date'], axis=1)
    return df

def process(results_df):
    results_df['ARREST'] = (results_df['resolution'] ==
                            'Cite or Arrest Adult').astype(int)
    arrests_df = results_df[results_df['ARREST'] == 1]
    arrests_df = datetime_processing(arrests_df.copy())
    # Count up associated incidents for each row
    arrests_df = arrests_df.copy().merge(
        (arrests_df['incident_id'].value_counts()).to_frame(name='associated_incidents'),
        left_on='incident_id',
        right_index=True,
        how='left')

    # Shelter in Place date is march 17 at 12:01 AM per
    # https://www.sf.gov/news/sf-responds-coronavirus-outbreak-stay-home-order
    shelter_in_place = datetime(2020, 3, 17, 0, 1)
    arrests_df['POST_SIP_DUMMY'] = (
        arrests_df['incident_datetime'] > shelter_in_place).astype(int)
    # test that the first row is indeed pre SIP
    # and that the last row is post SIP
    assert arrests_df['POST_SIP_DUMMY'].iloc[-1] > 0
    assert arrests_df['POST_SIP_DUMMY'].iloc[0] < 1
    arrests_df['pre_pandemic'] = (arrests_df['incident_datetime'] < '2020') & (arrests_df['incident_datetime'] >= '2018')
    arrests_df['post_pandemic'] = (arrests_df['incident_datetime'] >= '2022') & (arrests_df['incident_datetime'] < '2024')

    arrests_df = arrests_df.set_index('incident_datetime')
    return arrests_df

def crime_type_flags(arrests_df):
    # "Property Part I crime categories include burglary, larceny, motor vehicle theft and arson"
    property_crimes = ['Burglary', 'Larceny Theft', 'Motor Vehicle Theft',
                    'Motor Vehicle Theft?', 'Arson', "Recovered Vehicle"]
    # "Property Part I crime categories include burglary, larceny, motor vehicle theft and arson"
    drug_crimes = ['Drug Offense', 'Drug Violation']
    # Violent Part I crime categories include homicide, rape, robbery and aggravated assault
    violent_crimes = ['Homicide', 'Rape', 'Robbery']
    # note that aggravated assault is a sub category
    violent_crimes_subcat = ['Aggravated Assault']
    arrests_df['VIOLENT'] = (
    arrests_df['incident_category'].isin(violent_crimes).astype(int) +
    arrests_df['incident_subcategory'].isin(violent_crimes_subcat).astype(int)
    )
    assert (arrests_df['VIOLENT'].max() == 1)
    arrests_df['PROPERTY'] = arrests_df['incident_category'].isin(
        property_crimes
        ).astype(int)
    arrests_df['DRUGS'] = arrests_df['incident_category'].isin(
        drug_crimes
        ).astype(int)
    # Make one column that has all of these categories as str
    arrests_df['BROAD_CAT'] = (
        arrests_df['VIOLENT'].replace({1: "Violent", 0: ""}).astype(str) +
        arrests_df['PROPERTY'].replace({1: "Property", 0: ""}).astype(str) +
        arrests_df['DRUGS'].replace({1: "Drugs", 0: ""}).astype(str)
        ).replace({"": "Other"})
    arrests_df['drug_sale'] = ((arrests_df['DRUGS'] == 1) &
                                     (arrests_df['incident_description'].str.lower(
                                     ).str.contains('sale')))
    arrests_df['drug_non_sale'] = (arrests_df['DRUGS'] == 1) & (arrests_df['drug_sale'] == 0)
    arrests_df['larceny_theft'] = (arrests_df['incident_category'] == "Larceny Theft")
    arrests_df['burglary'] = (arrests_df['incident_category'] == "Burglary")
    arrests_df['assault'] = (arrests_df['incident_category'] == "Assault")
    arrests_df['weapons'] = (arrests_df['incident_subcategory'] == "Weapons Offense")
    arrests_df['homicide'] = (arrests_df['incident_category'] == "Homicide")
    arrests_df['robbery'] = (arrests_df['incident_category'] == "Robbery")
    arrests_df['traffic'] = (arrests_df['incident_category'] == "Traffic Violation Arrest")
    return arrests_df

def build_test_dataset(period, arrests_df):
    testing_df = arrests_df[arrests_df['pre_pandemic'] |arrests_df['post_pandemic']]
    testing_day_df = testing_df.resample(period)[[
        'larceny_theft',
        'burglary',
        'drug_non_sale',
        'drug_sale',
        'assault',
        'robbery',
        'traffic',
        'weapons',
        'homicide',
        'post_pandemic',
        'incident_id'
    ]].agg({'larceny_theft': 'sum',
            'burglary': 'sum',
            'drug_non_sale': 'sum',
            'drug_sale': 'sum',
            'assault': 'sum',
            'homicide': 'sum',
            'robbery': 'sum',
            'weapons': 'sum',
            'traffic': 'sum',
            'incident_id': 'nunique',
            'post_pandemic': 'max'
            })
    return testing_day_df
