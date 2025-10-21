# Initialize session state for assignment configuration
if 'assignments_config' not in st.session_state:
    st.session_state.assignments_config = ASSIGNMENTS.copy()

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Assignment customization section
    st.markdown("### 📝 Customize Assignments")
    
    with st.expander("✏️ Edit Assignments", expanded=False):
        st.markdown("**Modify existing assignments or add new ones:**")
        
        # Edit existing assignments
        assignments_to_delete = []
        for idx, (name, config) in enumerate(list(st.session_state.assignments_config.items())):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                new_name = st.text_input(
                    "Name",
                    value=name,
                    key=f"name_{idx}",
                    label_visibility="collapsed",
                    placeholder="Assignment name"
                )
            
            with col2:
                new_points = st.number_input(
                    "Points",
                    value=config["max_points"],
                    min_value=0,
                    step=1,
                    key=f"points_{idx}",
                    label_visibility="collapsed"
                )
            
            with col3:
                new_assigned = st.checkbox(
                    "Assigned",
                    value=config["assigned"],
                    key=f"assigned_{idx}"
                )
            
            with col4:
                if st.button("🗑️", key=f"delete_{idx}", help="Delete assignment"):
                    assignments_to_delete.append(name)
            
            # Update the assignment if name or values changed
            if new_name != name:
                st.session_state.assignments_config.pop(name)
                st.session_state.assignments_config[new_name] = {
                    "max_points": new_points,
                    "assigned": new_assigned
                }
            else:
                st.session_state.assignments_config[name] = {
                    "max_points": new_points,
                    "assigned": new_assigned
                }
        
        # Delete marked assignments
        for name in assignments_to_delete:
            if name in st.session_state.assignments_config:
                st.session_state.assignments_config.pop(name)
                st.rerun()
        
        st.markdown("---")
        
        # Add new assignment
        st.markdown("**Add New Assignment:**")
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            new_assignment_name = st.text_input(
                "New Assignment Name",
                key="new_assignment_name",
                label_visibility="collapsed",
                placeholder="New assignment name"
            )
        
        with col2:
            new_assignment_points = st.number_input(
                "Points",
                value=10,
                min_value=0,
                step=1,
                key="new_assignment_points",
                label_visibility="collapsed"
            )
        
        with col3:
            new_assignment_assigned = st.checkbox(
                "Assigned",
                value=False,
                key="new_assignment_assigned"
            )
        
        with col4:
            if st.button("➕", key="add_assignment", help="Add assignment"):
                if new_assignment_name and new_assignment_name not in st.session_state.assignments_config:
                    st.session_state.assignments_config[new_assignment_name] = {
                        "max_points": new_assignment_points,
                        "assigned": new_assignment_assigned
                    }
                    st.rerun()
                elif new_assignment_name in st.session_state.assignments_config:
                    st.error("Assignment already exists!")
        
        # Reset to defaults button
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            st.session_state.assignments_config = ASSIGNMENTS.copy()
            st.rerun()
    
    # Show current configuration summary
    with st.expander("👁️ View Current Setup"):
        assigned_assignments = {k: v for k, v in st.session_state.assignments_config.items() if v["assigned"]}
        upcoming_assignments = {k: v for k, v in st.session_state.assignments_config.items() if not v["assigned"]}
        
        st.markdown("**Assigned Assignments:**")
        for name, config in assigned_assignments.items():
            st.write(f"• {name}: {config['max_points']} points")
        
        st.markdown("**Upcoming Assignments:**")
        for name, config in upcoming_assignments.items():
            st.write(f"• {name}: {config['max_points']} points")
        
        total_assigned_points = sum(c["max_points"] for c in assigned_assignments.values())
        total_all_points = sum(c["max_points"] for c in st.session_state.assignments_config.values())
        st.info(f"📊 Total Assigned: {total_assigned_points} | Total Course: {total_all_points}")
    
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
