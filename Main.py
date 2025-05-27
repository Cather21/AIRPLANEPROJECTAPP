import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

def load_data():
# load dataset
    df = pd.read_csv("AIRPLANECRASHESPROJECT.csv")

    # Clean column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_") \
        .str.replace("(", "", regex=False).str.replace(")", "", regex=False) \
        .str.replace("/", "_")

   # Replace blank strings with NaN for object columns
    df[df.select_dtypes(include='object').columns] = df.select_dtypes(include='object').replace(r'^\s*$', np.nan, regex=True)

# Now fill essential missing values
    df['country_region'] = df.get('country_region', pd.Series()).fillna("Unknown")
    df['operator'] = df.get('operator', pd.Series()).fillna("Unknown")
    df['aircraft_manufacturer'] = df.get('aircraft_manufacturer', pd.Series()).fillna("Unknown")

    # Convert numeric columns
    df['year'] = pd.to_numeric(df.get('year', pd.Series()), errors='coerce')
    df['day'] = pd.to_numeric(df.get('day', pd.Series()), errors='coerce')
    df['aboard'] = pd.to_numeric(df.get('aboard', pd.Series()), errors='coerce')
    df['fatalities_air'] = pd.to_numeric(df.get('fatalities_air', pd.Series()), errors='coerce')
    df['ground'] = pd.to_numeric(df.get('ground', pd.Series()), errors='coerce')

 # Map month names to numbers
    month_map = {
    'January': 1, 'February': 2, 'March': 3, 'April': 4,
    'May': 5, 'June': 6, 'July': 7, 'August': 8,
    'September': 9, 'October': 10, 'November': 11, 'December': 12
}
    df['month_num'] = df['month'].map(month_map)

    
 # Create a datetime column from year and month_num
    df.columns = df.columns.str.lower()
    df['date'] = pd.to_datetime(dict(year=df['year'], month=df['month_num'], day=1))

 # Add month name for charts
    df['month_name'] = df['date'].dt.month_name()


# Add decade/period bins
    bins = [1908, 1920, 1933, 1944, 1955, 1967, 1980, 1991, 2002, 2013, 2024]
    labels = [
        "Late 1900s", "Early 1920s", "Mid 1930s",
        "Mid 1950s", "Late 1960s", "Early 1980s", "Early 1990s",
        "Early 2000s", "Late 2000s", "Mid 2020s"
    ]

    df['year_bin'] = pd.cut(df['year'], bins=bins, labels=labels, include_lowest=True)
    df['year_bin'] = pd.Categorical(df['year_bin'], categories=labels, ordered=True)
    
# define mapping from month name to season
    season_map= {
        "december":"Winter", "january":"Winter", "february":"Winter", "march":"Spring","april":"Spring",
             "may":"Spring", "june":"Summer", "july":"Summer", "august":"Summer", "september":"Autumn/Fall",
             "october":"Autumn/Fall", "november":"Autumn/Fall"
    }
    
    df['month'] = df['month'].str.lower()
    df['season'] = df['month'].str.lower().map(season_map)

    

    season_order = ["Winter", "Spring", "Summer", "Autumn/Fall"]



# Drop exact duplicates
    df.drop_duplicates(inplace=True)

    return df

# Load data
df = load_data()

st.title("✈️ Airplane Crashes Dashboard")

# Sidebar filters
filters = {
    "operator": df["operator"].unique(),
    "country_region": df["country_region"].unique(),
    "aircraft_manufacturer": df["aircraft_manufacturer"].unique()
}

selected_filters = {}
for key, options in filters.items():
    label = key.replace("_", " ").title()
    selected_filters[key] = st.sidebar.multiselect(str(label), options)

filtered_df = df.copy()
for key, selected_values in selected_filters.items():
    if selected_values:
        if key in filtered_df.columns:
            filtered_df = filtered_df = filtered_df[filtered_df[key].isin(selected_values)]
        else:
            st.warning(f"Column '{key}' not found in the dataframe.")

# Show sample data
st.dataframe(filtered_df.head())

# === Metrics ===
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Crashes", len(filtered_df))
with col2:
    st.metric("Total Fatalities", int(filtered_df["fatalities_air"].sum()))
with col3:
    st.metric("People Aboard", int(filtered_df["aboard"].sum()))
with col4:
    st.metric("Aircraft manufacturer", filtered_df["aircraft_manufacturer"].nunique())
with col5:
    st.metric("People on ground", filtered_df["ground"].nunique())

# === Charts ===
# Top 5 Operators by Fatalities
st.subheader(" Top 5 Operators by Fatalities")
top_operators = filtered_df.groupby("operator")["fatalities_air"].sum().nlargest(5).reset_index()

chart1 = alt.Chart(top_operators).mark_bar().encode(
    x=alt.X("fatalities_air:Q", title="Total Fatalities"),
    y=alt.Y("operator:N", title="Operator", sort='-x'),
    color=alt.Color("operator:N", legend=None)
).properties(height=300)

st.altair_chart(chart1, use_container_width=True)

# Pie Chart: Countries and The Their Number of Fatality
st.subheader(" Crashes by Countries")
crash_by_country = filtered_df.groupby("country_region")["fatalities_air"].sum().nlargest(10).reset_index()

chart2 = alt.Chart(crash_by_country).mark_arc(innerRadius=50).encode(
    theta="fatalities_air:Q",
    color="country_region:N",
    tooltip=["country_region:N", "fatalities_air:Q"]
).properties(height=350)

st.altair_chart(chart2, use_container_width=True)

# Bar Chart: Top Aircraft Types by Crashes
st.subheader("🛩️ Aircraft with the highest crashes")
by_type = filtered_df.groupby("aircraft_manufacturer")["fatalities_air"].sum().nlargest(10).reset_index()

chart3 = alt.Chart(by_type).mark_bar().encode(
    x=alt.X("fatalities_air:Q", title="Total Fatalities"),
    y=alt.Y("aircraft_manufacturer:N", title="aircraft", sort='-x'),
    color="aircraft_manufacturer:N"
).properties(height=300)

st.altair_chart(chart3, use_container_width=True)

# Line Chart: Monthly Crash Trend
st.subheader(" Monthly Crash Trend")

monthly_df = filtered_df.dropna(subset=["date"])


monthly_trend = (
    monthly_df.groupby("date")["fatalities_air"]
    .sum()
    .reset_index()
    .sort_values("date")
)

chart4 = alt.Chart(monthly_trend).mark_line(point=True).encode(
    x=alt.X("date:T", title="Month", axis=alt.Axis(format='%b %Y')),
    y=alt.Y("fatalities_air:Q", title="Fatalities"),
    tooltip=[alt.Tooltip("date:T", title="Month", format='%b %Y'), "fatalities_air:Q"]
).properties(height=350)

st.altair_chart(chart4, use_container_width=True)

#  Bar Chart: Crashes Over The Years
st.subheader(" Crashes by Decade")

crashes_by_decade = ( 
    filtered_df.groupby("year_bin", observed=False)["fatalities_air"]
    .sum()
    .reset_index()
)                     

chart5 = alt.Chart(crashes_by_decade).mark_bar().encode(
    x=alt.X("year_bin:N", title="Decade", sort='-y),
    y=alt.Y("fatalities_air:Q", title="Total Fatalities"),
    color=alt.Color("year_bin:N", legend=None)
).properties(height=350)

st.altair_chart(chart5, use_container_width=True)

#  Air vs Ground Fatalities Comparison
st.subheader("Air vs Ground Fatalities")

# Prepare the data
impact_comparison = pd.DataFrame({
    "Impact Type": ["Air Fatalities", "Ground Fatalities"],
    "Fatalities": [
        filtered_df["fatalities_air"].sum(),
        filtered_df["ground"].sum()
    ]
})

# Bar chart
chart6 = alt.Chart(impact_comparison).mark_bar().encode(
    x=alt.X("Impact Type:N", title="Impact Type"),
    y=alt.Y("Fatalities:Q", title="Total Fatalities"),
    color=alt.Color("Impact Type:N", legend=None)
).properties(height=300)

st.altair_chart(chart6, use_container_width=True)

#  Top 10 Locations by Number of Crashes
st.subheader("Locations With The Highest Crash")

# Group and count crashes per location
location_counts = (
    filtered_df.groupby("location")
    .size()
    .reset_index(name="crash_count")
    .sort_values("crash_count", ascending=False)
    .head(10)
)

# Bar chart
chart7 = alt.Chart(location_counts).mark_bar().encode(
    x=alt.X("crash_count:Q", title="Number of Crashes"),
    y=alt.Y("location:N", title="Location", sort='-x'),
    color=alt.Color("location:N", legend=None)
).properties(height=350)

st.altair_chart(chart7, use_container_width=True)

# Relationship Between People Aboard and Fatalities
st.subheader("Aboard vs. Fatalities (Air)")

# Drop rows with missing values in both columns
scatter_df = filtered_df.dropna(subset=["aboard", "fatalities_air"])

# Scatter plot
chart8 = alt.Chart(scatter_df).mark_circle(size=60, opacity=0.6).encode(
    x=alt.X("aboard:Q", title="People Aboard"),
    y=alt.Y("fatalities_air:Q", title="Fatalities (Air)"),
    tooltip=["year", "operator", "aboard", "fatalities_air"]
).interactive().properties(height=350)

st.altair_chart(chart8, use_container_width=True)

#  Average Aboard Over Time
st.subheader(" Average People Aboard Over Time")

# Drop missing years or aboard values
aboard_trend_df = filtered_df.dropna(subset=["year_bin", "aboard"])

# Group by year and calculate average aboard
aboard_trend = (
    aboard_trend_df.groupby("year_bin", observed=True)["aboard"]
    .mean()
    .sort_index()
    .reset_index()
    
)

# Line chart using Altair
chart_avg_aboard = alt.Chart(aboard_trend).mark_line(point=True).encode(
    x=alt.X("year_bin:O", title="Year"),
    y=alt.Y("aboard:Q", title="Average Aboard"),
    tooltip=["year_bin", alt.Tooltip("aboard:Q", title="Avg. Aboard", format=".1f")]
).properties(height=350)

st.altair_chart(chart_avg_aboard, use_container_width=True)

st.subheader(" Top 10 death in aircrafts with the number of people aboard and who died on ground")
data10 = df["aircraft"].value_counts().nlargest(10)
data10 = data10.to_frame(name="Count")

fatalities_sum = df.groupby("aircraft")["fatalities_air"].sum()
ground_sum = df.groupby("aircraft")["ground"].sum()
people_aboard = df.groupby("aircraft")["aboard"].sum()
data10["fatalities_air"] = fatalities_sum
data10["ground"] = ground_sum
data10["aboard"] = people_aboard

data10 = data10.reset_index().rename(columns={"index": "aircraft"})

st.dataframe(data10)

data1 = data10.melt(
    id_vars = "aircraft",
    value_vars= ["fatalities_air","ground","aboard"],
    var_name = "Metric",
    value_name = "Value"
)

chart9 = alt.Chart(data1).mark_line().encode(
    x = alt.X('aircraft', title='Aircrafts'),
    y=alt.Y('Value:Q', title='Count'),
    color=alt.Color('Metric:N', title='Metric',scale=alt.Scale(domain=["fatalities_air","ground","aboard"],
                        range=['green', 'blue',"red"])),
    xOffset='Metric:N',  # This makes the bars appear side-by-side within each Quarter
    tooltip=['aircraft', 'Metric', 'Value']
).properties(
    width=400,
    height=300
)

st.altair_chart(chart9, use_container_width=True)


st.title('Airplane Crashes by Season')

# Let user choose the metric
option = st.selectbox("Choose metric to display:", ["Number of Crashes", "Total Fatalities"])


# Prepare data based on selected metric
if option == "Number of Crashes":
    season_counts = df["season"].value_counts().rename_axis("season").reset_index(name='count')
    season_order = ["Winter", "Spring", "Summer", "Autumn/Fall"]
    season_counts["season"] = pd.Categorical(season_counts["season"], categories=season_order, ordered=True)
    season_counts = season_counts.sort_values("season")

    season_counts = df["season"].value_counts().reset_index(name='count')
    season_counts.columns = ['season', 'count']

    chart10 = alt.Chart(season_counts).mark_bar().encode(
    x=alt.X("season:N", sort=season_order, title='Season'),
    y=alt.Y("count:Q", title='Number of Crashes'),
    color=alt.Color("season:N", legend=None),
    tooltip=['season', 'count']
).properties(
    title='Number of Crashes per Season',
    width=600,
    height=400
)
else:
    fatalities_by_season = df.groupby("season")['fatalities_air'].sum().reset_index(name='count')
    season_order = ["Winter", "Spring", "Summer", "Autumn/Fall"]
    fatalities_by_season["season"] = pd.Categorical(fatalities_by_season["season"], categories=season_order, ordered=True)
    fatalities_by_season = fatalities_by_season.sort_values("season")

    chart10 = alt.Chart(fatalities_by_season).mark_bar().encode(
        x=alt.X("season:N", sort=season_order, title='Season'),
        y=alt.Y('count:Q', title='Total Fatalities'),
        color=alt.Color('season:N', legend=None,),
        tooltip=["season", 'count']
    ).properties(
        title='Total Fatalities per Season',
        width=600,
        height=400
    )

# Display the chart
st.altair_chart(chart10, use_container_width=True)
