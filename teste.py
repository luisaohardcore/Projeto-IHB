import google.generativeai as genai
genai.configure(api_key="AIzaSyC4SCIYWPQwMmT7nJdM6tAwarH7N6OxYCM")

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)