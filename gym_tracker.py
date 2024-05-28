import streamlit as st
import pandas as pd
import altair as alt

# Initialize session state
if 'exercise_data' not in st.session_state:
    st.session_state['exercise_data'] = pd.DataFrame(columns=["Exercise", "Muscle", "Date", "Reps", "Weight"])
if 'exercise_options' not in st.session_state:
    st.session_state['exercise_options'] = [
        "Bench Press", "Incline Press Machine", "Bird Machine", "Triceps Cable heavy", "Triceps Machine",
        "Shoulder Press Machine", "Lat Raise Machine", "Scholze Glas auskippen", "Shrug Machine",
        "Deadlift", "Cable Row Machine", "T Bar", "SZ Curls", "Biceps Machine"
    ]

# Title
st.title("Gym Exercise Tracker")

# Function to add new exercises
def add_new_exercise(new_exercise):
    if new_exercise:
        if new_exercise not in st.session_state['exercise_options']:
            st.session_state['exercise_options'].append(new_exercise)
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
    weight = st.number_input("Weight", min_value=0.0, step=0.1)
    submit_button = st.form_submit_button(label='Add Exercise')

# Handle form submission
if submit_button:
    if exercise and date and reps and weight:
        new_data = pd.DataFrame([{
            "Exercise": exercise,
            "Muscle": "",  # Remove muscle column if not needed
            "Date": date,
            "Reps": reps,
            "Weight": weight,
        }])
        st.session_state['exercise_data'] = pd.concat([st.session_state['exercise_data'], new_data], ignore_index=True)
        st.write("Data added successfully!")
    else:
        st.error("Please fill in all fields.")

# Display exercise data
st.subheader("Exercise Log")

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
