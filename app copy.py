from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from pdfminer.high_level import extract_text
import json
import google.generativeai as genai
import os

from IPython.display import display
from IPython.display import Markdown
import pathlib
import textwrap

# peompts for resume review
prompt1 = """
Imagine you are a hiring manager tasked with selecting candidates for a prestigious position within your company.
You've received a stack of resumes from qualified applicants, and your goal is to identify the most promising candidates. 
Take a close look at one of the resumes provided and analyze it critically. Consider the candidate's qualifications, experiences, skills, and achievements.
What stands out to you as particularly impressive or relevant to the position? Are there any areas where the candidate could improve or provide further clarification?
Additionally, reflect on how well the resume is structured and organized. 
Does it effectively showcase the candidate's strengths and accomplishments? Based on your analysis, make recommendations for
how the candidate could enhance their resume to increase their chances of success in the application process.
"""

prompt2 = """Review the skills section of your resume, taking note of the abilities you've already listed. Next, consider additional skills that are relevan
t to your field or desired career path but may not yet be included. 
Reflect on industry trends, job postings, and the requirements of positions you aspire to. Are there any emerging technologies, software programs, or methodologies
that you could learn to stay competitive? Additionally, think about transferable skills that could be valuable across various roles, such as communication, problem-solving,
or leadership abilities. Once you've identified potential areas for improvement or expansion, create a plan for acquiring these skills. This could involve enrolling in courses, 
participating in workshops or seminars, seeking mentorship, or engaging in self-directed learning. Finally, update your resume to include any new skills you've acquired,
along with relevant examples or experiences that demonstrate your proficiency.
By continually refining and expanding your skill set, you'll enhance your professional capabilities and increase your value as a candidate in the job market.
"""

prompt3 = """
You're tasked with optimizing a resume to ensure it passes through an Applicant Tracking System (ATS) effectively. Begin by reviewing the job description of a specific position 
you're interested in or a role within your industry. Identify key skills, qualifications, and experiences mentioned in the job posting. Then, analyze your resume to determine which
of these keywords are missing or underrepresented. Consider industry-specific terminology, technical skills, certifications, and relevant buzzwords. Once you've identified the gaps,
brainstorm ways to incorporate these keywords naturally into your resume. This could involve revising job descriptions to include relevant keywords, highlighting specific achievements
or experiences that align with the job requirements, or adding a skills section with targeted keywords. Your goal is to ensure that your resume not only accurately represents your
qualifications but also aligns closely with the language and criteria used by the ATS to screen candidates. By strategically incorporating relevant keywords, you'll increase 
the likelihood of your resume being selected for further consideration in the application process.
"""
prompt4 = """"
You're tasked with assessing the suitability of a resume for a specific job opening. Begin by carefully reviewing the job description provided for the position. Identify 
key skills, qualifications, experiences, and other criteria outlined in the job posting. Next, thoroughly examine the candidate's resume to determine the extent to 
which it aligns with the requirements and preferences specified in the job description. As you evaluate the resume, assign a numerical value or score to each matched 
item, considering the relevance and depth of the candidate's experience in each area. Once you've completed this assessment, calculate the percentage match of 
the resume to the job description by dividing the total number of matched items by the total number of criteria specified in the job posting and multiplying by 100. 
Finally, reflect on the significance of the percentage match in determining the candidate's suitability for the position. Consider any strengths or weaknesses 
identified during the evaluation process and how they may impact the candidate's prospects in the application process. Your goal is to provide a comprehensive 
analysis of the resume's alignment with the job requirements, helping to inform hiring decisions and identify potential areas for improvement in the candidate's application materials.
"""




app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def pdf_to_text_converter(pdf_file):
    text = extract_text(pdf_file)
    
    return text

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            text = pdf_to_text_converter(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Load the JSON data from the file
            with open('config.json') as f:
                config = json.load(f)
            # Get the value of the API_KEY field
            api_key = config['configurations'][0]['env']['API_KEY']
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')

            # Define the prompt based on user input or use a default prompt
            user_input = int(request.form['query_choice'])
            job_description = request.form.get('job_description', '')
            print("User Input:", user_input)
            # prompts = [prompt1, prompt2, prompt3, prompt4]
            # prompt = prompts[user_input - 1]
            
            if user_input == 1:
                response = model.generate_content([prompt1, text, job_description])
            elif user_input == 2:
                response = model.generate_content([prompt2, text, job_description])
            elif user_input == 3:
                response = model.generate_content([prompt3, text, job_description])
            else:
                response = model.generate_content([prompt4, text, job_description])
            

            # Call the API and get the response
            
            # Assuming response is the variable containing the text response from the API

            # Split the response into lines
            response = response.text
            lines = response.split('\n')

            formatted_response = ''
            in_bullet_list = False

            # Iterate through each line and format accordingly
            for line in lines:
                if line.startswith('**') and line.endswith('**'):
                    # Format as heading
                    formatted_response += f'<h2>{line.strip("** ")}</h2>'
                elif line.startswith('*') and line.endswith('*'):
                    if not in_bullet_list:
                        # Start bullet list
                        formatted_response += '<ul>'
                        in_bullet_list = True
                    # Add bullet item
                    formatted_response += f'<li>{line.strip("* ")}</li>'
                elif in_bullet_list:
                    # End bullet list if not a bullet line
                    formatted_response += '</ul>'
                    in_bullet_list = False
                    # Add the line as normal text
                    formatted_response += f'<p>{line}</p>'
                else:
                    # Add the line as normal text
                    formatted_response += f'<p>{line}</p>'

            # Check if the bullet list was still open at the end
            if in_bullet_list:
                formatted_response += '</ul>'

            # Use the formatted_response in your Flask application
            return render_template('result.html', reply=formatted_response)

        else:
            return "Invalid file format."
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
