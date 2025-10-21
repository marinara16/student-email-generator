import streamlit as st
import pandas as pd
import csv
from io import StringIO
import json

# Page configuration
st.set_page_config(
    page_title="Student Email Generator",
    page_icon="📧",
    layout="wide"
)

# Assignment configurations
ASSIGNMENTS = {
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
    
    if grade_str.lower() in ["missing", "not submitted"]:
        return 0, "Missing"
    
    if grade_str.lower() in ["not graded yet", "ungraded", "pending"]:
        return None, "Not Graded Yet"
    
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
    
    # Format points as integer if it's a whole number
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
    elif status == "Not Graded Yet":
        return f"• {assignment_name}: Not yet graded/{max_points} points"
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
    # Return as integer if it's a whole number
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

# Initialize session state for tracking sent emails
if 'sent_status' not in st.session_state:
    st.session_state.sent_status = {}
if 'generated_data' not in st.session_state:
    st.session_state.generated_data = None

# Custom CSS for better styling
st.markdown("""
<style>
    .student-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .copy-button {
        background-color: #4CAF50;
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

# Streamlit UI
st.title("📧 Student Grade Summary Generator")
st.markdown("### Quick Grade Snippets for HubSpot")

st.info("💡 **New Workflow:** This app now generates ONLY the grade summary section. Copy and paste it into your HubSpot email template!")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    st.markdown("### Assignment Settings")
    
    with st.expander("View/Edit Assignments"):
        st.markdown("**Assigned Assignments:**")
        for name, config in ASSIGNMENTS.items():
            if config["assigned"]:
                st.write(f"• {name}: {config['max_points']} points")
        
        st.markdown("**Upcoming Assignments:**")
        for name, config in ASSIGNMENTS.items():
            if not config["assigned"]:
                st.write(f"• {name}: {config['max_points']} points")
    
    st.markdown("---")
    st.markdown("### Grade Format Guide")
    st.code("5 or 15.5 = Graded\nLate: 5 = Late submission\nMissing = Not submitted\nNot Graded Yet = Pending\nBlank = Not assigned")
    
    st.markdown("---")
    if st.session_state.generated_data is not None:
        sent_count = sum(1 for v in st.session_state.sent_status.values() if v)
        total_count = len(st.session_state.generated_data)
        st.metric("📊 Progress", f"{sent_count}/{total_count} sent")
        
        if sent_count > 0:
            progress_pct = (sent_count / total_count) * 100
            st.progress(progress_pct / 100)

# File uploader
uploaded_file = st.file_uploader("Upload Student Grades CSV", type=['csv'])

if uploaded_file is not None:
    try:
        # Read the CSV
        df = pd.read_csv(uploaded_file)
        
        # Verify required columns
        required_columns = ["Student Name"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
        else:
            st.success(f"✅ Successfully loaded data for {len(df)} students")
            
            # Show preview
            with st.expander("📊 Preview Student Data"):
                st.dataframe(df)
            
            # Generate emails button
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
                    
                    # Initialize sent status
                    if student_id not in st.session_state.sent_status:
                        st.session_state.sent_status[student_id] = False
                    
                    progress_bar.progress((idx + 1) / len(df))
                    status_text.text(f"Processing {idx + 1}/{len(df)}: {row['Student Name']}")
                
                status_text.text("✅ All emails generated!")
                st.session_state.generated_data = results
                
                # Display statistics
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
                    st.metric("On Track for Completion", completion_eligible)
            
            # Display individual student grade summaries
            if st.session_state.generated_data is not None:
                st.markdown("---")
                st.header("📊 Individual Student Grade Summaries")
                
                # Filter options
                col1, col2 = st.columns(2)
                with col1:
                    show_sent = st.checkbox("Show already sent", value=True)
                with col2:
                    show_unsent = st.checkbox("Show not sent", value=True)
                
                for idx, student_data in enumerate(st.session_state.generated_data):
                    student_id = student_data["student_id"]
                    is_sent = st.session_state.sent_status.get(student_id, False)
                    
                    # Filter based on sent status
                    if (is_sent and not show_sent) or (not is_sent and not show_unsent):
                        continue
                    
                    # Determine points badge color
                    points = student_data["Total Points"]
                    if points >= 80:
                        badge_class = "points-high"
                        badge_text = "🏆 Completion Track"
                    elif points >= 40:
                        badge_class = "points-medium"
                        badge_text = "📜 Participation Track"
                    else:
                        badge_class = "points-low"
                        badge_text = "⚠️ Below Threshold"
                    
                    # Student card
                    with st.container():
                        st.markdown(f"""
                        <div class="student-card">
                            <span class="student-name">
                                {student_data['Student Name']}
                            </span>
                            <span class="points-badge {badge_class}">
                                {points} points - {badge_text}
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.text(f"👤 {student_data['Student Name']}")
                        
                        with col2:
                            # Mark as sent checkbox
                            sent = st.checkbox(
                                "✓ Sent" if is_sent else "Mark Sent",
                                value=is_sent,
                                key=f"sent_{student_id}"
                            )
                            st.session_state.sent_status[student_id] = sent
                        
                        # Show grade summary preview in expander
                        with st.expander("👁️ Preview Grade Summary"):
                            st.text_area(
                                "Grade Summary",
                                student_data["Grade Summary"],
                                height=300,
                                key=f"preview_{student_id}",
                                label_visibility="collapsed"
                            )
                        
                        st.markdown("---")
                
                # Download CSV option
                st.markdown("### 💾 Export Options")
                col1, col2 = st.columns(2)
                
                with col1:
                    output_df = pd.DataFrame(st.session_state.generated_data)
                    output_df = output_df.drop('student_id', axis=1)
                    csv_buffer = StringIO()
                    output_df.to_csv(csv_buffer, index=False, quoting=csv.QUOTE_ALL)
                    csv_string = csv_buffer.getvalue()
                    
                    st.download_button(
                        label="⬇️ Download All Emails (CSV)",
                        data=csv_string,
                        file_name="hubspot_import.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # Export sent status log
                    sent_log = []
                    for student in st.session_state.generated_data:
                        sent_log.append({
                            "Name": f"{student['Student Name']}",
                            "Sent": "Yes" if st.session_state.sent_status.get(student['student_id'], False) else "No"
                        })
                    
                    log_df = pd.DataFrame(sent_log)
                    log_buffer = StringIO()
                    log_df.to_csv(log_buffer, index=False)
                    
                    st.download_button(
                        label="📊 Download Send Log",
                        data=log_buffer.getvalue(),
                        file_name="email_send_log.csv",
                        mime="text/csv"
                    )
                
    except FileNotFoundError:
        st.error("Error: Could not find the uploaded file")
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
else:
    st.info("👆 Upload your CSV file to get started")
    
    # Show example format
    st.markdown("---")
    st.subheader("📋 Expected CSV Format")
    example_data = {
        "Student Name": ["John Doe", "Jane Smith"],
        "Total Points": ["-", "-"],
        "Starter Pack Quiz": ["5", "Late: 4"],
        "Assignment 1": ["5", "Missing"],
        "Assignment 2": ["15", "Not Graded Yet"],
        "Assignment 3": ["18", "15"],
        "Mid Course Feedback Form": ["2", "2"],
        "Assignment 4": ["-", "-"],
        "Assignment 5": ["-", "-"],
        "Assignment 6": ["-", "-"],
        "End Course Feedback Form": ["-", "-"]
    }
    st.dataframe(pd.DataFrame(example_data))

# Footer
st.markdown("---")
st.markdown("Made for Comic Book Writing Course | Enhanced with Copy & Track Features")
