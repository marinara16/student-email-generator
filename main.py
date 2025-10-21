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

def detect_assignment_columns(df):
    """Automatically detect which columns are assignments (everything except Student Name)."""
    assignment_cols = []
    for col in df.columns:
        if col.strip().lower() != "student name":
            assignment_cols.append(col)
    return assignment_cols

def estimate_max_points(df, column_name):
    """Estimate max points for an assignment from the data."""
    max_val = 0
    for val in df[column_name]:
        if pd.isna(val):
            continue
        val_str = str(val).strip()
        
        # Skip non-numeric statuses
        if val_str.lower() in ["missing", "not submitted", "not graded yet", "ungraded", "pending", "", "-"]:
            continue
        
        # Handle "Late: X" format
        if val_str.lower().startswith("late:"):
            try:
                points = float(val_str.split(":")[1].strip())
                max_val = max(max_val, points)
            except:
                pass
        # Handle numeric values
        else:
            try:
                points = float(val_str)
                max_val = max(max_val, points)
            except:
                pass
    
    # If we found values, round up intelligently
    if max_val > 0:
        if max_val <= 5:
            return max(5, int(max_val))
        elif max_val <= 10:
            return 10
        elif max_val <= 15:
            return 15
        elif max_val <= 20:
            return 20
        elif max_val <= 25:
            return 25
        else:
            # Round up to nearest 5
            return int((max_val + 4) // 5 * 5)
    
    # Default to 10 if we couldn't find any values
    return 10

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

def calculate_total_points(row, assignments_config):
    """Calculate total points earned so far."""
    total = 0
    for assignment, config in assignments_config.items():
        if config["assigned"]:
            grade_value = row.get(assignment)
            if grade_value is not None:
                points, status = parse_grade(grade_value)
                if points is not None and status in ["Graded", "Done Late"]:
                    total += points
    # Return as integer if it's a whole number
    return int(total) if total == int(total) else total

def generate_email_body(row, assignments_config):
    """Generate personalized email body for a student."""
    total_points = calculate_total_points(row, assignments_config)
    
    progress_lines = []
    upcoming_lines = []
    
    for assignment, config in assignments_config.items():
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

def validate_assignments(assignments_config, csv_columns):
    """Validate that all configured assignments exist in CSV."""
    missing_assignments = []
    for assignment_name in assignments_config.keys():
        if assignment_name not in csv_columns:
            missing_assignments.append(assignment_name)
    return missing_assignments

# Initialize session state
if 'sent_status' not in st.session_state:
    st.session_state.sent_status = {}
if 'generated_data' not in st.session_state:
    st.session_state.generated_data = None
if 'assignments_config' not in st.session_state:
    st.session_state.assignments_config = {}
if 'current_df' not in st.session_state:
    st.session_state.current_df = None
if 'last_file_id' not in st.session_state:
    st.session_state.last_file_id = None
if 'csv_columns' not in st.session_state:
    st.session_state.csv_columns = []

# Custom CSS for better styling
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

# Streamlit UI
st.title("📧 Student Grade Summary Generator")
st.markdown("### Quick Grade Snippets for HubSpot")

st.info("💡 **Universal Workflow:** Upload any CSV with student grades. The app auto-detects assignments and lets you configure them!")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Only show assignment customization if CSV is loaded
    if st.session_state.current_df is not None and st.session_state.assignments_config:
        st.markdown("### 📝 Assignment Settings")
        st.markdown("*Adjust points and mark as Assigned/Upcoming*")
        
        with st.expander("✏️ Configure Assignments", expanded=True):
            for idx, (name, config) in enumerate(list(st.session_state.assignments_config.items())):
                st.markdown(f"**{name}**")
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    new_assigned = st.checkbox(
                        "✓ Assigned (graded/grading)",
                        value=config["assigned"],
                        key=f"assigned_{idx}_{name}",
                        help="Check if this assignment has been assigned to students"
                    )
                
                with col2:
                    new_points = st.number_input(
                        "Max Points",
                        value=config["max_points"],
                        min_value=0,
                        step=1,
                        key=f"points_{idx}_{name}",
                        help="Maximum points for this assignment"
                    )
                
                st.session_state.assignments_config[name] = {
                    "max_points": new_points,
                    "assigned": new_assigned
                }
                
                st.markdown("---")
            
            # Add reset button
            if st.button("🔄 Reset to Auto-Detected Values", use_container_width=True):
                if st.session_state.current_df is not None:
                    assignment_columns = detect_assignment_columns(st.session_state.current_df)
                    st.session_state.assignments_config = {}
                    for col in assignment_columns:
                        max_pts = estimate_max_points(st.session_state.current_df, col)
                        has_grades = st.session_state.current_df[col].notna().any()
                        st.session_state.assignments_config[col] = {
                            "max_points": max_pts,
                            "assigned": has_grades
                        }
                    st.rerun()
        
        # Show current configuration summary
        with st.expander("👁️ View Current Setup"):
            assigned_assignments = {k: v for k, v in st.session_state.assignments_config.items() if v["assigned"]}
            upcoming_assignments = {k: v for k, v in st.session_state.assignments_config.items() if not v["assigned"]}
            
            st.markdown("**Assigned Assignments:**")
            if assigned_assignments:
                for name, config in assigned_assignments.items():
                    st.write(f"• {name}: {config['max_points']} points")
            else:
                st.write("_(None marked as assigned yet)_")
            
            st.markdown("**Upcoming Assignments:**")
            if upcoming_assignments:
                for name, config in upcoming_assignments.items():
                    st.write(f"• {name}: {config['max_points']} points")
            else:
                st.write("_(All assignments marked as assigned)_")
            
            total_assigned_points = sum(c["max_points"] for c in assigned_assignments.values())
            total_all_points = sum(c["max_points"] for c in st.session_state.assignments_config.values())
            st.info(f"📊 Total Assigned: {total_assigned_points} | Total Course: {total_all_points}")
    else:
        st.info("📤 Upload a CSV file to configure assignments")
    
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
        
        # Verify Student Name column exists
        if "Student Name" not in df.columns:
            st.error("❌ Missing required column: 'Student Name'")
        else:
            # Auto-detect assignments from CSV columns
            assignment_columns = detect_assignment_columns(df)
            
            if not assignment_columns:
                st.error("❌ No assignment columns detected! CSV should have columns other than 'Student Name'.")
            else:
                # Check if this is a new file by comparing file name or content
                current_file_id = uploaded_file.name + str(len(df))
                
                # Initialize assignment config only for NEW files
                if 'last_file_id' not in st.session_state or st.session_state.last_file_id != current_file_id:
                    st.session_state.assignments_config = {}
                    for col in assignment_columns:
                        max_pts = estimate_max_points(df, col)
                        # Default to "assigned" if there are any grades
                        has_grades = df[col].notna().any()
                        st.session_state.assignments_config[col] = {
                            "max_points": max_pts,
                            "assigned": has_grades
                        }
                    st.session_state.last_file_id = current_file_id
                    st.session_state.current_df = df
                    st.session_state.csv_columns = list(df.columns)
                    st.rerun()  # Rerun to show the detected assignments
                else:
                    # Same file, just update the dataframe reference
                    st.session_state.current_df = df
                    st.session_state.csv_columns = list(df.columns)
                
                st.success(f"✅ Successfully loaded data for {len(df)} students with {len(assignment_columns)} assignments")
                
                # Show detected assignments
                with st.expander("🔍 Detected Assignments from CSV"):
                    st.markdown("*These were auto-detected and configured. Adjust in the sidebar.*")
                    for col in assignment_columns:
                        config = st.session_state.assignments_config.get(col, {})
                        status = "✓ Assigned" if config.get("assigned", False) else "⏳ Upcoming"
                        st.write(f"• **{col}** ({config.get('max_points', 0)} pts) - {status}")
                
                # Show preview
                with st.expander("📊 Preview Student Data"):
                    st.dataframe(df)
            
            # Generate emails button
            if st.button("🚀 Generate Emails", type="primary"):
                # Validate assignments before generating
                missing = validate_assignments(st.session_state.assignments_config, st.session_state.csv_columns)
                
                if missing:
                    st.error(f"⚠️ **Validation Error:** The following assignments in your configuration don't exist in the CSV:\n\n" + 
                            "\n".join([f"• {name}" for name in missing]))
                    st.warning("Please check your sidebar configuration or re-upload your CSV.")
                else:
                    results = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, row in df.iterrows():
                        grade_summary = generate_email_body(row, st.session_state.assignments_config)
                        total_points = calculate_total_points(row, st.session_state.assignments_config)
                        
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
                
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
else:
    st.info("👆 Upload your CSV file to get started")
    
    # Show example format
    st.markdown("---")
    st.subheader("📋 Expected CSV Format")
    st.markdown("Your CSV should have:")
    st.markdown("• **Student Name** column (required)")
    st.markdown("• Any number of assignment columns with any names you choose")
    st.markdown("• Grade values as numbers, 'Late: X', 'Missing', 'Not Graded Yet', or blank")
    
    example_data = {
        "Student Name": ["John Doe", "Jane Smith"],
        "Starter Pack Quiz": ["5", "Late: 4"],
        "Assignment 1": ["5", "Missing"],
        "Assignment 2": ["15", "Not Graded Yet"],
        "Final Project": ["18", "15"]
    }
    st.dataframe(pd.DataFrame(example_data))

# Footer
st.markdown("---")
st.markdown("Made for Any Course | Auto-detects assignments from your CSV")
