import streamlit as st
import pandas as pd
import csv
from io import StringIO

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
    "Assignment 4": {"max_points": 20, "assigned": False},
    "Assignment 5": {"max_points": 20, "assigned": False},
    "Assignment 6": {"max_points": 20, "assigned": False},
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
        return f"   * {assignment_name}: worth {max_points} points"
    
    points, status = parse_grade(grade_value)
    
    if status == "Graded":
        return f"   * {assignment_name}: {points}/{max_points} points"
    elif status == "Done Late":
        if points is not None:
            return f"   * {assignment_name}: {points}/{max_points} points (Done Late)"
        else:
            return f"   * {assignment_name}: Done Late/{max_points} points"
    elif status == "Missing":
        return f"   * {assignment_name}: Missing/{max_points} points"
    elif status == "Not Graded Yet":
        return f"   * {assignment_name}: Not yet graded/{max_points} points"
    else:
        return f"   * {assignment_name}: _/{max_points} points"

def calculate_total_points(row):
    """Calculate total points earned so far."""
    total = 0
    for assignment, config in ASSIGNMENTS.items():
        if config["assigned"]:
            grade_value = row.get(assignment)
            points, status = parse_grade(grade_value)
            if points is not None and status in ["Graded", "Done Late"]:
                total += points
    return total

def generate_email_body(row):
    """Generate personalized email body for a student."""
    first_name = row["First Name"]
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
    
    email_body = f"""Hey {first_name},

I hope you're doing well! I am reaching out to you because we've passed Class #9, and I wanted to check in with a quick progress update and see how things are going for you in our Comic Book Writing course.

Your current progress is summarized below. Please note this only reflects the assignments that have been graded so far. There are still assignments that haven't been assigned or graded!

Current Total: {total_points} points

Progress so far:
{progress_section}

Upcoming Assignments:
{upcoming_section}

IMPORTANT: Keep in mind that the minimum scores for our two certificate types are:
   1. Certificate of Completion: 80+ points total
   2. Certificate of Participation: 40 to 79 points total

Click here to view step-by-step instructions on checking your grades and calculating your points in Google Classroom.

If you'd ever like to discuss your assignments or the possibility of extensions, please don't hesitate to reach out — I'm happy to help.

Finally, I'd love to hear how the course has been going so far — what you've enjoyed, what's been most useful, or if there's anything we could improve. If you'd prefer to talk it through, we can also schedule a quick phone call. To schedule a phone call with me, click here.

Best regards,"""
    
    return email_body

# Streamlit UI
st.title("📧 Student Progress Email Generator")
st.markdown("### Comic Book Writing Course")

st.markdown("""
Upload your exported Google Sheets CSV file, and this tool will automatically generate personalized emails for each student.
""")

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

# File uploader
uploaded_file = st.file_uploader("Upload Student Grades CSV", type=['csv'])

if uploaded_file is not None:
    try:
        # Read the CSV
        df = pd.read_csv(uploaded_file)
        
        # Verify required columns
        required_columns = ["Last Name", "First Name", "Email Address"]
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
                    email_body = generate_email_body(row)
                    total_points = calculate_total_points(row)
                    
                    results.append({
                        "Email": row["Email Address"],
                        "First Name": row["First Name"],
                        "Last Name": row["Last Name"],
                        "Subject": "Comic Book Writing Course - Progress Update",
                        "Email Body": email_body,
                        "Total Points": total_points
                    })
                    
                    progress_bar.progress((idx + 1) / len(df))
                    status_text.text(f"Processing {idx + 1}/{len(df)}: {row['First Name']} {row['Last Name']}")
                
                status_text.text("✅ All emails generated!")
                
                # Create output dataframe
                output_df = pd.DataFrame(results)
                
                # Display statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Students", len(results))
                with col2:
                    avg_points = output_df["Total Points"].mean()
                    st.metric("Average Points", f"{avg_points:.1f}")
                with col3:
                    completion_eligible = len(output_df[output_df["Total Points"] >= 80])
                    st.metric("On Track for Completion", completion_eligible)
                
                # Show sample email
                st.markdown("---")
                st.subheader("📬 Sample Email Preview")
                sample_student = st.selectbox(
                    "Select a student to preview their email:",
                    output_df["First Name"] + " " + output_df["Last Name"]
                )
                
                sample_idx = output_df.index[output_df["First Name"] + " " + output_df["Last Name"] == sample_student][0]
                sample_email = output_df.iloc[sample_idx]
                
                st.text_area("Email Body", sample_email["Email Body"], height=400)
                
                # Download button
                st.markdown("---")
                csv_buffer = StringIO()
                output_df.to_csv(csv_buffer, index=False, quoting=csv.QUOTE_ALL)
                csv_string = csv_buffer.getvalue()
                
                st.download_button(
                    label="⬇️ Download HubSpot Import CSV",
                    data=csv_string,
                    file_name="hubspot_import.csv",
                    mime="text/csv",
                    type="primary"
                )
                
                st.success("🎉 Ready to import into HubSpot!")
                
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
else:
    st.info("👆 Upload your CSV file to get started")
    
    # Show example format
    st.markdown("---")
    st.subheader("📋 Expected CSV Format")
    example_data = {
        "Last Name": ["Doe", "Smith"],
        "First Name": ["John", "Jane"],
        "Email Address": ["john@example.com", "jane@example.com"],
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
st.markdown("Made for Comic Book Writing Course | Need help? Contact your administrator")
