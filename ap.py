import streamlit as st
from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt
import time

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
    "Movement in living organisms": {
        "prerequisite": ["Life processes"],
        "bloom_levels": ["Understanding", "Applying"]
    },
    "Metabolism": {
        "prerequisite": ["Life processes"],
        "bloom_levels": ["Prerequisite","Remembering", "Analyzing"]
    },
    "Life processes": {
        "prerequisite": ["Living organisms"],
        "bloom_levels": ["Understanding"]
    },
    "Metabolism in unicellular organisms"  : {  
        "prerequisite": ["Life processes", "Metabolism"],
        "bloom_levels": ["Remembering","Applying"]
    },
    "Metabolism in multicellular organisms": {
        "prerequisite": ["Life processes", "Metabolism"],
        "bloom_levels": ["Understanding"]
    },
}

# -------------------- Question Bank -------------------- #
question_bank = [{"question_id": "Q1", "text": "Which of the following is considered a sign of life?", "options": ["Being silent", "Molecular movement", "Being inanimate", "Staying still"], "correct_answer": "Molecular movement", "bloom_level": "Remembering", "concept_tag": "Unicellular organisms"},
    {"question_id": "Q2", "text": "Which of the following is *not* a living thing?", "options": ["Dog", "Man", "Rock", "Cow"], "correct_answer": "Rock", "bloom_level": "Prerequisite", "concept_tag": "Living organisms"},
    {"question_id": "Q3", "text": "Why is visible movement not always a reliable sign of life?", "options": ["Only large organisms show movement", "Some living beings are too small", "Some life processes occur at molecular levels", "Movement is not needed at all"], "correct_answer": "Some life processes occur at molecular levels", "bloom_level": "Understanding", "concept_tag": "Movement in living organisms"},
    {"question_id": "Q4", "text": "A leafless tree stands still during winter. Which observation best supports that it is still alive?", "options": ["It is green in color", "It produces flowers immediately", "It continues cellular activities internally", "It sheds leaves every day"], "correct_answer": "It continues cellular activities internally", "bloom_level": "Applying", "concept_tag": "Living organisms"},
    {"question_id": "Q5", "text": "Which life process helps organisms break down food to release energy?", "options": ["Excretion", "Nutrition", "Respiration", "Diffusion"], "correct_answer": "Respiration", "bloom_level": "Remembering", "concept_tag": "Metabolism"},
    {"question_id": "Q6", "text": "What do living beings use to obtain energy?", "options": ["Dust", "Heat", "Food", "Water"], "correct_answer": "Food", "bloom_level": "Prerequisite", "concept_tag": "Metabolism"},
    {"question_id": "Q7", "text": "Why do organisms need to constantly carry out life processes?", "options": ["To sleep better", "To prevent breakdown of body structures", "To show movement", "To make noise"], "correct_answer": "To prevent breakdown of body structures", "bloom_level": "Understanding", "concept_tag": "Life processes"},
    {"question_id": "Q8", "text": "Which of these best explains the interdependence of respiration and nutrition?", "options": ["Respiration provides energy for making food", "Nutrition provides food which is broken down by respiration to release energy", "Nutrition and respiration are unrelated", "Respiration eliminates waste from food"], "correct_answer": "Nutrition provides food which is broken down by respiration to release energy", "bloom_level": "Analyzing", "concept_tag": "Metabolism"},
    {"question_id": "Q9", "text": "What do unicellular organisms use for gas exchange?", "options": ["Blood vessels", "Heart", "Entire body surface", "Alveoli"], "correct_answer": "Entire body surface", "bloom_level": "Remembering", "concept_tag": "Metabolism in unicellular organisms"},
    {"question_id": "Q10", "text": "Why do multicellular organisms require specialized transport systems?", "options": ["They cannot breathe", "Their body is large and complex", "They have more blood", "They do not grow"], "correct_answer": "Their body is large and complex", "bloom_level": "Understanding", "concept_tag": "Metabolism in multicellular organisms"},
    {"question_id": "Q11", "text": "An amoeba absorbs oxygen directly through its surface, but a frog has lungs. Why is this difference important?", "options": ["Frogs don’t need oxygen", "Amoeba has lungs too", "Multicellular organisms need systems to reach internal cells", "Frogs live in water"], "correct_answer": "Multicellular organisms need systems to reach internal cells", "bloom_level": "Applying", "concept_tag": "Metabolism in unicellular organisms"}
   ]

# -------------------- Learner Profile -------------------- #
if "learner_log" not in st.session_state:
    st.session_state.learner_log = defaultdict(lambda: {"level": "Remembering", "attempts": 0, "mastered": False})
if "history" not in st.session_state:
    st.session_state.history = []

# -------------------- Helper Functions -------------------- #
def next_bloom_level(current):
    order = ["Remembering", "Understanding", "Applying"]
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
        unanswered = [q for q in bank if q["concept_tag"] == concept and q["bloom_level"] == level and q["text"] not in [h["question"] for h in st.session_state.history]]
        if unanswered:
            return unanswered[0]

    log[concept]["mastered"] = True
    log[concept]["level"] = None
    return None
    concept = eligible_concepts[0]

    # Ensure a valid level is set
    current_level = log[concept]["level"]
    bloom_levels = graph[concept]["bloom_levels"]
    if current_level not in bloom_levels:
        current_level = bloom_levels[0]
        log[concept]["level"] = current_level

    levels_to_try = bloom_levels[bloom_levels.index(current_level):]
    for level in levels_to_try:
        for q in bank:
            if q["concept_tag"] == concept and q["bloom_level"] == level:
                return q
    return None
    current_level = log[concept]["level"]
    levels_to_try = ["Remembering", "Understanding", "Applying"]
    start_index = levels_to_try.index(current_level)
    for level in levels_to_try[start_index:]:
        for q in bank:
            if q["concept_tag"] == concept and q["bloom_level"] == level:
                return q
    return None
    current_level = log[concept]["level"]
    for q in bank:
        if q["concept_tag"] == concept and q["bloom_level"] == current_level:
            return q
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

    for concept, data in graph.items():
        G.add_node(concept)
        for prereq in data["prerequisite"]:
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

    # Adjust font size dynamically based on the length of the longest label
    max_label_length = max(len(label.replace("\n", "")) for label in labels.values())
    font_size = max(6, 8 - (max_label_length // 10))  # Reduce font size for longer labels

    pos = nx.spring_layout(G)
    fig, ax = plt.subplots()
    nx.draw(
        G,
        pos,
        labels=labels,
        node_color=node_colors,
        node_size=3000,
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

            if is_correct:
                st.balloons()
                st.markdown("### 🎉 Great job! Keep it up!")
                next_level = next_bloom_level(question["bloom_level"])
                if next_level:
                    st.session_state.learner_log[concept]["level"] = next_level
                else:
                    st.session_state.learner_log[concept]["mastered"] = True
                    st.session_state.learner_log[concept]["level"] = None
                    st.success(f"🎉 You've mastered the concept: {concept}")
            else:
                st.snow()
                st.markdown("### 😓 Oops! Don't worry—review and try again!")
                st.session_state.learner_log[concept]["level"] = "Remembering"

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
    st.json(dict(st.session_state.learner_log))

    st.markdown("---")
    st.subheader("📜 Answer History")
    for entry in st.session_state.history:
        result = "✅" if entry["correct"] else "❌"
        st.markdown(f"**Q:** {entry['question']}  ")
        st.markdown(f"**Your Answer:** {entry['answer']} {result}")
