import streamlit as st
import random
import google.generativeai as gemini

# Configure Gemini API
gemini.configure(api_key="AIzaSyBSsdS719axuCPO-EtU0IEg2BB1v9gHIg0")
model = gemini.GenerativeModel('gemini-1.5-pro')

fact = None
# Add background image and font
st.markdown(
    """
    <style>
    {
        font-family: "Trajan Pro", serif; /* Change font to Trajan Pro */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Mythology topics
topics = ["Ramayana", "Mahabharata", "Vedas", "Puranas", "Upanishads", "Random"]

# UI Layout
st.title("Indian Mythology Quiz Bot")
st.sidebar.title("Quiz Settings")

# Choose Topic
chosen_topic = st.sidebar.selectbox("Choose a topic:", topics)

# Choose Mode
mode = st.sidebar.radio("Who should ask the questions?", ("Bot Asks", "User Asks"))



# Function to generate content from Gemini API
def generate_from_gemini(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error occurred: {e}")
        return "Error generating content"

if mode == "Bot Asks":
    # Initialize session state for quiz history
    if "quiz_history" not in st.session_state:
        st.session_state.quiz_history = []
    if "current_question_index" not in st.session_state:
        st.session_state.current_question_index = -1

    # Step 3: Choose Question Type
    question_type = st.sidebar.radio("Choose question type:", ("Multiple Choice", "True/False", "Q&A"))
    # Generate a random fact
    fact = st.sidebar.button("Get a random fact")

    # Initialize session state for quiz data
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = {
            "topic": None,
            "question": None,
            "options": None,
            "correct_answer": None,
            "selected_option": None,
            "explanation": None,
            "result_status": None  # Initialize result_status
        }

    # Initialize session state for quiz history and question tracking
    if "previous_questions" not in st.session_state:
        st.session_state.previous_questions = set()

    def generate_new_question(topic, question_type):
        max_retries = 3
        for attempt in range(max_retries):
            if question_type == "Multiple Choice":
                prompt = f"""Create a unique and diverse multiple choice question about {topic}.
Make sure it is different from common or basic questions.
Focus on interesting, specific aspects or lesser-known facts.

Format EXACTLY as follows:
Question: [question text]
Options:
(A) [option A text]
(B) [option B text]
(C) [option C text]
(D) [option D text]
Correct Answer: [A/B/C/D]"""
            elif question_type == "True/False":
                prompt = f"""Create a unique true/false question about {topic}.
Make sure it is different from common or basic questions.
Focus on interesting, specific aspects or lesser-known facts.

Format EXACTLY as follows:
Question: [question text]
Options:
(A) True
(B) False
Correct Answer: [A/B]"""
            elif question_type == "Q&A":
                prompt = f"""Create a fill-in-the-blank question about {topic}.
Make sure it is different from common or basic questions.
Focus on interesting, specific aspects or lesser-known facts.
Use ___ for the blank space.

Format EXACTLY as follows:
Question: [question text with ___]
Correct Answer: [correct answer text]"""
            else:
                # Handle other question types if needed
                continue
        
            response = generate_from_gemini(prompt)

            try:
                lines = [line.strip() for line in response.split('\n') if line.strip()]
                question = lines[0].replace('Question:', '').strip()
                
                # Check if this question is too similar to previous ones
                if question in st.session_state.previous_questions:
                    if attempt == max_retries - 1:
                        st.error("Failed to generate a unique question. Please try again.")
                        return None
                    continue
                
                options = []
                correct_answer = None
                for line in lines[1:]:
                    if line.startswith('(') and ')' in line:
                        opt = line.strip()
                        options.append(opt)
                    elif line.startswith('Correct Answer:'):
                        correct_answer = line.replace('Correct Answer:', '').strip()

                if (question_type == "Multiple Choice" and len(options) != 4) or (question_type == "True/False" and len(options) != 2) or (question_type == "Q&A" and not correct_answer):
                    raise ValueError("Invalid response format")

                # Store the question for future duplicate checking
                st.session_state.previous_questions.add(question)

                return {
                    "topic": topic,
                    "question": question,
                    "options": options if question_type != "Fill in the Blanks" else None,
                    "correct_answer": correct_answer,
                    "selected_option": None,
                    "explanation": None,
                    "result_status": None
                }
            except Exception as e:
                if attempt == max_retries - 1:
                    st.error(f"Failed to parse the question. Please try again. Error: {str(e)}")
                    return None

    # Button to start quiz or generate next question
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.session_state.current_question_index > 0:
            if st.button("Previous Question"):
                if st.session_state.current_question_index > 0:
                    st.session_state.current_question_index -= 1
                    st.session_state.quiz_data = st.session_state.quiz_history[st.session_state.current_question_index]
    
    with col2:
        if st.button("Start Quiz" if st.session_state.current_question_index == -1 else "Next Question"):
            # Handle "Random" topic
            topic = chosen_topic if chosen_topic != "Random" else random.choice(
                ["Ramayana", "Mahabharata", "Vedas", "Puranas", "Upanishads", "Mythological Characters"]
            )
            
            new_question = generate_new_question(topic, question_type)
            if new_question:
                if st.session_state.current_question_index == -1:
                    # First question
                    st.session_state.quiz_history = [new_question]
                    st.session_state.current_question_index = 0
                else:
                    # Next question
                    st.session_state.current_question_index += 1
                    if st.session_state.current_question_index < len(st.session_state.quiz_history):
                        # Replace existing question at current index
                        st.session_state.quiz_history[st.session_state.current_question_index] = new_question
                    else:
                        # Add new question to history
                        st.session_state.quiz_history.append(new_question)
                
                st.session_state.quiz_data = new_question

    # Display current question number if quiz has started
    if st.session_state.current_question_index >= 0:
        st.write(f"Question {st.session_state.current_question_index + 1} of {len(st.session_state.quiz_history)}")

    # Display the question if it exists in session state
    if st.session_state.quiz_data["question"]:
        st.write(f"Topic: {st.session_state.quiz_data['topic']}")
        st.write("Question:", st.session_state.quiz_data["question"])
        
        if question_type == "Q&A":
            # Display text input for fill-in-the-blank question
            user_answer = st.text_input("Your answer:", key=f"fill_in_blank_{st.session_state.current_question_index}")
        else:
            # Display options as radio buttons
            selected_option = st.radio(
                "Select your answer:",
                st.session_state.quiz_data["options"],
                key=f"quiz_options_{st.session_state.current_question_index}",
                index=None
            )

        # Submit button and result display
        if st.button("Submit Answer"):
            if question_type == "Q&A":
                if user_answer:
                    if user_answer.strip().lower() == st.session_state.quiz_data["correct_answer"].strip().lower():
                        st.session_state.quiz_data["result_status"] = "correct"
                    else:
                        st.session_state.quiz_data["result_status"] = ("incorrect", st.session_state.quiz_data["correct_answer"])
                else:
                    st.warning("Please enter an answer before submitting.")
            else:
                if selected_option:
                    try:
                        # Extract the letter from the selected option (A), (B), etc.
                        selected_letter = selected_option.split(")")[0].replace("(", "").strip()
                        correct_letter = st.session_state.quiz_data["correct_answer"].strip()
                        
                        if selected_letter == correct_letter:
                            st.session_state.quiz_data["result_status"] = "correct"
                            st.session_state.quiz_data["correct_option_full"] = selected_option
                        else:
                            try:
                                correct_option = next(opt for opt in st.session_state.quiz_data["options"] 
                                                   if opt.startswith(f"({correct_letter})"))
                                st.session_state.quiz_data["result_status"] = ("incorrect", correct_option)
                                st.session_state.quiz_data["correct_option_full"] = correct_option
                            except StopIteration:
                                st.error("Error processing answer: Could not find correct option")
                    except Exception as e:
                        st.error(f"Error processing answer: {str(e)}")
                else:
                    st.warning("Please select an answer before submitting.")

        # Display result status if available
        if st.session_state.quiz_data["result_status"]:
            if st.session_state.quiz_data["result_status"] == "correct":
                st.success("Correct! ✅")
            elif isinstance(st.session_state.quiz_data["result_status"], tuple):
                st.error(f"Incorrect. The correct answer is: {st.session_state.quiz_data['result_status'][1]}")

        # Explanation button
        if st.button("Get Explanation"):
            if "correct_option_full" not in st.session_state.quiz_data and question_type != "Q&A":
                st.error("Please submit an answer first to get an explanation.")
            else:
                try:
                    correct_option = st.session_state.quiz_data["correct_option_full"] if question_type != "Q&A" else st.session_state.quiz_data["correct_answer"]
                    options_context = "\n".join(st.session_state.quiz_data["options"]) if question_type != "Q&A" else ""
                    
                    explanation_prompt = f"""
                    Based on Hindu mythology, explain:
                    Question: {st.session_state.quiz_data['question']}
                    All Options:
                    {options_context}
                    Correct Answer: {correct_option}
                    
                    Provide a clear explanation that:
                    1. First explains why {correct_option.split(') ')[1] if question_type != "Q&A" else correct_option} is the correct answer
                    """
                    
                    if question_type == "Multiple Choice":
                        explanation_prompt += """
                        2. Then briefly explain why the other options are incorrect
                        """
                    
                    explanation = generate_from_gemini(explanation_prompt)
                    if explanation:
                        st.session_state.quiz_data["explanation"] = explanation
                        st.write("Explanation:", explanation)
                    
                except Exception as e:
                    st.error(f"Error generating explanation: {str(e)}")

        # Quit button to stop the quiz and reset the state
        if st.button("Quit"):
            st.session_state.quiz_history = []
            st.session_state.current_question_index = -1
            st.session_state.quiz_data = {
                "topic": None,
                "question": None,
                "options": None,
                "correct_answer": None,
                "selected_option": None,
                "explanation": None,
                "result_status": None
            }

# ...existing code...

if mode == "User Asks":
    # Initialize session state variables if not already present
    if "user_question" not in st.session_state:
        st.session_state.user_question = ""
    if "answer" not in st.session_state:
        st.session_state.answer = ""
    if "explanation" not in st.session_state:
        st.session_state.explanation = ""

    # Input box for user to ask a question
    st.session_state.user_question = st.text_area("Ask your question to the bot:", value=st.session_state.user_question)

    if st.button("Ask"):
        st.session_state.answer = generate_from_gemini(st.session_state.user_question)
        st.session_state.explanation = ""  # Clear previous explanation

    # Display the answer if available
    if st.session_state.answer:
        st.write(st.session_state.answer)

        # Explanation option
        if st.button("Get Explanation"):
            st.session_state.explanation = generate_from_gemini(
                f"Give a brief contextual explanation about {st.session_state.answer} to the question {st.session_state.user_question}. no need for the any heading."
            )

    # Display the explanation if available
    if st.session_state.explanation:
        st.write(st.session_state.explanation)

    # Quit button to stop further interactions and clear state
    if st.button("Clear"):
        # Clear session state variables
        st.session_state.user_question = ""
        st.session_state.answer = ""
        st.session_state.explanation = ""
        st.stop()

# Function to generate a random fact
def generate_random_fact():
    prompt = "Provide a random interesting fact about Indian mythology."
    return generate_from_gemini(prompt)

# Display random fact when button is clicked
if fact:
    random_fact = generate_random_fact()
    st.sidebar.write(random_fact)
