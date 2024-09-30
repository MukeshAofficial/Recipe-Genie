from flask import Flask, render_template, jsonify, request ,redirect, url_for
import requests
import google.generativeai as genai
import json
from gtts import gTTS
import base64
import io
import PIL
from PIL import Image


app = Flask(__name__)

genai.configure(api_key="AIzaSyAbmCYsZsjfCPf-uakFksDglYasW4EsehE")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/Genie')
def Genie():
    return render_template('Genie.html')


def strip_code(response_text):
    response_text = response_text.strip()
    if response_text.startswith('```json') and response_text.endswith('```'):
        return response_text[7:-3].strip()
    return response_text

@app.route('/generate_content', methods=['POST'])
def generate_content():
    data = request.json
    title = data.get('title')

    # AI Model Prompt for generating recipe content
    prompt = f"Provide a YouTube video link for '{title}' https://www.youtube.com/watch?v=95BCU1n268w recipe. Include the ingredients, instructions, and nutrition facts.Dont use symbol like Apostrophe Respond in JSON format as follows: \
    {{'video_link': 'YouTube video link', 'ingredients': ['ingredient1', 'ingredient2'], 'instructions': 'step by step instructions', 'nutrition': {{'Calories': 'value', 'Protein': 'value', etc.}}}}"

    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    print(response.text)

    # Extract the AI's generated content
    try:
        response_text = response.text
        response_text = strip_code(response_text)
        # Assuming the response is already in JSON format
        content = json.loads(response_text)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to generate content"}), 500

    return jsonify(content)



# Function to fetch the first 100 meals from TheMealDB
def fetch_meals(search_query=""):
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={search_query}"
    response = requests.get(url)
    data = response.json()
    
    # Return meals, limiting to 100 if available
    meals = data['meals'] if data and data['meals'] else []
    return meals[:100]

# Home route
@app.route('/meals')
def meals():
    meals = fetch_meals()  # Fetch the first 100 meals
    return render_template('meals.html', meals=meals)

# Endpoint to fetch detailed recipe information by ID
@app.route('/recipe/<meal_id>')
def get_recipe(meal_id):
    response = requests.get(f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}")
    meal_data = response.json()
    
    if meal_data and meal_data['meals']:
        return jsonify(meal_data['meals'][0])
    else:
        return jsonify({}), 404


@app.route('/bookmarks')
def bookmark():
    return render_template('bookmarks.html')
# Endpoint to search for recipes by name
@app.route('/search')
def search_recipe():
    query = request.args.get('query', '')
    meals = fetch_meals(query)
    return jsonify(meals)

@app.route('/preferences')
def preferences():
    return render_template('preference.html')


@app.route('/preference', methods=['POST'])
def preference():
    data = request.json
    meal_type = data.get('meal_type')
    food_type = data.get('food_type')
    flavors = data.get('flavors', [])
    cooking_time = data.get('cooking_time')

    # AI Model Prompt for generating recipe content
    prompt = (
        f"Generate a recipe for a {meal_type} that is {food_type}. "
        f"Include flavor preferences: {', '.join(flavors)}. "
        f"Please ensure the cooking time does not exceed {cooking_time} minutes. "
        f"Provide the recipe in JSON format, including ingredients, instructions, and nutrition facts."
    )

    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    print(response.text)

    # Extract the AI's generated content
    try:
        response_text = response.text
        # Assuming the response is already in JSON format
        response_text = strip_code(response_text)
        content = json.loads(response_text)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to generate content"}), 500

    return jsonify(content)


@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    data = request.json
    user_message = data['message']
    model = genai.GenerativeModel('gemini-1.5-flash')
    rply = model.generate_content(f"{user_message}  answer in   10 lines without any */ symbols for this recipe or cooking related question")

    return jsonify({'response': rply.text})

@app.route('/meal-plan')
def meal_plan():
    return render_template('meal-planner.html')


@app.route('/generate_meal_plan', methods=['POST', 'GET'])
def generate_meal():
    prompt = "Provide a 7-day meal plan for indian tamil nadu with just the dish names for breakfast, lunch, and dinner for each day. Format the response in JSON as follows: \
    {'meal_plan': [ \
        {'day': 'Day 1', 'breakfast': 'dish_name', 'lunch': 'dish_name', 'dinner': 'dish_name'}, \
        {'day': 'Day 2', 'breakfast': 'dish_name', 'lunch': 'dish_name', 'dinner': 'dish_name'}, \
        {'day': 'Day 3', 'breakfast': 'dish_name', 'lunch': 'dish_name', 'dinner': 'dish_name'}, \
        {'day': 'Day 4', 'breakfast': 'dish_name', 'lunch': 'dish_name', 'dinner': 'dish_name'}, \
        {'day': 'Day 5', 'breakfast': 'dish_name', 'lunch': 'dish_name', 'dinner': 'dish_name'}, \
        {'day': 'Day 6', 'breakfast': 'dish_name', 'lunch': 'dish_name', 'dinner': 'dish_name'}, \
        {'day': 'Day 7', 'breakfast': 'dish_name', 'lunch': 'dish_name', 'dinner': 'dish_name'} \
    ]}"

    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    print(response.text)

    # Extract the AI's generated content
    try:
        response_text = response.text
        # Ensure the response is in proper JSON format
        response_text = response_text.replace("'", "\"")  # Replace single quotes with double quotes
        response_text = strip_code(response_text)  # Assuming this function removes unnecessary code blocks
        content = json.loads(response_text)  # Parse JSON

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to generate content"}), 500

    return jsonify(content)

@app.route('/ingredients-image')
def food():
    return render_template('ingredients.html')

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        # Get the image data from the request
        data = request.json
        image_data = data.get('image')

        # Decode the base64 image data
        image_data = image_data.split(',')[1]
        image_binary = base64.b64decode(image_data)

        # Load the image
        img = PIL.Image.open(io.BytesIO(image_binary))

        # Use Generative AI model to generate a list of food items and instructions from the image
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(["Generate a food recipe with instructions from given ingredients available in this  image  dont use any asterisk symbols in response", img], stream=True)
        response.resolve()
        rply=response.text
        
        with open('static/recipe.txt', 'w') as f:
            f.write(rply)

        # Generate speech from the extracted text
        tts = gTTS(text=response.text, lang='en')

        # Save the speech to a file
        audio_path = 'static/output.mp3'
        tts.save(audio_path)
        audio_url = f"/{audio_path}"
        
        return redirect(url_for('result'))

@app.route('/result')
def result():
    audio_url = "output.mp3"
    with open('static/recipe.txt', 'r') as f:
        recipe_content = f.read()

    return render_template('result.html',recipe=recipe_content, audio=audio_url)

@app.route('/food-image')
def taste():
    return render_template('food-recipe.html')

@app.route('/foodupload', methods=['POST'])
def foodupload():
    if request.method == 'POST':
        # Get the image data from the request
        data = request.json
        image_data = data.get('image')

        # Decode the base64 image data
        image_data = image_data.split(',')[1]
        image_binary = base64.b64decode(image_data)

        # Load the image
        img = PIL.Image.open(io.BytesIO(image_binary))

        # Use Generative AI model to generate a list of food items and instructions from the image
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(["Generate a food recipe with instructions  which tastes Similar to this food image  dont use any asterisk symbols in response", img], stream=True)
        response.resolve()
        rply=response.text
        
        with open('static/foodrecipe.txt', 'w') as f:
            f.write(rply)

        # Generate speech from the extracted text
        tts = gTTS(text=response.text, lang='en')

        # Save the speech to a file
        audio_path = 'static/output.mp3'
        tts.save(audio_path)
        audio_url = f"/{audio_path}"
        
        return redirect(url_for('results'))

@app.route('/results')
def results():
    audio_urls = "output.mp3"
    with open('static/foodrecipe.txt', 'r') as f:
        recipe_contents = f.read()

    return render_template('food-result.html',recipe=recipe_contents, audio=audio_urls)


@app.route('/compare')
def compare():
    return render_template('cost.html')


@app.route('/generate', methods=['POST'])
def generate_html():
    prompt = request.form['prompt']
    model = genai.GenerativeModel('gemini-1.5-flash')
    rply = model.generate_content("Generate both html and css code in single file for cost comparision website where it is an indian tamil nadu food chennai Give cost of making it home " + prompt + " , Give complete code I need only code and no explanation")
    html_content = rply.text

    with open("templates/index1.html", "w") as file:
        file.write(html_content)

    return redirect(url_for('output'))

@app.route('/output')
def output():
    return render_template('index1.html')


@app.route('/gpt', methods=['GET', 'POST'])
def gpt():
    response_text = ""
    audio=''
    if request.method == 'POST':
        # Get transcribed text from the form
        transcribed_text = request.form.get('transcribed_text')
          
        # Generate response using the transcribed text
        if transcribed_text:
            # Generate response using Generative AI model
            model = genai.GenerativeModel('gemini-pro')
            rply = model.generate_content("Tell me how to make this food give me complete recipe without usingn any symbols "+ transcribed_text)
            response_text = rply.text
            print(response_text)
            # Convert response text to speech
            tts = gTTS(text=response_text, lang='en')
            tts.save('response.mp3')
            # Encode the audio file as base64
            with open("response.mp3", "rb") as audio_file:
                 encoded_string = base64.b64encode(audio_file.read()).decode('utf-8')
        else:
            response_text = "No input provided."
            encoded_string = ""
        
        # Return the response to the client
        return render_template('gpt.html', response=response_text, audio=encoded_string)
    else:
        # If it's a GET request, render the form
        return render_template('gpt.html')


if __name__ == '__main__':
    app.run(debug=True)
