import streamlit as st
import pandas as pd
import altair as alt
import os
import pika 
import logging
from json import dumps
from sqlalchemy import create_engine
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader


#YAML einlesen
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

authenticator.login(location='main', key='Login')

if st.session_state["authentication_status"]:
    authenticator.logout('Logout', 'main')
    st.write(f'Welcome *{st.session_state["username"]}*')
    connection_parameter=pika.URLParameters(st.secrets["PIKA_CONNECTION"])
    postgres_connection_string=st.secrets["POSTGRES_CONNECTION"]

    #connection = pika.BlockingConnection(connection_parameter)
    #channel = connection.channel()
    #channel.queue_declare(queue="test")
    #st.session_state["pika_channel"]=channel
    #channel.basic_publish(routing_key="test", exchange="", body="hello from streamlit")


    # File path to store the exercise log
    EXERCISE_LOG_PATH = 'exercise_log.csv'
    EXERCISE_OPTIONS_PATH = 'exercise_options.txt'

    # Function to load exercise data from postgres db
    def load_data():
        return pd.read_sql(sql=f"SELECT * FROM exercises WHERE username='{st.session_state['username']}'", con= st.session_state["postgres_connection"])

    # Function to save exercise data to postgres db
    def save_data(df):
        df.to_sql(name="exercises", con= st.session_state["postgres_connection"], index=False, if_exists="append")

    # Function to load exercise options from db

    def load_exercise_options():
        df= pd.read_sql(sql=f"SELECT * FROM exercise_options WHERE username='{st.session_state['username']}'", con= st.session_state["postgres_connection"])
        return df['OPTIONS'].tolist()

    # Function to save exercise options to db

    def save_exercise_option(option):
        df=pd.DataFrame({'OPTIONS': [option],'username': [st.session_state['username']]})
        df.to_sql(name="exercise_options", con= st.session_state["postgres_connection"], index=False, if_exists="append")


    # Initialize session state
    if 'postgres_connection' not in st.session_state:
        st.session_state["postgres_connection"]=create_engine(postgres_connection_string)
    #if 'exercise_data' not in st.session_state:
    st.session_state['exercise_data'] = load_data()
    #if 'exercise_options' not in st.session_state:
    st.session_state['exercise_options'] = load_exercise_options()
    if 'pika_channel' not in st.session_state:
        connection_parameter=pika.URLParameters(st.secrets["PIKA_CONNECTION"])
        connection = pika.BlockingConnection(connection_parameter)
        channel = connection.channel()
        channel.queue_declare(queue="GYM")
        st.session_state["pika_channel"]=channel

    # Title
    st.title("Gym Exercise Tracker")

    # Function to add new exercises
    def add_new_exercise(new_exercise):
        if new_exercise:
            if new_exercise not in st.session_state['exercise_options']:
                st.session_state['exercise_options'].append(new_exercise)
                save_exercise_option(new_exercise)  # Save options
                st.success(f"Exercise '{new_exercise}' added successfully!")
            else:
                st.warning(f"Exercise '{new_exercise}' already exists.")
        else:
            st.error("Please fill in the exercise name.")

    # Section to add a new exercise
    st.subheader("Add a New Exercise")
    new_exercise_input = st.text_input("New Exercise Name")
    add_exercise_button = st.button("Add Exercise")

    if add_exercise_button:
        add_new_exercise(new_exercise_input)

    # Input form
    with st.form(key='exercise_form'):
        exercise = st.selectbox("Exercise", st.session_state['exercise_options'])
        date = st.date_input("Date")
        reps = st.number_input("Reps", min_value=1)
        weight = st.number_input("Weight", min_value=0, step=1)
        set_number = st.number_input("Set Number", min_value=1)
        submit_button = st.form_submit_button(label='Add Exercise')

    # Handle form submission
    if submit_button:
        if exercise and date and reps and weight and set_number:
            data_dict={
                "Exercise": exercise,
                "Date": date.strftime('%Y-%m-%d'),
                "Reps": reps,
                "Weight": weight,
                "Set Number": set_number,
                "username": st.session_state['username']
            }
            new_data = pd.DataFrame([data_dict])
            st.session_state['exercise_data'] = pd.concat([st.session_state['exercise_data'], new_data], ignore_index=True)
            save_data(new_data)  # Save data
            st.session_state["pika_channel"].basic_publish(routing_key="GYM", exchange="", body=dumps(data_dict))
            st.write("Data added successfully!")

        else:
            st.error("Please fill in all fields.")

    # Display exercise data
    st.subheader("Exercise Log")

    # Upload CSV file
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    # Handle file upload
    if uploaded_file is not None:
        try:
            csv_data = pd.read_csv(uploaded_file)
            # Ensure correct column names
            csv_data.columns = ["Exercise", "Date", "Reps", "Weight", "Set Number"]
            st.session_state['exercise_data'] = pd.concat([st.session_state['exercise_data'], csv_data], ignore_index=True)
            save_data(st.session_state['exercise_data'])  # Save data
            st.write("CSV data loaded successfully!")
        except Exception as e:
            st.error(f"Error loading CSV file: {e}")

    # Download exercise data
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv = convert_df(st.session_state['exercise_data'])

    st.download_button(
        label="Download Exercise Log as CSV",
        data=csv,
        file_name='exercise_log.csv',
        mime='text/csv',
    )

    # Option to delete a row
    if not st.session_state['exercise_data'].empty:
        row_to_delete = st.number_input("Select Row to Delete", min_value=0, max_value=len(st.session_state['exercise_data']) - 1)
        if st.button("Delete Row"):
            st.session_state['exercise_data'].drop(index=row_to_delete, inplace=True)
            st.session_state['exercise_data'].reset_index(drop=True, inplace=True)
            save_data(st.session_state['exercise_data'])  # Save data
            st.write(f"Deleted row: {row_to_delete}")

    # Option to delete the entire exercise log
    if st.button("Delete Entire Exercise Log"):
        st.session_state['exercise_data'] = pd.DataFrame(columns=["Exercise", "Date", "Reps", "Weight", "Set Number"])
        save_data(st.session_state['exercise_data'])  # Save data
        st.write("Deleted the entire exercise log.")

    st.dataframe(st.session_state['exercise_data'])

    # Plotting
    st.subheader("Exercise Progress")

    # Select exercise for visualization
    if not st.session_state['exercise_data'].empty:
        selected_exercise = st.selectbox("Select Exercise", st.session_state['exercise_data']["Exercise"].unique())
        
        if selected_exercise:
            # Filter data based on selections
            filtered_data = st.session_state['exercise_data'][
                st.session_state['exercise_data']["Exercise"] == selected_exercise
            ]

            if not filtered_data.empty:
                filtered_data['Date'] = pd.to_datetime(filtered_data['Date'])
                
                # Combined chart for Weight vs Reps over time
                st.subheader(f"Weight vs Reps over time for {selected_exercise}")
                
                scatter_chart = alt.Chart(filtered_data).mark_circle(size=100).encode(
                    x='Reps:Q',
                    y='Weight:Q',
                    color=alt.Color('Date:T', scale=alt.Scale(scheme='viridis')),
                    tooltip=['Date', 'Reps', 'Weight']
                ).properties(
                    title=f"Weight vs Reps over time for {selected_exercise}"
                ).interactive()
                
                st.altair_chart(scatter_chart, use_container_width=True)
            else:
                st.write("No data available for the selected exercise.")
    else:
        st.write("No exercise data available. Please add some exercises or upload a CSV file.")

elif st.session_state["authentication_status"] == False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] == None:
    st.warning('Please enter your username and password')


