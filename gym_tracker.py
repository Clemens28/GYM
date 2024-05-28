import streamlit as st
import pandas as pd
import altair as alt

# Initialize session state
if 'exercise_data' not in st.session_state:
    st.session_state['exercise_data'] = pd.DataFrame(columns=["Exercise", "Muscle", "Date", "Reps", "Weight"])

# Title
st.title("Gym Exercise Tracker")

# Upload CSV file
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

# Function to load CSV data
def load_csv(file):
    csv_data = pd.read_csv(file)
    # Ensure correct column names
    csv_data.columns = ["Exercise", "Muscle", "Date", "Reps", "Weight"]
    return csv_data

# Handle file upload
if uploaded_file is not None:
    try:
        csv_data = load_csv(uploaded_file)
        st.session_state['exercise_data'] = pd.concat([st.session_state['exercise_data'], csv_data], ignore_index=True)
        st.write("CSV data loaded successfully!")
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")

# Input form
with st.form(key='exercise_form'):
    exercise = st.text_input("Exercise")
    muscle = st.text_input("Muscle")
    date = st.date_input("Date")
    reps = st.number_input("Reps", min_value=1)
    weight = st.number_input("Weight", min_value=0.0, step=0.1)
    submit_button = st.form_submit_button(label='Add Exercise')

# Handle form submission
if submit_button:
    new_data = pd.DataFrame([{
        "Exercise": exercise,
        "Muscle": muscle,
        "Date": date,
        "Reps": reps,
        "Weight": weight,
    }])
    st.session_state['exercise_data'] = pd.concat([st.session_state['exercise_data'], new_data], ignore_index=True)
    st.write("Data added successfully!")

# Display exercise data
st.subheader("Exercise Log")
st.dataframe(st.session_state['exercise_data'])

# Plotting
st.subheader("Exercise Progress")

# Select exercise and muscle for visualization
if not st.session_state['exercise_data'].empty:
    selected_exercise = st.selectbox("Select Exercise", st.session_state['exercise_data']["Exercise"].unique())
    selected_muscle = st.selectbox("Select Muscle", st.session_state['exercise_data']["Muscle"].unique())

    # Filter data based on selections
    filtered_data = st.session_state['exercise_data'][
        (st.session_state['exercise_data']["Exercise"] == selected_exercise) & 
        (st.session_state['exercise_data']["Muscle"] == selected_muscle)
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
    st.write("No data available for the selected exercise and muscle.")