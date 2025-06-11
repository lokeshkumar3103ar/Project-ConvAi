"""
Convert JSON filled forms to HTML with pre-filled values

This script reads JSON files containing extracted form fields and generates HTML forms
with those values pre-filled. It takes the form template and populates it with data
from the JSON files.
"""

import json
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup

# Configuration paths - made relative to work on any computer
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # Go up one level from python scripts folder

FILLED_FORMS_PATH = os.path.join(PROJECT_ROOT, "ConvAi-IntroEval", "filled_forms")
HTML_TEMPLATE_PATH = os.path.join(PROJECT_ROOT, "extras", "ConvAI_Form_Updated.html")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "ConvAi-IntroEval", "Student_Intro_Eval")

# HTML Template (if the file path doesn't work)
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ConvAI Form</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 20px;
    }
    section {
      margin-bottom: 30px;
    }
    h2 {
      background-color: #f0f0f0;
      padding: 10px;
      border-left: 5px solid #007bff;
    }
    label {
      display: block;
      margin-top: 10px;
      font-weight: bold;
    }
    input, select, textarea {
      width: 100%;
      padding: 8px;
      margin-top: 4px;
      box-sizing: border-box;
    }
  </style>
</head>
<body>

  <h1>ConvAI: HR/Placement Form</h1>
  <section>
    <h2>Personal Details</h2>
    <label>Name</label>
    <input type="text" id="name" name="name" />

    <label>Age</label>
    <input type="number" id="age" name="age" />

    <label>Hometown (auto-filled if mentioned in intro)</label>
    <input type="text" id="hometown" name="hometown" />

    <label>Languages Known</label>
    <input type="text" id="languages" name="languages" />

    <label>Personal Achievements</label>
    <textarea id="personal_achievements" name="personal_achievements"></textarea>

    <label>Professional Status</label>
    <select id="professional_status" name="professional_status">
      <option value="">Select...</option>
      <option value="Fresher">Fresher</option>
      <option value="Experienced">Experienced</option>
    </select>
  </section>

  <section>
    <h2>Personal Traits</h2>
    <label>Personality Traits</label>
    <textarea id="personality_traits" name="personality_traits" placeholder="e.g., adaptive, leader, quick learner, etc."></textarea>
  </section>

  <section>
    <h2>Education Background</h2>
    <label>Degree & Specialization</label>
    <input type="text" id="degree" name="degree" />

    <label>College/University</label>
    <input type="text" id="college" name="college" />

    <label>Year of Graduation</label>
    <input type="text" id="graduation_year" name="graduation_year" />

    <label>CGPA</label>
    <input type="text" id="cgpa" name="cgpa" />

    <label>Certifications & Notable Achievements</label>
    <textarea id="certifications" name="certifications"></textarea>
  </section>

  <section>
    <h2>Skills</h2>
    <label>Technical Skills</label>
    <textarea id="technical_skills" name="technical_skills"></textarea>

    <label>Soft Skills</label>
    <textarea id="soft_skills" name="soft_skills"></textarea>

    <label>Tools & Technologies</label>
    <textarea id="tools_technologies" name="tools_technologies"></textarea>

    <label>Domain Expertise (if applicable)</label>
    <textarea id="domain_expertise" name="domain_expertise"></textarea>
  </section>

  <section>
    <h2>Work Experience</h2>
    <label>Company Name</label>
    <input type="text" id="company_name" name="company_name" />

    <label>Role</label>
    <input type="text" id="role" name="role" />

    <label>Time Period</label>
    <input type="text" id="time_period" name="time_period" />

    <label>Total Years of Experience</label>
    <select id="total_experience" name="total_experience">
      <option value="">Select...</option>
      <option value="<1 year">&lt;1 year</option>
      <option value="1 - 3 years">1 - 3 years</option>
      <option value="3 - 5 years">3 - 5 years</option>
      <option value="5 - 7 years">5 - 7 years</option>
      <option value="7 - 10 years">7 - 10 years</option>
      <option value="10+ years">10+ years</option>
    </select>

    <label>Skills Gained</label>
    <textarea id="skills_gained" name="skills_gained"></textarea>

    <label>Key Responsibilities & Achievements</label>
    <textarea id="responsibilities_achievements" name="responsibilities_achievements"></textarea>
  </section>
  
  <section>
    <h2>Projects</h2>
    <label>Project Name</label>
    <input type="text" id="project_name" name="project_name" />

    <label>Technology/Tools Used</label>
    <input type="text" id="project_technology" name="project_technology" />

    <label>Problem Statement</label>
    <textarea id="problem_statement" name="problem_statement"></textarea>

    <label>Solution Implemented</label>
    <textarea id="solution_implemented" name="solution_implemented"></textarea>

    <label>Outcomes/Accomplishments</label>
    <textarea id="project_outcomes" name="project_outcomes"></textarea>

    <label>Your Role (if team project)</label>
    <textarea id="project_role" name="project_role"></textarea>
  </section>

  <section>
    <h2>Role Expectation</h2>
    <label>Target Job Role</label>
    <input type="text" id="target_job_role" name="target_job_role" placeholder="e.g., Full Stack Developer, Data Analyst, etc." />
  </section>

  <section>
    <h2>Achievements & Activities</h2>
    <label>Professional Achievements</label>
    <textarea id="professional_achievements" name="professional_achievements"></textarea>

    <label>Extracurricular Activities</label>
    <textarea id="extracurricular_activities" name="extracurricular_activities"></textarea>

    <label>Relevant Hobbies</label>
    <textarea id="relevant_hobbies" name="relevant_hobbies"></textarea>
  </section>

  <section>
    <h2>Career Preferences</h2>
    <label>Career Goals</label>
    <textarea id="career_goals" name="career_goals"></textarea>

    <label>Preferred Location</label>
    <select id="preferred_location" name="preferred_location">
      <option value="">Select...</option>
      <option value="Any">Any</option>
      <option value="Chennai">Chennai</option>
      <option value="Bangalore">Bangalore</option>
      <option value="Hyderabad">Hyderabad</option>
      <option value="Mumbai">Mumbai</option>
      <option value="Delhi">Delhi</option>
      <option value="Pune">Pune</option>
    </select>

    <label>Willingness to Relocate</label>
    <input type="radio" id="relocate_yes" name="relocate" value="Yes" /> Yes
    <input type="radio" id="relocate_no" name="relocate" value="No" /> No

    <label>Work Environment Preference</label>
    <input type="radio" id="work_env_remote" name="work_env" value="Remote" /> Remote
    <input type="radio" id="work_env_hybrid" name="work_env" value="Hybrid" /> Hybrid
    <input type="radio" id="work_env_onsite" name="work_env" value="On-site" /> On-site

    <label>Expected Salary Range</label>
    <select id="salary_range" name="salary_range">
      <option value="">Select...</option>
      <option value="<3 LPA">&lt;3 LPA</option>
      <option value="3 - 5 LPA">3 - 5 LPA</option>
      <option value="5 - 7 LPA">5 - 7 LPA</option>
      <option value="7 - 10 LPA">7 - 10 LPA</option>
      <option value="10 - 15 LPA">10 - 15 LPA</option>
      <option value="15 - 20 LPA">15 - 20 LPA</option>
      <option value="20+ LPA">20+ LPA</option>
    </select>
  </section>

  <button type="submit">Submit</button>

</body>
</html>'''


def extract_field_value(text, field_pattern):
    """Extract specific field value from the extracted fields text"""
    try:
        # More flexible pattern matching
        patterns = [
            rf"{field_pattern}[:\-]\s*([^\n\r]+)",
            rf"{field_pattern}[:\-]\s*(.+?)(?:\n|$)",
            rf"- {field_pattern}[:\-]\s*([^\n\r]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                # Clean up common artifacts
                value = re.sub(r'^[:\-\s]+', '', value)  # Remove leading colons, dashes, spaces
                value = re.sub(r'\s+', ' ', value)  # Normalize whitespace
                return value
        return ""
    except Exception as e:
        print(f"Error extracting {field_pattern}: {e}")
        return ""


def parse_json_fields(json_data):
    """Parse JSON data and extract structured fields"""
    extracted_text = json_data.get('extracted_fields', '')
    
    # Define field mappings from JSON to HTML form fields
    field_mappings = {
        'name': ['Name', 'Full Name'],
        'age': ['Age'],
        'hometown': ['Hometown', 'Location', 'City'],
        'languages': ['Languages known', 'Languages'],
        'personal_achievements': ['Personal achievements', 'Achievements'],
        'professional_status': ['Professional Status'],
        'personality_traits': ['Personality Traits', 'Personal Traits'],
        'degree': ['Degree & specialization', 'Degree', 'Education'],
        'college': ['College/university', 'University', 'College'],
        'graduation_year': ['Year of graduation', 'Graduation year'],
        'cgpa': ['CGPA', 'GPA'],
        'certifications': ['Notable achievements/certifications', 'Certifications'],
        'technical_skills': ['Technical skills'],
        'soft_skills': ['Soft skills'],
        'tools_technologies': ['Tools & technologies', 'Tools', 'Technologies'],
        'domain_expertise': ['Domain expertise'],
        'company_name': ['Company name'],
        'role': ['Role', 'Position'],
        'time_period': ['Time period', 'Duration'],
        'total_experience': ['Total years of experience', 'Experience'],
        'skills_gained': ['Skills gained'],
        'responsibilities_achievements': ['Key responsibilities & achievements', 'Responsibilities'],
        'project_name': ['Project name'],
        'project_technology': ['Technology/tools used', 'Technologies used'],
        'problem_statement': ['Problem statement'],
        'solution_implemented': ['Solution implemented'],
        'project_outcomes': ['Outcomes/accomplishments', 'Outcomes'],
        'project_role': ['Your role'],
        'target_job_role': ['Target Job Role', 'Target role'],
        'professional_achievements': ['Professional achievements'],
        'extracurricular_activities': ['Extracurricular activities'],
        'relevant_hobbies': ['Relevant hobbies', 'Hobbies'],
        'career_goals': ['Career goals'],
        'preferred_location': ['Preferred location'],
        'relocate': ['Willingness to relocate'],
        'work_env': ['Work environment preference'],
        'salary_range': ['Expected Salary Range', 'Salary']
    }
    
    parsed_fields = {}
    
    for field_id, patterns in field_mappings.items():
        for pattern in patterns:
            value = extract_field_value(extracted_text, pattern)
            if value:
                parsed_fields[field_id] = value
                break
        if field_id not in parsed_fields:
            parsed_fields[field_id] = ""
    
    # Additional logic for fields that may not be explicitly labeled
    # Extract relocate willingness from preferred location or other text
    if not parsed_fields.get('relocate'):
        if 'willing to relocate' in extracted_text.lower() or 'open to relocating' in extracted_text.lower():
            parsed_fields['relocate'] = 'Yes'
        elif 'not willing to relocate' in extracted_text.lower():
            parsed_fields['relocate'] = 'No'
    
    # Extract work environment preference
    if not parsed_fields.get('work_env'):
        if 'remote' in extracted_text.lower() and 'hybrid' in extracted_text.lower() and 'on-site' in extracted_text.lower():
            parsed_fields['work_env'] = 'Any'
        elif 'remote' in extracted_text.lower():
            parsed_fields['work_env'] = 'Remote'
        elif 'hybrid' in extracted_text.lower():
            parsed_fields['work_env'] = 'Hybrid'
        elif 'on-site' in extracted_text.lower() or 'onsite' in extracted_text.lower():
            parsed_fields['work_env'] = 'On-site'
    
    return parsed_fields


def populate_html_form(html_template, field_data):
    """Populate HTML form with extracted field data"""
    # Use string replacement instead of BeautifulSoup to preserve formatting
    html_content = html_template
    
    for field_id, value in field_data.items():
        if not value:
            continue
        
        # Escape HTML special characters in value
        escaped_value = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
        
        # Replace input fields
        input_pattern = f'<input([^>]*?)id="{field_id}"([^>]*?)/?>'
        input_replacement = f'<input\\1id="{field_id}"\\2value="{escaped_value}" />'
        html_content = re.sub(input_pattern, input_replacement, html_content)
        
        # Replace textarea fields
        textarea_pattern = f'<textarea([^>]*?)id="{field_id}"([^>]*?)></textarea>'
        textarea_replacement = f'<textarea\\1id="{field_id}"\\2>{escaped_value}</textarea>'
        html_content = re.sub(textarea_pattern, textarea_replacement, html_content)
        
        # Handle select fields with specific options
        if field_id == 'professional_status':
            if 'fresher' in value.lower():
                html_content = html_content.replace('<option value="Fresher">Fresher</option>', 
                                                  '<option value="Fresher" selected>Fresher</option>')
            elif 'experienced' in value.lower():
                html_content = html_content.replace('<option value="Experienced">Experienced</option>', 
                                                  '<option value="Experienced" selected>Experienced</option>')
        
        elif field_id == 'total_experience':
            if '<1' in value or 'intern' in value.lower():
                html_content = html_content.replace('<option value="<1 year">&lt;1 year</option>', 
                                                  '<option value="<1 year" selected>&lt;1 year</option>')
            elif '1' in value and '3' in value:
                html_content = html_content.replace('<option value="1 - 3 years">1 - 3 years</option>', 
                                                  '<option value="1 - 3 years" selected>1 - 3 years</option>')
        
        elif field_id == 'preferred_location':
            if 'chennai' in value.lower():
                html_content = html_content.replace('<option value="Chennai">Chennai</option>', 
                                                  '<option value="Chennai" selected>Chennai</option>')
            elif 'bangalore' in value.lower():
                html_content = html_content.replace('<option value="Bangalore">Bangalore</option>', 
                                                  '<option value="Bangalore" selected>Bangalore</option>')
            elif 'any' in value.lower() or 'remote' in value.lower():
                html_content = html_content.replace('<option value="Any">Any</option>', 
                                                  '<option value="Any" selected>Any</option>')
        
        elif field_id == 'salary_range':
            if '8' in value and '12' in value:
                html_content = html_content.replace('<option value="7 - 10 LPA">7 - 10 LPA</option>', 
                                                  '<option value="7 - 10 LPA" selected>7 - 10 LPA</option>')
                html_content = html_content.replace('<option value="10 - 15 LPA">10 - 15 LPA</option>', 
                                                  '<option value="10 - 15 LPA" selected>10 - 15 LPA</option>')
        
        # Handle radio buttons
        if field_id == 'relocate':
            if 'yes' in value.lower():
                html_content = html_content.replace('<input type="radio" id="relocate_yes" name="relocate" value="Yes" />', 
                                                  '<input type="radio" id="relocate_yes" name="relocate" value="Yes" checked />')
            elif 'no' in value.lower():
                html_content = html_content.replace('<input type="radio" id="relocate_no" name="relocate" value="No" />', 
                                                  '<input type="radio" id="relocate_no" name="relocate" value="No" checked />')
        
        elif field_id == 'work_env':
            if 'remote' in value.lower():
                html_content = html_content.replace('<input type="radio" id="work_env_remote" name="work_env" value="Remote" />', 
                                                  '<input type="radio" id="work_env_remote" name="work_env" value="Remote" checked />')
            elif 'hybrid' in value.lower():
                html_content = html_content.replace('<input type="radio" id="work_env_hybrid" name="work_env" value="Hybrid" />', 
                                                  '<input type="radio" id="work_env_hybrid" name="work_env" value="Hybrid" checked />')
            elif 'on-site' in value.lower() or 'onsite' in value.lower():
                html_content = html_content.replace('<input type="radio" id="work_env_onsite" name="work_env" value="On-site" />', 
                                                  '<input type="radio" id="work_env_onsite" name="work_env" value="On-site" checked />')
    
    return html_content


def extract_date_from_filename(filename):
    """Extract date from filename like form_20241201_123456.json"""
    match = re.search(r'(\d{8})', filename)
    if match:
        return match.group(1)
    return datetime.now().strftime('%Y%m%d')


def process_json_files():
    """Process all JSON files in the filled forms directory structure"""
    print(f"Script directory: {SCRIPT_DIR}")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Looking for files in: {FILLED_FORMS_PATH}")
    print(f"Template path: {HTML_TEMPLATE_PATH}")
    print(f"Output path: {OUTPUT_PATH}")
    
    if not os.path.exists(FILLED_FORMS_PATH):
        print(f"Error: Filled forms directory not found: {FILLED_FORMS_PATH}")
        print("Please ensure the directory structure is correct relative to this script.")
        return
    
    # Create output directory if it doesn't exist
    try:
        os.makedirs(OUTPUT_PATH, exist_ok=True)
        print(f"Output directory ready: {OUTPUT_PATH}")
    except Exception as e:
        print(f"Error creating output directory: {e}")
        return
    
    # Look for roll number subdirectories
    total_processed = 0
    for item in os.listdir(FILLED_FORMS_PATH):
        roll_path = os.path.join(FILLED_FORMS_PATH, item)
        
        # Skip if not a directory
        if not os.path.isdir(roll_path):
            continue
        
        roll_number = item
        print(f"\nProcessing roll number: {roll_number}")
        
        # Get all form JSON files in this roll number directory
        json_files = [f for f in os.listdir(roll_path) 
                      if f.startswith('form_') and f.endswith('.json')]
        
        if not json_files:
            print(f"No form JSON files found for {roll_number}")
            continue
        
        print(f"Found {len(json_files)} JSON files for {roll_number}")
        
        for json_file in json_files:
            json_path = os.path.join(roll_path, json_file)
            
            try:
                print(f"Processing: {json_file}")
                
                # Read JSON data
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # Parse fields from JSON
                field_data = parse_json_fields(json_data)
                
                # Load HTML template
                try:
                    if os.path.exists(HTML_TEMPLATE_PATH):
                        with open(HTML_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
                            html_template = f.read()
                        print(f"Using template file: {HTML_TEMPLATE_PATH}")
                    else:
                        html_template = HTML_TEMPLATE
                        print(f"Using embedded template (file not found: {HTML_TEMPLATE_PATH})")
                except Exception as e:
                    print(f"Error reading template, using embedded: {e}")
                    html_template = HTML_TEMPLATE
                
                # Populate HTML form
                populated_html = populate_html_form(html_template, field_data)
                
                # Extract date from filename
                date_str = extract_date_from_filename(json_file)
                
                # Generate output filename as rollnumber_date.html
                output_filename = f"{roll_number}_{date_str}.html"
                output_path = os.path.join(OUTPUT_PATH, output_filename)
                
                # Save populated HTML
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(populated_html)
                
                print(f"Generated: {output_filename}")
                total_processed += 1
                
                # Print summary of extracted fields
                print("Extracted fields summary:")
                for field, value in field_data.items():
                    if value:
                        print(f"  {field}: {value[:50]}{'...' if len(value) > 50 else ''}")
                print("-" * 50)
                
            except Exception as e:
                print(f"Error processing {json_file}: {e}")
                continue
    
    if total_processed == 0:
        print("No files were processed. Check the directory structure.")
        print("Expected structure: filled_forms/rollnumber/form_*.json")


def main():
    """Main function to run the conversion process"""
    print("ConvAI Form JSON to HTML Converter")
    print("=" * 40)
    
    process_json_files()
    
    print("Conversion completed!")
    print(f"Output files saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
