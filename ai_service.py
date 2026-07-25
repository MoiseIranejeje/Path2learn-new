from groq import Groq
import os
import re

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

def get_school_recommendation(student_profile: str, schools: list) -> str:
    school_list = "\n".join([
        f"- {s.name} | {s.province} | {s.district} | "
        f"Type: {s.ownership} | Program: {s.education_program} | "
        f"Gender: {s.gender_policy} | Boarding: {s.boarding_policy or 'Unknown'} | "
        f"Tags: {s.tags or 'None'} | Combinations: {s.combinations or 'Not listed'}"
        for s in schools
    ])

    prompt = f"""You are Path2Learn AI, a friendly and knowledgeable school advisor 
helping students and parents in Rwanda choose the right secondary school.

A student has described their situation:
"{student_profile}"

Here are the schools currently in the Path2Learn database:
{school_list}

Based on the student's situation, recommend the 3 most suitable schools from this list.
For each school:
1. State the school name clearly
2. Explain in 2-3 sentences exactly WHY this school fits this specific student
3. Mention one thing they should consider or prepare for

Be warm, encouraging, and practical. Write as if you're a trusted counselor 
who knows both the student and the schools personally.
End with one sentence of general encouragement."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.7
    )

    # Remove markdown stars and hashes from the AI response
    result = response.choices[0].message.content
    result = re.sub(r'\*+', '', result)        # removes ** and *
    result = re.sub(r'#+\s*', '', result)      # removes ## headers
    result = result.strip()
    return result