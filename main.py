import streamlit as st
import pandas as pd
import csv
from io import StringIO
import json

# ------------------------------------------------------------
# PAGE CONFIGURATION
# ------------------------------------------------------------
st.set_page_config(
    page_title="Student Email Generator",
    page_icon="📧",
    layout="wide"
)

# ------------------------------------------------------------
# INITIALIZE ASSIGNMENT CONFIGURATION
# ------------------------------------------------------------
DEFAULT_ASSIGNMENTS = {
    "Starter Pack Quiz": {"max_points": 5, "assigned": True},
    "Assignment 1": {"max_points": 5, "assigned": True},
    "Assignment 2": {"max_points": 15, "assigned": True},
    "Assignment 3": {"max_points": 20, "assigned": True},
    "Mid Course Feedback Form": {"max_points": 2, "assigned": True},
    "Assignment 4": {"max_points": 20, "assigned": True},
    "Assignment 5": {"max_points": 20, "assigned": False},
    "Assignment 6": {"max_points": 20, "assigned": False},
    "Assignment 7": {"max_points": 15, "assigned": False},
    "End Course Feedback Form": {"max_points": 3, "assigned": False}
}

if "assignments" not in st.session_state:
    st.session_state.assignments = DEFAULT_ASSIGNMENTS.copy()

ASSIGNMENTS = st.session_state.assignments

# ------------------------------------------------------------
# FUNCTIONS
# ------------------------------------------------------------
def parse_grade(grade_value):
    """Parse grade value and return status and points."""
    if pd.isna(grade_value) or str(grade_value).strip() in ["", "-"]:
        return None, "Not yet assigned"
    
    grade_str = str(grade_value).strip()
    
    if grade_str.lower().startswith("late:"):
        try:
            points = float(grade_str.split(":")[1].strip())
            return points, "Done Late"
        except:
            return None, "Done Late"
    
    if grade_str.lower() in ["missing"]:
        return 0, "Missing"
    
    if grade_str.lower() in ["not graded yet", "ungraded", "pending"]:
        return None, "Pending Grade"

    if grade_str.lower() in ["not submitted"]:
        return None, "No Submission"
    
    try:
        points = float(grade_str)
        return points, "Graded"
    except:
        return None, "Unknown"

def format_assignment_line(assignment_name, grade_value, max_points, is_assigned):
    """Format a single assignment line for the email."""
    if not is_assigned:
        return f"• {assignment_name}: worth {max_points} points"
    
    points, status = parse_grade(grade_value)
    if points is not None and points == int(points):
        points = int(points)
    if max_points == int(max_points):
        max_points = int(max_points)
    
    if status == "Graded":
        return f"• {assignment_name}: {points}/{max_points} points"
    elif status == "Done Late":
        if points is not None:
            return f"• {assignment_name}: {points}/{max_points} points (Done Late)"
        else:
            return f"• {assignment_name}: Done Late/{max_points} points"
    elif status == "Missing":
        return f"• {assignment_name}: Missing/{max_points} points"
    elif status == "Pending Grade":
        return f"• {assignment_name}: Pending Grade/{max_points} points"
    elif status == "No Submission":
        return f"• {assignment_name}: No Submission/{max_points} points"
    else:
        return f"• {assignment_name}: _/{max_points} points"

def calculate_total_points(row):
    """Calculate total points earned so far."""
    total = 0
    for assignment, config in ASSIGNMENTS.items():
        if config["assigned"]:
            grade_value = row.get(assignment)
            points, status = parse_grade(grade_value)
            if points is not None and status in ["Graded", "Done Late"]:
                total += points
    return int(total) if total == int(total) else total

def generate_email_body(row):
    """Generate personalized email body for a student."""
    first_name = row["Student Name"]
    total_points = calculate_total_points(row)
    
    progress_lines = []
    upcoming_lines = []
    
    for assignment, config in ASSIGNMENTS.items():
        grade_value = row.get(assignment)
        line = format_assignment_line(assignment, grade_value, config["max_points"], config["assigned"])
        if config["assigned"]:
            progress_lines.append(line)
        else:
            upcoming_lines.append(line)
    
    progress_section = "\n".join(progress_lines)
    upcoming_section = "\n".join(upcoming_lines)
    
    email_body = f"""CURRENT TOTAL: {total_points} points

Progress so far:
{progress_section}

Upcoming Assignments:
{upcoming_section}"""
    
    return email_body

# ------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------
if 'sent_status' not in st.session_state:
    st.session_state.sent_status = {}
if 'generated_data' not in st.session_state:
    st.session_state.generated_data = None

# ------------------------------------------------------------
# CUSTOM CSS
# ------------------------------------------------------------
st.markdown("""
<style>
    .student-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .student-name {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
    }
    .points-badge {
        font-size: 18px;
        font-weight: bold;
        padding: 5px 10px;
        border-radius: 5px;
        display: inline-block;
    }
    .points-high {
        background-color: #d4edda;
        color: #155724;
    }
    .points-medium {
        background-color: #fff3cd;
        color: #856404;
    }
    .points-low {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# MAIN UI
# ------------------------------------------------------------
st.title("📧 Student Grade Summary Generator")
st.markdown("### Quick Grade Snippets for HubSpot")

st.info("💡 **New Workflow:** You can now edit assignment configurations for any class!")

# ------------------------------------------------------------
# SIDEBAR CONFIGURATION
# ------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")

    with st.expander("✏️ Edit Assignments", expanded=False):
        st.markdown("Modify your class setup or load a saved one.")

        # Add new assignment
        with st.form("add_assignment_form", clear_on_submit=True):
            st.subheader("Add New Assignment")
            new_name = st.text_input("Assignment Name")
            new_points = st.number_input("Max Points", min_value=1, max_value=200, value=10)
            new_assigned = st.checkbox("Already Assigned?", value=True)
            submitted = st.form_submit_button("Add Assignment")
            if submitted and new_name:
                st.session_state.assignments[new_name] = {
                    "max_points": new_points,
                    "assigned": new_assigned
                }
                st.success(f"Added '{new_name}'")

        st.markdown("---")
        st.subheader("Current Assignments")

        remove_list = []
        for name, config in list(st.session_state.assignments.items()):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                new_name = st.text_input("Name", name, key=f"name_{name}")
            with col2:
                new_points = st.number_input("Max Points", min_value=1, value=config["max_points"], key=f"points_{name}")
            with col3:
                new_assigned = st.checkbox("Assigned?", value=config["assigned"], key=f"assigned_{name}")
            with col4:
                if st.button("🗑️", key=f"delete_{name}"):
                    remove_list.append(name)
            
            st.session_state.assignments[name] = {
                "max_points": new_points,
                "assigned": new_assigned
            }
            if new_name != name:
                st.session_state.assignments[new_name] = st.session_state.assignments.pop(name)

        for r in remove_list:
            st.session_state.assignments.pop(r, None)
            st.warning(f"Removed '{r}'")

        # Save / Load JSON config
        st.markdown("---")
        st.subheader("💾 Save / Load Configuration")
        col1, col2 = st.columns(2)
        with col1:
            json_data = json.dumps(st.session_state.assignments, indent=2)
            st.download_button("⬇️ Download Config (JSON)", json_data, file_name="assignments_config.json")
        with col2:
            uploaded_json = st.file_uploader("Upload Config JSON", type=["json"], key="upload_json")
            if uploaded_json is not None:
                st.session_state.assignments = json.load(uploaded_json)
                st.success("✅ Loaded new assignment configuration!")

# ------------------------------------------------------------
# FILE UPLOAD
# ------------------------------------------------------------
uploaded_file = st.file_uploader("Upload Student Grades CSV", type=['csv'])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        required_columns = ["Student Name"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
        else:
            st.success(f"✅ Successfully loaded data for {len(df)} students")
            
            with st.expander("📊 Preview Student Data"):
                st.dataframe(df)
            
            if st.button("🚀 Generate Emails", type="primary"):
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, row in df.iterrows():
                    grade_summary = generate_email_body(row)
                    total_points = calculate_total_points(row)
                    student_id = f"{row['Student Name']}"
                    
                    results.append({
                        "student_id": student_id,
                        "Student Name": row["Student Name"],
                        "Grade Summary": grade_summary,
                        "Total Points": total_points
                    })
                    
                    if student_id not in st.session_state.sent_status:
                        st.session_state.sent_status[student_id] = False
                    
                    progress_bar.progress((idx + 1) / len(df))
                    status_text.text(f"Processing {idx + 1}/{len(df)}: {row['Student Name']}")
                
                status_text.text("✅ All emails generated!")
                st.session_state.generated_data = results
                
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                output_df = pd.DataFrame(results)
                with col1:
                    st.metric("Total Students", len(results))
                with col2:
                    avg_points = output_df["Total Points"].mean()
                    st.metric("Average Points", f"{avg_points:.1f}")
                with col3:
                    completion_eligible = len(output_df[output_df["Total Points"] >= 80])
