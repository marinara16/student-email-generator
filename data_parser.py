import csv
import re
from io import StringIO


def parse_classroom_data(data):
    """
    Parse Google Classroom grade data and convert to CSV format.
    
    Args:
        data (str): Raw text data from Google Classroom
        
    Returns:
        str: CSV formatted string
    """
    # Split data into blocks
    blocks = data.split('\n\n')
    
    # Parse assignments
    course_block = blocks.pop(0)
    assignments = []

    lines = course_block.strip().split('\n')
    for idx, line in enumerate(lines):
        if idx == 0:
            continue
        if 'out of' in line:
            # Extract assignment name and points
            name = lines[idx-1]
            points = line.strip('out of ')
            assignments.append(f"{name} [{points}]")

    
    # Parse student data
    students = []
    for block in blocks:
        lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
        
        if not lines:
            continue

        # Student blocks start with a name
        student_name = lines[0]
        
        # Parse grades from remaining lines
        grades = []
        # Start at third element because 2nd one is overall grade (not necessary)
        i = 2
        while i < len(lines):
            line = lines[i]

            if 'AssignedNo grade' in line:
                grades.append('Pending')
                i += 1
                continue
            
            # Check for "/20No grade" pattern (submitted but not graded)
            if re.match(r'/\d+No grade', line):
                status = 'Submitted'
                next_line = line = lines[i+1]
                if 'Done late' in next_line:
                    status = 'Late'
                grades.append(status)
                i += 1
                continue
            
            # Check for "X out of Y" pattern
            match = re.search(r'^(\d+)\s+(\d+\s+)?out of \d+', line)
            if match:
                grade = match.group(1)
                if grade != '0':
                    grades.append(grade)
                i += 1
                continue
            
            # Check for "0 out of X Draft•Missing" or similar
            if 'Missing' in line:
                grades.append('Missing')
                i += 1
                continue
            
            if 'Excused' in line:
                grades.append('Excused')
                i += 1
                continue

            i += 1
        
        students.append([student_name] + grades)
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    header = ['Student Name'] + assignments
    writer.writerow(header)
    
    # Write student rows
    for student in students:
        # Pad with empty strings if needed
        while len(student) < len(header):
            student.append('')
        writer.writerow(student[:len(header)])
    
    return output.getvalue()


# Example usage:
if __name__ == "__main__":
    # Read the data (you would paste your data here or read from file)
    with open('copypasta.txt', 'r') as f:
        data = f.read()
    
    csv_output = parse_classroom_data(data)
    
    # Write to CSV file
    with open('grades.csv', 'w') as f:
        f.write(csv_output)
    
    print("CSV file created successfully!")
    print("\nPreview:")
    print(csv_output[:500])  # Print first 500 characters
