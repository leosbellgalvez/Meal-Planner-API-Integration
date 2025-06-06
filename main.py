import math

import streamlit as st
import pandas as pd
import altair as alt
import time
import os
import requests



DATA_FOLDER = "data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)


CONSENT_CSV = os.path.join(DATA_FOLDER, "consent_data.csv")
INFORMATION_CSV = os.path.join(DATA_FOLDER, "information_data.csv")
MEALS_PLANNED_CSV = os.path.join(DATA_FOLDER, "meals_planned_data.csv")



def save_to_csv(data_dict, csv_file):
    df_new = pd.DataFrame([data_dict])
    if not os.path.isfile(csv_file):
        df_new.to_csv(csv_file, mode='w', header=True, index=False)
    else:
        df_new.to_csv(csv_file, mode='a', header=False, index=False)


def load_from_csv(csv_file):
    if os.path.isfile(csv_file):
        return pd.read_csv(csv_file)
    else:
        return pd.DataFrame()



def get_meal_plan(calories, diet, exclude_allergies):
    api_key = '1f6b5367671446f0ab61108d03385775'
    url = f"https://api.spoonacular.com/mealplanner/generate?apiKey={api_key}"

    params = {
        'timeFrame': 'week',
        'targetCalories': calories,
        'diet': diet,  # E.g.,
        'exclude': exclude_allergies
    }

    response = requests.get(url, params=params)
    data = response.json()

    if response.status_code == 200:
        for day, details in data['week'].items():

            st.session_state.daily_nutrients[day.capitalize()] = details.get('nutrients', {})
            for meal in details['meals']:
                meal_info = {
                    'day': day.capitalize(),
                    'title': meal['title'],
                    'readyInMinutes': meal['readyInMinutes'],
                    'servings': meal['servings'],
                    'sourceUrl': meal['sourceUrl'],
                    'image': meal['image'],
                    'sourceUrl': meal['sourceUrl'],
                }
                st.session_state.meals_to_display.append(meal_info)
    else:
        print(f"Error: {response.status_code}")
        print(data)





def calculate_calories(weight, height, age, sex, activity_level):
    if sex.lower() == 'male':
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)


    activity_multiplier = {
        'sedentary': 1.2,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very_active': 1.9
    }
    return bmr * activity_multiplier[activity_level]

def cm_to_feet_inches(cm):
    inches_total = cm / 2.54
    feet = int(inches_total // 12)
    inches = int(round(inches_total % 12))
    return f"{feet}'{inches}\""

def kg_to_lbs(kg):
    lbs = kg * 2.20462
    return round(lbs, 2)


def main():
    for key, default in [
        ('weight_m', None),
        ('height_m', None),
        ('age_m', None),
        ('sex_m', None),
        ('activity_level_m', None),
        ('calories_needed', 0),
        ('allergies', 'None'),
        ('meals_to_display', []),
        ('daily_nutrients', {})
    ]:
        if key not in st.session_state:
            st.session_state[key] = default


    if "meals_to_display" not in st.session_state:
        st.session_state.meals_to_display = []

    if "daily_nutrients" not in st.session_state:
        st.session_state.daily_nutrients = {}





    st.title("Meal Planner")

    st.sidebar.header("Navigation")
    tab = st.sidebar.radio("Go to", ["🏠 Home", "✅ Consent", "ℹ️ Information", "🍽 Meal Plan", "📈 Report"])


    if tab == "🏠 Home":
        st.header("How to use the meal planner!")
        st.write("""
                Welcome to the Meal Planning Tool!

                To begin, please follow these steps:
                1. Provide consent for data collection and analysis.
                2. Fill out a short form involving height, weight, etc.
                3. View a report for your meal plan!
                4. Finish!
                """)
        col1, col2, col3 = st.columns(3)

        df_meals = load_from_csv(MEALS_PLANNED_CSV)
        with col1:
            if not df_meals.empty:
                st.metric(label="🥗 Meals Planned", value=df_meals["meals_planned"].sum())
                st.caption("Total meals in your current weekly plan")
            else:
                st.metric(label="🥗 Meals Planned", value=0)
                st.caption("Total meals in your current weekly plan")

        with col2:
            st.metric(label="⏰ Avg Prep Time", value="30 mins")
            st.caption("Average cooking time per meal")

        with col3:
            st.metric(label="🔥 Calories / Day", value="2000 kcal")
            st.caption("Target daily calorie intake")

        st.markdown("---")

    elif tab == "✅ Consent":
        st.header("Consent Form")

        st.text(
            "I consent and give permission to have any of the answers I send and submit in this questionnaire to be used for data analysis, etc.")

        consent_checkbox = st.checkbox("I consent and give permission")

        if st.button("Submit Consent"):

            if not consent_checkbox:
                st.warning("You must agree to the consent terms before proceeding.")
            else:
                data_dict = {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "consent_given": consent_checkbox
                }
                save_to_csv(data_dict, CONSENT_CSV)
                st.success("Consent Form successfully submitted!")
    elif tab == "ℹ️ Information":
        st.header("Information Form")

        with st.form("information_form"):
            sex = st.text_input("What's your sex?", value=st.session_state.get('sex_m') or "")
            age = st.number_input("What's your age?", 0, 100, value=st.session_state.get('age_m') or 0)
            weight = st.number_input("What's your weight in kg?", 0.0, 600.0,
                                     value=st.session_state.get('weight_m') or 0.0)
            height = st.number_input("What's your height in cm?", 0.0, 600.0,
                                     value=st.session_state.get('height_m') or 0.0)
            activity_level = st.selectbox("Select activity level:",
                                          ["sedentary", "light", "moderate", "active", "very_active"],
                                          index=["sedentary", "light", "moderate", "active", "very_active"].index(
                                              st.session_state.get('activity_level_m') or 'sedentary'
                                          ))
            food_allergies = st.text_input("Any allergies? (Type separating with commas) e.g gluten,dairy",
                                           value=st.session_state.get('allergies', 'None'))

            submitted = st.form_submit_button("Generate Meal Plan!")

            if submitted:
                st.session_state['sex_m'] = sex.strip()
                st.session_state['age_m'] = age
                st.session_state['weight_m'] = weight
                st.session_state['height_m'] = height
                st.session_state['activity_level_m'] = activity_level
                st.session_state['allergies'] = food_allergies.strip()

                st.session_state['calories_needed'] = calculate_calories(weight, height, age, sex, activity_level)


                st.session_state['meals_to_display'] = []
                get_meal_plan(calories=st.session_state['calories_needed'], diet='none', exclude_allergies=food_allergies)

                # Save information to CSV if needed
                data_dict = {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "sex": sex,
                    "age": age,
                    "weight": weight,
                    "height": height,
                    "activity_level": activity_level,
                    "food_allergies": food_allergies
                }
                save_to_csv(data_dict, INFORMATION_CSV)

                st.success(
                    "Information successfully submitted! Generated your specialized meal plan. Please move on to the next tab!")
    elif tab == "🍽 Meal Plan":
        st.header("Weekly Meal Plan")

        if "meals_planned_count" not in st.session_state:
            st.session_state.meals_planned_count = 0
        else:
            st.session_state.meals_planned_count = 0

        with st.container():


            days = []
            for meal in st.session_state.get("meals_to_display", []):
                if meal['day'] not in days:
                    days.append(meal['day'])

            for day in days:
                st.markdown(f"## {day}")

                for meal in st.session_state.get("meals_to_display", []):
                    if meal['day'] == day:
                        st.markdown(f"### {meal['title']}")
                        st.image(f"https://spoonacular.com/recipeImages/{meal['image']}", width=300)
                        st.write(f"**Ready in:** {meal['readyInMinutes']} mins")
                        st.write(f"**Servings:** {meal['servings']}")
                        st.markdown(f"[Recipe Link]({meal['sourceUrl']})")
                        st.session_state.meals_planned_count += 1

                st.markdown("---")
                nutrients = st.session_state.get("daily_nutrients", {}).get(day, {})
                if nutrients:
                    st.markdown("**Nutrients:**")
                    for nutrient_name, amount in nutrients.items():
                        pretty_name = nutrient_name.replace('_', ' ').capitalize()
                        st.write(f"- {pretty_name}: {amount}")

                st.markdown("---")

            with st.form("meal_planner_form_unique"):

                submit = st.form_submit_button("I understand!")
                if submit:
                    data_dict = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "meals_planned": st.session_state.get("meals_planned_count", 0),
                    }

                    save_to_csv(data_dict, MEALS_PLANNED_CSV)
                    st.success(f"Great! Total meals planned this time: : {st.session_state.meals_planned_count}")
    elif tab == "📈 Report":
        st.header("Report")
        df_meals = load_from_csv(MEALS_PLANNED_CSV)

        st.write("Meals planned by the meal planner (All time)")

        if MEALS_PLANNED_CSV and not df_meals.empty:
            df = pd.read_csv(MEALS_PLANNED_CSV, parse_dates=['timestamp'])
            df = df.sort_values('timestamp')

            chart = (
                alt.Chart(df)
                .mark_line(point=True)
                .encode(
                    x=alt.X('timestamp:T', axis=alt.Axis(format='%Y-%m-%d %I:%M %p')),
                    y='meals_planned',
                    tooltip=['timestamp:T', 'meals_planned']
                )
                .interactive()
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.error("No CSV file or no data found")

        if MEALS_PLANNED_CSV and not df_meals.empty:
            df = pd.read_csv(MEALS_PLANNED_CSV, parse_dates=['timestamp'])
            df = df.sort_values('timestamp')

            chart = (
                alt.Chart(df)
                .mark_bar(point=True)
                .encode(
                    x=alt.X('timestamp:T', axis=alt.Axis(format='%Y-%m-%d %I:%M %p')),
                    y='meals_planned',
                    tooltip=['timestamp:T', 'meals_planned']
                )
                .interactive()
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.error("No CSV file or no data found")

        st.metric(label="🥗 Meals Planned", value=df_meals["meals_planned"].sum())
        st.metric(label="🎯 Target Calories", value=math.ceil(st.session_state.get('calories_needed', 0)))
        st.metric(label="❌ Allergies", value=st.session_state.get('allergies', 'None'))
        st.metric(label="💯 Age", value=st.session_state.get('age_m', 0))
        st.metric(label="♂️♀️ Sex", value=st.session_state.get('sex_m', 'Not specified'))
        st.metric(label="💯 Weight in lbs", value=kg_to_lbs(float(st.session_state.get('weight_m') or 0)))
        st.metric(label="⬆️ Height in feet", value=cm_to_feet_inches(float(st.session_state.get('height_m') or 0)))
        st.metric(label="🏋 Activity Level", value=st.session_state.get('activity_level_m', 'Not selected'))

        st.dataframe(df)

        bbox = (24.396308, -87.634938, 31.000968, -79.974307)
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:25];
        (
          node["shop"="supermarket"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          node["shop"="grocery"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        );
        out body;
        """
        response = requests.get(overpass_url, params={'data': query})
        data = response.json()
        stores = []
        for element in data['elements']:
            lat = element.get('lat')
            lon = element.get('lon')
            name = element.get('tags', {}).get('name', 'Unnamed Store')
            stores.append({'name': name, 'lat': lat, 'lon': lon})

        df = pd.DataFrame(stores)

        st.title("Grocery Stores in Florida")

        st.write(f"Number of stores found: {len(df)}")

        if not df.empty:
            st.map(df[['lat', 'lon']])
        else:
            st.write("No stores found.")



        st.dataframe(df)









    # ------------ Assignment API Credit Fineprint----------------
    st.markdown("""
       <div style='text-align: right; font-size: 12px; color: gray; padding-top: 50px;'>
           Powered by Spoonacular API
       </div>
       """, unsafe_allow_html=True)
    #______________________________________________________________

if __name__ == "__main__":
    main()