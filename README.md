<h1 align="center">🎓 Lumina Tutor</h1>

<p align="center">
  <strong>An Adaptive AI Tutor That Knows When to Teach, When to Retry, and When to Ask for Help</strong>
</p>


<p align="center">
  <a href="https://lumina-tutor-agent.streamlit.app/">
    <img src="https://img.shields.io/badge/🚀_LIVE_DEMO-Try_Lumina_Tutor-7C3AED?style=for-the-badge" alt="Live Demo">
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/LangGraph-Agent_Workflow-1C3C3C" alt="LangGraph">
  <img src="https://img.shields.io/badge/Groq-LLM-orange" alt="Groq">
  <img src="https://img.shields.io/badge/Pydantic-Data_Validation-E92063" alt="Pydantic">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License">
</p>

**Lumina Tutor** is an adaptive tutoring interface for an Algorithmic Instructional Designer Agent. It demonstrates how an AI tutor can respond to learner mistakes, adjust its teaching strategy, track mastery, and escalate to a human teacher when needed.

Instead of repeating the same explanation, the tutor follows a **five-level failure-response ladder** and makes its decisions visible through a live learning dashboard.

> **Core idea:** An effective AI tutor should not just provide answers. It should identify learning difficulties, adapt its teaching approach, and know when a human should step in.

## 🚀 Live Demo

**[Open Lumina Tutor](https://lumina-tutor-agent.streamlit.app/)**

The hosted application runs in **demo mode** with a built-in sample lesson: *Fetch a web page with Python requests.*

You can explore the interface and its tutoring workflow without configuring an API key or running the full engine locally.

The complete LangGraph engine runs separately in Google Colab. The application can connect to it through a backend bridge when that engine is running and accessible.

## ✨ Key Features

| Feature | What it does |
|---|---|
| 🧠 Adaptive tutoring | Adjusts the teaching response based on learner performance |
| 🎯 Quick diagnostic | Uses a three-question check before the lesson |
| 🪜 Five-level fail ladder | Escalates teaching strategies when the learner struggles |
| 💡 Guided hints | Provides up to three hints per exercise |
| 📝 Teach-back | Asks learners to explain concepts in their own words |
| 📊 Learning dashboard | Displays mastery, progress, mood indicators, and error signals |
| 👤 Human handoff | Parks a struggling exercise and creates a downloadable teacher handoff packet |
| 🔁 Spaced revisits | Schedules revision for 1, 3, 7, 14, and 30 days |
| 🎉 Mastery feedback | Shows a celebration when an exercise is mastered |
| 🔍 Engine trace | Displays workflow nodes and events when trace data is available |
| 📈 System metrics | Presents lesson-quality, learner-outcome, and workflow metrics |

## ⚡ Try It in 60 Seconds

No setup is required.

1. Open the [Lumina Tutor live demo](https://lumina-tutor-agent.streamlit.app/).
2. Find the **Presenter controls** in the sidebar.
3. Select **Presenter: one weak spot** during the quick check.
4. Repeatedly select **Presenter: wrong answer**.
5. Watch the tutor escalate through the five failure levels.
6. Observe how the exercise is parked and a teacher handoff packet becomes available.
7. Start a **New session** and use **Presenter: correct answer** to explore mastery feedback and the revision schedule.

**Tip:** The presenter controls let you demonstrate different learner scenarios without manually typing every answer.

## 🪜 The Five-Level Fail Ladder

The tutor changes its teaching strategy instead of simply repeating the same response.

| Level | Teaching strategy | Learner experience |
|:---:|---|---|
| 1 | Hint + new variant | A small hint and another question testing the same skill |
| 2 | Worked example | A solved example followed by a partially completed task |
| 3 | Backward diagnosis | Questions that check prerequisite understanding |
| 4 | New representation | Smaller steps, an analogy, and a teach-back exercise |
| 5 | Human handoff | The exercise is parked and a handoff packet is created |

### 🧩 Additional Adaptation Rules

- **Mastery:** Requires two correct answers on different variants of the same exercise.
- **Repeated mistakes:** Making the same mistake twice triggers the level-three treatment.
- **Weak explanations:** A correct answer with an insufficient explanation does not count as mastery.
- **Different error patterns:** Fast incorrect answers, slow incorrect answers, and dependence on hints can trigger different responses.
- **Partial progress:** Parking one exercise blocks only dependent activities, allowing the learner to continue with other work.

These rules help make the tutor's behaviour more structured and explainable.

## 🧠 How the System Works

Lumina Tutor is the user-facing component of a ten-step instructional-design system based on **Gagné's Nine Events of Instruction** and **Merrill's First Principles of Instruction**.

The system has two main loops.

### Loop A — Build and Validate the Lesson

1. **Setup:** Load source material, configuration, and source chunks.
2. **Structured schemas:** Define blueprints, exercises, answer keys, failure logs, and learner state using Pydantic.
3. **Blueprint agent:** Creates a structured lesson blueprint using a fixed 21-minute template and prerequisite graph.
4. **Writer agent:** Produces lesson content, exercises, hints, variants, and source links.
5. **Quality checks:** Run pacing lint, a sandboxed code runner, and grading checks.
6. **Simulated student:** Attempts the lesson and records failure cases.
7. **Repair loop:** Uses failure logs to improve the lesson.

### Loop B — Teach the Learner

8. **Tutor engine:** Handles pre-test routing, the fail ladder, learner-state flags, and teach-back.
9. **Handoff and revision:** Creates teacher handoff packets, schedules spaced revisits, and tracks aggregate flags.
10. **Workflow and metrics:** Uses a LangGraph state machine, release gate, and dashboard metrics.

This separation allows lesson creation and validation to be handled independently from the learner-facing tutoring experience.

## 🖥️ What the Interface Shows

The main screen is divided into two areas.

**Left — Tutor Chat**
- AI tutor and learner conversation
- Diagnostic questions and exercises
- Multiple-choice and typed responses
- Hints and worked examples
- Teach-back input

**Right — Learning Dashboard**
- Mastery ring and exercise progress
- Five-level failure ladder
- Learner mood indicators
- Error signals and error signatures
- Teacher handoff card
- Spaced-revision schedule

Additional tabs provide system metrics and engine-trace information.

## ⚙️ Two Ways to Run Lumina Tutor

| | Demo Engine | Live Engine |
|---|---|---|
| Location | Streamlit Community Cloud | Google Colab + backend bridge |
| Lesson | Built-in sample lesson | Full engine workflow |
| Setup | None | Run notebook steps and bridge |
| Best for | Quick exploration and presentations | Demonstrating the connected engine |

The app selects the backend automatically. If the live bridge is reachable, it displays **Live engine connected**; otherwise, it falls back to the built-in demo engine.

**Important:** Metrics based on the scripted learner cohort are synthetic demonstration data, not results collected from real students.

## 🛠️ Tech Stack

| Technology | Role |
|---|---|
| Python | Core application logic |
| Streamlit | User interface and interactive dashboard |
| HTML, CSS, JavaScript | Custom interface styling and interactions |
| LangGraph | Live tutoring workflow and state management |
| Groq | Language-model inference in the live engine |
| Pydantic | Structured data schemas and validation |

The demo interface is designed to run independently of the full live engine. Some technologies are used only in the separate Colab workflow.

## 💻 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/AfzalManihar/lumina-tutor-Agent.git
cd lumina-tutor-Agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the application

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

Without a live engine connection, the app starts in demo mode.

### Connect to a Live Engine

If the backend bridge is running locally, configure its address before starting the app.

**Windows PowerShell:**

```powershell
$env:TUTOR_BACKEND_URL="http://127.0.0.1:8765"
streamlit run app.py
```

**macOS / Linux:**

```bash
export TUTOR_BACKEND_URL="http://127.0.0.1:8765"
streamlit run app.py
```

The live engine must be running and reachable at the configured address.

## 📁 Repository Structure

```text
lumina-tutor-Agent/
├── app.py
├── requirements.txt
├── README.md
└── LICENSE
```

The Streamlit interface, styling, demo engine, dashboard, and live-engine client are contained in `app.py`. The full LangGraph engine is run separately in Google Colab.

## 🎯 Why This Project?

Lumina Tutor explores an important question in AI education:

**What should an AI tutor do when its current teaching strategy is not working?**

Rather than treating every wrong answer the same way, the system demonstrates progressive support, prerequisite diagnosis, alternative explanations, mastery checks, and human escalation.

The project brings together instructional design, structured AI workflows, learner-state tracking, and explainable tutoring decisions in one interactive application.

## 👨‍💻 Author

**Afzal Manihar**

Interested in Agentic AI, Generative AI, and building practical AI applications.

- GitHub: [@AfzalManihar](https://github.com/AfzalManihar)
- Project repository: [lumina-tutor-Agent](https://github.com/AfzalManihar/lumina-tutor-Agent)
- Live application: [Lumina Tutor](https://lumina-tutor-agent.streamlit.app/)

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <b>Built to explore more adaptive, transparent, and human-centered AI tutoring.</b>
  <br>
  ⭐ If you find this project interesting, consider starring the repository!
</p>
