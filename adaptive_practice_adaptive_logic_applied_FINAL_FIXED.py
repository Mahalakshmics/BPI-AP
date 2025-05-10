import streamlit as st
import pandas as pd
import re

from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt
import time
import json

from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage
from datetime import datetime

# Hide sidebar, menu, and footer
st.set_page_config(page_title="BPI Learning",layout="wide", initial_sidebar_state="collapsed")

if "db" not in st.session_state:
    st.session_state.db = TinyDB(storage=MemoryStorage)

st.markdown("""
    <style>
    [data-testid="stSidebar"], #MainMenu, footer, header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Init session state
if "page" not in st.session_state:
    st.session_state.page = "login"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# -------------------- Knowledge Graph -------------------- #
knowledge_graph = {
        "Living organisms":{
            "prerequisite": [],
            "bloom_levels": ["Prerequisite","Applying"]
        },
        "Unicellular organisms": {
            "prerequisite": ["Living organisms"],
            "bloom_levels": ["Remembering"]
        },
        "Multicellular organisms": {
            "prerequisite": ["Living organisms"],
            "bloom_levels": ["Remembering"]
        },
        "Life processes": {
            "prerequisite": ["Living organisms"],
            "bloom_levels": ["Understanding"]
        },
        "Movement in living organisms": {
            "prerequisite": ["Life processes"],
            "bloom_levels": ["Understanding", "Applying"]
        },
        "Metabolism": {
            "prerequisite": ["Life processes"],
            "bloom_levels": ["Prerequisite","Remembering", "Analyzing"]
        },
        "Metabolism in unicellular organisms"  : {  
            "prerequisite": ["Metabolism"],
            "bloom_levels": ["Remembering","Applying"]
        },
        "Metabolism in multicellular organisms": {
            "prerequisite": ["Metabolism"],
            "bloom_levels": ["Understanding"]
        },
    }
# Login Page
def show_login():
    st.title("🎓 Student Login")
    with st.form("login_form"):
        name = st.text_input("Enter your name")
        age = st.number_input("Enter your age", min_value=5, max_value=100)
        gender = st.selectbox("Select your gender", ["Male", "Female", "Other"])
        submitted = st.form_submit_button("Login")
        if submitted and name.strip():
            st.session_state.logged_in = True
            st.session_state.name = name
            st.session_state.age = age
            st.session_state.gender = gender
            st.session_state.page = "home"
            st.session_state.learner_log = defaultdict(lambda: {"level": "Remembering", "attempts": 0, "mastered": False})
            # Initialize learning_log for tracking progress in the learning phase
            if "learning_log" not in st.session_state:
                st.session_state.learning_log = defaultdict(lambda: {"completed": False, "attempts": 0})
            st.session_state.history = []
            st.session_state.db.insert({
                "event": "login",
                "name": name,
                "age": age,
                "gender": gender,
                "timestamp": datetime.now().isoformat()
            })
            st.rerun()

# Home Page
def show_home():
    st.title("🏠 Welcome to Branching Programmed Instruction-based Learning")
    name = st.session_state.get("name", "Student")
    tab1, tab2 = st.tabs(["📘 Start Learning", "📝 Practice"])
    completed_frames = -1
    total_frames = 0
    # Check if the user is logged in

    with tab1:
        st.markdown(f"Hello **{name}**, here is your learning journey:")
        all_data = st.session_state.db.all()
        responses = [r for r in all_data if r.get("event") == "response" and r.get("name") == name]

        if not responses:
            st.info("You haven't started your learning path yet. Click below to begin.")
            if st.button("📘 Start Learning"):
                st.session_state.page = "frame"
                st.rerun()
        else:
            # 🎯 Show progress bar
            # Count how many frames exist in the course
            df = load_data()
            main_frames = df[df["source"] == "Main_frame"].index.tolist()
            total_frames = len(main_frames)
            completed_frames = sum(1 for frame in df.index if st.session_state.learning_log.get(frame, {}).get("completed", False))


            # Count how many frames the student got correct
            correct_frames = [r for r in responses if r["result"].lower() == "correct"]
            completed_frames = len(set(r["frame"] for r in correct_frames))

            # ✅ Calculate progress (cap at 1.0)
            progress = min(completed_frames / total_frames, 1.0)

            # 🎯 Show progress bar
            st.markdown("### 🎯 Your Learning Progress")
            st.progress(progress)

            # Optional: Display percentage
            st.write(f"Completed: **{completed_frames} / {total_frames}** frames")
            if completed_frames < total_frames:
                st.info("Complete all frames to unlock the practice phase.")
                if st.button("📘 Continue Learning"):
                    st.session_state.page = "frame"
                    st.rerun()


    with tab2:
        st.markdown(f"Hello **{name}**, here is your practice journey:")
        # Check if all concepts are mastered
        all_frames_completed = completed_frames == total_frames

        if not all_frames_completed:
            st.warning("⚠️ You need to complete all learning concepts before starting practice.")
            st.info("Go to the **Start Learning** tab to complete your learning journey.")
        else:
            all_data = st.session_state.db.all()
            responses = [r for r in all_data if r.get("event") == "response" and r.get("name") == name]

            if not responses:
                st.info("You haven't started your practice path yet. Click below to begin.")
                if st.button("📝 Start Practice"):
                    st.session_state.page = "practice"
                    st.rerun()
            else:
                # 🎯 Show progress bar
                # Count how many questions still to be answered from the knowledge graph
                remaining_concepts = [concept for concept, data in knowledge_graph.items()
                                      if not st.session_state.learner_log[concept]["mastered"]]
                total_concepts = len(knowledge_graph)
                completed_concepts = total_concepts - len(remaining_concepts)
                progress = min(completed_concepts / total_concepts, 1.0)

                # 🎯 Show progress bar
                st.markdown("### 🎯 Your Practice Progress")
                st.progress(progress)

                # Optional: Display percentage
                st.write(f"Completed: **{completed_concepts} / {total_concepts}** concepts")
                if st.button("📝 Continue Practice"):
                    st.session_state.page = "practice"
                    st.rerun()

# Frame Page
def show_frame():
    st.title("📖 Lets Get Started!")
    #change you are learning text color to green
    st.markdown(
        """
        <style>
        h5 {
            color: green;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown("<h5>You are learning : Science Grade 10 -> Biology -> Life Processes</h5>", unsafe_allow_html=True)
    st.markdown(f"👤 {st.session_state.name} | Age: {st.session_state.age} | Gender: {st.session_state.gender}")
    load_deafault_frame1()
    # Show "Back to Home" ONLY for main frames
    col1, col2, col3 = st.columns([6,1,1])
    with col2:
        if st.session_state.current_frame.startswith("main_frame"):
            if st.button("🔙 Back to Home"):
                st.session_state.page = "home"
                st.rerun()
    with col3:
        if st.button("Logout"):
            st.session_state.page = "login"
            st.session_state.logged_in = False
            st.rerun()

@st.cache_data
def load_data():
    df_main = pd.read_excel("branching_content.xlsx", sheet_name="Main_frame")
    df_remedial = pd.read_excel("branching_content.xlsx", sheet_name="Remedial_frame")
    df_main["source"] = "Main_frame"
    df_remedial["source"] = "Remedial_frame"
    df = pd.concat([df_main, df_remedial], ignore_index=True)
    df.set_index("frame_name", inplace=True)
    return df


def parse_option(raw):
    fields = {"ans": None, "result": None, "next_step": None, "feedback": None}
    for key in fields.keys():
        match = re.search(rf'{key}\s*[:=]\s*(.*?)(,|$)', raw, re.IGNORECASE | re.DOTALL)
        if match:
            fields[key] = match.group(1).strip(" \"{}")
    return fields

def load_deafault_frame1():
    df = load_data()
    # Initialize session state variables
    if "current_frame" not in st.session_state:
        st.session_state.current_frame = "main_frame_1"
    if "selected_option" not in st.session_state:
        st.session_state.selected_option = None
    if "show_feedback" not in st.session_state:
        st.session_state.show_feedback = False
    if "show_review" not in st.session_state:
        st.session_state.show_review = False
    if "next_step" not in st.session_state:
        st.session_state.next_step = None
    if "remedial_frame" not in st.session_state:
        st.session_state.remedial_frame = False

    # Load current frame
    if st.session_state.current_frame not in df.index:
        st.error(f"Frame '{st.session_state.current_frame}' not found. Please contact support.")
        return

    row = df.loc[st.session_state.current_frame]
    col1, col2 = st.columns(2)
    with col1:
        st.title(row["frame_heading"])
        st.markdown(f"<div style='font-size: 32px;'>{row['frame_content']}</div>", unsafe_allow_html=True)

        # Display notes
        st.markdown("<br>", unsafe_allow_html=True)
        if pd.notna(row.get("notes", None)):
            if "http" in row["notes"]:
                st.markdown(f"[📄 View Notes]({row['notes']})", unsafe_allow_html=True)
            else:
                st.info("Notes are not linked.")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"🔍 **Key Focus:** {row['key_focus']}")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"📎 [Extra Info]({row['extra_info']})")
    with col2:
        st.markdown("---")
        st.subheader("📚 Additional Learning")
        st.video(row["video"])

    if st.button("🔍 Review Now"):
        st.session_state.show_review = True

    if st.session_state.get("show_review", False):
        st.subheader("Scenario")
        st.markdown(f"<div style='font-size: 24px;'>{row['scenario']}</div>", unsafe_allow_html=True)
        st.subheader("Question")
        st.markdown(f"<div style='font-size: 20px;'>{row['question']}</div>", unsafe_allow_html=True)

        options_raw = [row["option_a"], row["option_b"], row["option_c"]]
        parsed_options = [
            parse_option(row["option_a"]),
            parse_option(row["option_b"]),
            parse_option(row["option_c"]),
        ]

        # Extract answer labels for display
        answer_labels = [opt["ans"] for opt in parsed_options]

        selected_ans = st.radio("Choose an answer:", answer_labels)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Check Answer"):
            matched = next((opt for opt in parsed_options if opt["ans"] == selected_ans), None)
            if matched:
                st.session_state.selected_option = matched
                st.session_state.feedback = matched["feedback"]
                st.session_state.next_step = matched["next_step"]
                st.session_state.db.insert({
                    "event": "response",
                    "name": st.session_state.name,
                    "frame": st.session_state.current_frame,
                    "selected_answer": matched["ans"],
                    "result": matched["result"],
                    "feedback": matched["feedback"],
                    "timestamp": datetime.now().isoformat()
                })
                if matched["result"].lower() == "correct":
                    st.success("✅ Correct!")
                    st.info(f"💬 {matched['feedback']}")
                    st.session_state.show_feedback = True
                    st.session_state.in_remedial = False
                else:
                    st.session_state.in_remedial = True
                    st.session_state.remedial_frame = matched["next_step"]
                    st.rerun()

    if st.session_state.show_feedback and st.session_state.selected_option["result"].lower() == "correct":
        # Check if the current frame is the last frame
        if st.session_state.next_step == "complete" or pd.isna(st.session_state.next_step):
            st.success("🎉 Congratulations! You have completed all concepts.")
        elif st.session_state.next_step not in df.index:
            st.error(f"Next frame '{st.session_state.next_step}' not found. Please contact support.")
        else:
            if st.button("➡️ Next"):
                st.session_state.learning_log[st.session_state.current_frame]["completed"] = True
                st.session_state.learning_log[st.session_state.current_frame]["attempts"] += 1
                st.session_state.current_frame = st.session_state.next_step
                st.session_state.show_feedback = False
                st.session_state.selected_option = None
                st.session_state.next_step = None
                st.session_state.show_review = False
                st.rerun()

def show_remedial():
    df = load_data()
    if not st.session_state.get("remedial_frame"):
        st.error("No remedial frame available.")
        return
    
    row = df.loc[st.session_state.remedial_frame]
    st.title(row.get("frame_heading", "Remedial Frame"))
    st.write(row.get("frame_content", ""))

    if st.session_state.get("selected_option") and st.session_state.selected_option.get("feedback"):
        st.subheader("💬 Feedback")
        st.info(st.session_state.selected_option["feedback"])
        
    if "next_step" in row and pd.notna(row["next_step"]):
        st.info(f"ℹ️ {row['next_step']}")

    if st.button("🔁 Return to Main Frame"):
        main_id = "main_frame_" + st.session_state.current_frame.split("_")[-1]
        st.session_state.in_remedial = False
        st.session_state.current_frame = main_id
        st.session_state.show_feedback = False
        st.session_state.selected_option = None
        st.session_state.remedial_frame = None
        st.rerun()

def show_practice():
    

    # -------------------- Question Bank -------------------- #
    question_bank = [{"question_id": "Q1.1", "text": "Which of the following is considered a sign of life?", "options": ["Being silent", "Molecular movement", "Being inanimate", "Staying still"], "correct_answer": "Molecular movement", "bloom_level": "Remembering", "concept_tag": "Unicellular organisms"},
        {"question_id": "Q1.0", "text": "Which of the following is *not* a living thing?", "options": ["Dog", "Man", "Rock", "Cow"], "correct_answer": "Rock", "bloom_level": "Prerequisite", "concept_tag": "Living organisms"},
        {"question_id": "Q1.2", "text": "Why is visible movement not always a reliable sign of life?", "options": ["Only large organisms show movement", "Some living beings are too small", "Some life processes occur at molecular levels", "Movement is not needed at all"], "correct_answer": "Some life processes occur at molecular levels", "bloom_level": "Understanding", "concept_tag": "Movement in living organisms"},
        {"question_id": "Q1.3", "text": "A leafless tree stands still during winter. Which observation best supports that it is still alive?", "options": ["It is green in color", "It produces flowers immediately", "It continues cellular activities internally", "It sheds leaves every day"], "correct_answer": "It continues cellular activities internally", "bloom_level": "Applying", "concept_tag": "Living organisms"},
        {"question_id": "Q2.1", "text": "Which life process helps organisms break down food to release energy?", "options": ["Excretion", "Nutrition", "Respiration", "Diffusion"], "correct_answer": "Respiration", "bloom_level": "Remembering", "concept_tag": "Metabolism"},
        {"question_id": "Q2.0", "text": "What do living beings use to obtain energy?", "options": ["Dust", "Heat", "Food", "Water"], "correct_answer": "Food", "bloom_level": "Prerequisite", "concept_tag": "Metabolism"},
        {"question_id": "Q2.2", "text": "Why do organisms need to constantly carry out life processes?", "options": ["To sleep better", "To prevent breakdown of body structures", "To show movement", "To make noise"], "correct_answer": "To prevent breakdown of body structures", "bloom_level": "Understanding", "concept_tag": "Life processes"},
        {"question_id": "Q2.3", "text": "Which of these best explains the interdependence of respiration and nutrition?", "options": ["Respiration provides energy for making food", "Nutrition provides food which is broken down by respiration to release energy", "Nutrition and respiration are unrelated", "Respiration eliminates waste from food"], "correct_answer": "Nutrition provides food which is broken down by respiration to release energy", "bloom_level": "Analyzing", "concept_tag": "Metabolism"},
        {"question_id": "Q3.1", "text": "What do unicellular organisms use for gas exchange?", "options": ["Blood vessels", "Heart", "Entire body surface", "Alveoli"], "correct_answer": "Entire body surface", "bloom_level": "Remembering", "concept_tag": "Metabolism in unicellular organisms"},
        {"question_id": "Q3.2", "text": "Why do multicellular organisms require specialized transport systems?", "options": ["They cannot breathe", "Their body is large and complex", "They have more blood", "They do not grow"], "correct_answer": "Their body is large and complex", "bloom_level": "Understanding", "concept_tag": "Metabolism in multicellular organisms"},
        {"question_id": "Q3.3", "text": "An amoeba absorbs oxygen directly through its surface, but a frog has lungs. Why is this difference important?", "options": ["Frogs don’t need oxygen", "Amoeba has lungs too", "Multicellular organisms need systems to reach internal cells", "Frogs live in water"], "correct_answer": "Multicellular organisms need systems to reach internal cells", "bloom_level": "Applying", "concept_tag": "Metabolism in unicellular organisms"}
    ]

    # -------------------- Learner Profile -------------------- #
    if "learner_log" not in st.session_state:
        st.session_state.learner_log = defaultdict(lambda: {"level": "Remembering", "attempts": 0, "mastered": False})
    if "history" not in st.session_state:
        st.session_state.history = []

    # -------------------- Helper Functions -------------------- #
    def next_bloom_level(current):
        order = ["Prerequisite", "Remembering", "Understanding", "Applying","Analyzing","Evaluating", "Creating"]
        try:
            return order[order.index(current) + 1]
        except (ValueError, IndexError):
            return None

    def get_next_concept(log, graph):
        for concept, data in graph.items():
            if not log[concept]["mastered"]:
                if all(log[p]["mastered"] for p in data["prerequisite"]):
                    return concept
        return None

    def choose_question(log, graph, bank):
        eligible_concepts = [
            concept for concept in graph
            if not log[concept]["mastered"] and all(log[p]["mastered"] for p in graph[concept]["prerequisite"])
        ]
        if not eligible_concepts:
            return None

        concept = eligible_concepts[0]

        current_level = log[concept]["level"]
        bloom_levels = graph[concept]["bloom_levels"]
        if current_level not in bloom_levels:
            current_level = bloom_levels[0]
            log[concept]["level"] = current_level

        levels_to_try = bloom_levels[bloom_levels.index(current_level):]
        for level in levels_to_try:
            unanswered = [
                q for q in bank
                if q["concept_tag"] == concept and q["bloom_level"] == level and
                q["text"] not in [h["question"] for h in st.session_state.history]
            ]
            if unanswered:
                return unanswered[0]

        # Mark the concept as mastered if all questions at all levels are answered
        log[concept]["mastered"] = True
        log[concept]["level"] = None
        return None


    # -------------------- Graph Visualization -------------------- #
    def plot_knowledge_graph(graph, learner_log, current_concept=None):
        G = nx.DiGraph()
        node_colors = []
        labels = {}

        # Helper function to split text into multiple lines
        def split_text(text, max_length=15):
            words = text.split()
            lines = []
            current_line = []
            current_length = 0
            for word in words:
                if current_length + len(word) + 1 > max_length:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = len(word)
                else:
                    current_line.append(word)
                    current_length += len(word) + 1
            if current_line:
                lines.append(" ".join(current_line))
            return "\n".join(lines)

        # Add nodes and edges to the graph
        for concept, data in graph.items():
            G.add_node(concept)
            for prereq in data["prerequisite"]:
                if prereq in graph:  # Ensure the prerequisite is in the filtered graph
                    G.add_edge(prereq, concept)
            status = "✅" if learner_log[concept]["mastered"] else "🕗"
            label_text = f"{concept} {status}"
            labels[concept] = split_text(label_text)  # Split label into multiple lines
            if concept == current_concept:
                node_colors.append("gold")
            elif learner_log[concept]["mastered"]:
                node_colors.append("lightgreen")
            else:
                node_colors.append("lightcoral")

        # Ensure node_colors matches the number of nodes in the graph
        if len(node_colors) != len(G.nodes):
            raise ValueError(f"Mismatch: node_colors has {len(node_colors)} elements, but graph has {len(G.nodes)} nodes.")

        # Adjust font size dynamically based on the length of the longest label
        max_label_length = max(len(label.replace("\n", "")) for label in labels.values())
        font_size = max(6, 8 - (max_label_length // 10))  # Reduce font size for longer labels

        pos = nx.spring_layout(G, scale=1.5)  # Adjust scale for smaller layout
        fig, ax = plt.subplots(figsize=(8, 6))  # Reduce figure size
        nx.draw(
            G,
            pos,
            labels=labels,
            node_color=node_colors,
            node_size=1500,  # Reduce node size
            font_size=font_size,  # Use dynamically calculated font size
            ax=ax
        )
        st.pyplot(fig)

    # -------------------- UI -------------------- #
    st.title("🤖 Adaptive Practice with Knowledge Graph")
    st.markdown("Get concept-based questions that adapt to your progress.")

    tabs = st.tabs(["📖 Practice", "📌 Concept Graph", "📊 Progress & History"])

    with tabs[0]:
        if "last_submitted" not in st.session_state:
            st.session_state.last_submitted = False

        if st.session_state.last_submitted:
            st.session_state.last_submitted = False
            st.rerun()

        with st.form(key="question_form"):
            previous_concept = get_next_concept(st.session_state.learner_log, knowledge_graph)
            question = choose_question(st.session_state.learner_log, knowledge_graph, question_bank)
            current_concept = question["concept_tag"] if question else None
            if current_concept and current_concept != previous_concept:
                st.info(f"🎯 New Concept Unlocked: {current_concept}!")

            if question:
                st.subheader(question["text"])
                user_answer = st.radio("Choose an answer:", question["options"], key=question["question_id"])
            else:
                user_answer = None

            submit_clicked = st.form_submit_button("Submit")
            if submit_clicked and question:
                with st.spinner("Evaluating answer..."):
                    time.sleep(1.5)
                is_correct = (user_answer == question["correct_answer"])

                concept = question["concept_tag"]
                st.session_state.learner_log[concept]["attempts"] += 1

                st.session_state.history.append({
                    "question": question["text"],
                    "answer": user_answer,
                    "correct": is_correct
                })
                with open("adaptive_redirection_map_v2.json") as f:
                        adaptive_map = json.load(f)
                if is_correct:
                    st.balloons()
                    st.markdown("### 🎉 Great job! Keep it up!")                    
                    redir = adaptive_map.get(question["text"], {}).get("if_correct", "")
                    if redir.lower().startswith("Serve"):
                        qid = redir.split()[1].strip("()").strip()
                        st.session_state.redirect_question = qid
                        next_level = next_bloom_level(question["bloom_level"])
                        if next_level:
                            st.session_state.learner_log[concept]["level"] = next_level
                        else:
                            st.session_state.learner_log[concept]["mastered"] = True
                            st.session_state.learner_log[concept]["level"] = None
                            st.success(f"🎉 You've mastered the concept: {concept}")
                else:
                    st.snow()
                    st.markdown("### 😓 Oops! Incorrect answer. Redirecting to prerequisite concept.")
                    # Reset progress to the prerequisite concept
                    prerequisites = knowledge_graph[concept]["prerequisite"]
                    if prerequisites:
                        # Redirect to the first unmet prerequisite
                        redir = adaptive_map.get(question["text"], {}).get("if_incorrect", "")
                        if redir.lower().startswith("Serve"):
                            qid = redir.split()[1].strip("()").strip()
                            st.session_state.redirect_question = qid
                            st.session_state.learner_log[concept]["attempts"] = 0
                            st.session_state.learner_log[concept]["mastered"] = False
                            st.session_state.learner_log[concept]["level"] = "Prerequisite"
                            st.success(f"🔄 Redirected to prerequisite concept: {prerequisites[0]}")
                    else:
                        st.warning("No prerequisites found for this concept. Please review the material.")

                ph = st.empty()
                for i in range(3, 0, -1):
                    with ph.container():
                        cols = st.columns([0.6, 0.3, 0.1])
                        with cols[0]:
                            st.markdown(f"#### ⏳ Next question in {i} seconds...")
                            if is_correct:
                                st.progress((3 - i + 1) / 3, text=f"Progress: {(3 - i + 1) * 33}% ✅")
                            else:
                                st.progress((3 - i + 1) / 3, text=f"Progress: {(3 - i + 1) * 33}% ❌")
                        with cols[1]:
                            st.markdown("<form action='' method='get'><button type='submit'>Next Now</button></form>", unsafe_allow_html=True)
                    time.sleep(1)
                    ph.empty()

                st.session_state.last_submitted = True
                st.rerun()

            if question is None:
                if any(log["attempts"] > 0 for log in st.session_state.learner_log.values()):
                    st.success("🏁 You've mastered all concepts in this graph! Well done.")
                    if st.form_submit_button("Practice next concept"):
                        st.session_state.learner_log = defaultdict(lambda: {"level": "Remembering", "attempts": 0, "mastered": False})
                        st.session_state.history = []
                        st.rerun()
                else:
                    st.info("📘 Start practicing to see your progress here.")

    with tabs[1]:
        st.subheader("📌 Concept Mastery Graph")
        st.markdown("**Legend:** 🟩 Mastered | 🟥 Pending | 🟨 Current Concept")
        filter_pending = st.checkbox("🔍 Show only pending concepts", value=False)
        if filter_pending:
            filtered_graph = {k: v for k, v in knowledge_graph.items() if not st.session_state.learner_log[k]["mastered"]}
        else:
            filtered_graph = knowledge_graph
        plot_knowledge_graph(filtered_graph, st.session_state.learner_log, current_concept=get_next_concept(st.session_state.learner_log, knowledge_graph))
    with tabs[2]:
        st.subheader("📊 Your Learning Progress")

        # Prepare data for the chart
        concepts = list(st.session_state.learner_log.keys())
        progress = [
            1.0 if log["mastered"] else (0.5 if log["level"] else 0.0)
            for log in st.session_state.learner_log.values()
        ]  # 1.0 for mastered, 0.5 for in-progress, 0.0 for not started

        # Create a bar chart
        fig, ax = plt.subplots(figsize=(4, 2))
        ax.barh(concepts, progress, color=["lightgreen" if p == 1.0 else "gold" if p == 0.5 else "lightcoral" for p in progress])
        ax.set_xlim(0, 1)
        ax.set_xlabel("Progress")
        ax.set_title("Concept Mastery Progress")
        ax.set_yticks(range(len(concepts)))
        ax.set_yticklabels(concepts)

        # Display the chart
        st.pyplot(fig)

        st.markdown("---")
        st.subheader("📜 Answer History")
        for entry in st.session_state.history:
            result = "✅" if entry["correct"] else "❌"
            st.markdown(f"**Q:** {entry['question']}  ")
            st.markdown(f"**Your Answer:** {entry['answer']} {result}")
    # Show "Back to Home" ONLY for main frames
    col1, col2, col3 = st.columns([6,1,1])
    with col2:
        if st.session_state.current_frame.startswith("main_frame"):
            if st.button("🔙 Back to Home"):
                st.session_state.page = "home"
                st.rerun()
    with col3:
        if st.button("Logout"):
            st.session_state.page = "login"
            st.session_state.logged_in = False
            st.rerun()


# Router
if st.session_state.page == "login":
    show_login()
elif st.session_state.page == "home":
    show_home()
elif st.session_state.page == "frame":
    if st.session_state.get("in_remedial"):
        show_remedial()
    else:
        show_frame()
elif st.session_state.page == "practice":
    show_practice()
else:
    st.error("Page not found.")


# Footer
st.markdown(
    """
    <style>
    footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Add a footer
st.markdown(
    """
    <style>
    footer:after {
        content: '© 2023 Braching Programmed Instruction based learning';
        display: block;
        text-align: center;
        padding: 10px;
        color: #888;
    }
    </style>
    """,
    unsafe_allow_html=True
)