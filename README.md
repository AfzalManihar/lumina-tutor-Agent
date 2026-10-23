# 🎓 Lumina Tutor

**An adaptive tutoring UI for the Algorithmic Instructional Designer Agent.**
Watch an AI tutor teach a lesson, detect when a learner is stuck, climb a five-level fail ladder, and hand the learner over to a human teacher, with every decision visible on a live dashboard.

### 👉 [Open the live demo](https://lumina-tutor-agent.streamlit.app/)

> The hosted link runs the built-in **demo engine** (a small sample lesson, "Fetch a web page with Python requests"). It uses the same rules and the same screens as the full system, so you can try the whole flow without any setup. The full LangGraph engine runs in Google Colab (see [Two ways to run it](#two-ways-to-run-it)).

---

## What you will see

The screen is split in two.

| Left: Tutor chat | Right: Live dashboard |
|---|---|
| Chat bubbles between the AI tutor and the learner | Mastery ring and per-exercise progress |
| A 3-question quick check before the lesson | **Fail ladder** (levels 1 to 5) that lights up as the learner struggles |
| Multiple-choice and typed answers | Student mood (confident, frustrated, rushing, needs a break) |
| Up to 3 hints per exercise | Error signals and error signatures |
| A "teach-back" box: *explain it in your own words* | **Park & handoff** card with a downloadable packet for the teacher |
| Confetti when an exercise is mastered | Spaced-revisit schedule (1, 3, 7, 14, 30 days) |

Two more tabs show the system side: **System metrics** (release gate, lesson quality, learner outcomes, ladder effectiveness) and **Engine trace** (LangGraph nodes and events).

## Try it in one minute

The sidebar has **Presenter controls**, so you do not have to type answers.

1. Open the [live demo](https://lumina-tutor-agent.streamlit.app/).
2. Press **Presenter: one weak spot** on the quick check.
3. Press **Presenter: wrong answer** again and again.
4. Watch the fail ladder go from level 1 to 5, and see the learner parked with a handoff packet at level 5.
5. Press **New session** in the sidebar and use **Presenter: correct answer** to see mastery, confetti and the revisit schedule.

## How the tutor decides what to do

| Level | Treatment | What the learner sees |
|:-:|---|---|
| 1 | Hint, then a new variant | A small nudge and a fresh question on the same skill |
| 2 | Worked example + completion problem | A similar solved example, then a half-solved task |
| 3 | Backward diagnostic | Two quick questions on the prerequisite idea |
| 4 | New representation + teach-back | Tiny steps, an analogy, and "explain it back" |
| 5 | Park & handoff | Progress is saved and a person takes over |

A few rules behind it:

- **Mastery** means two correct answers on *different* variants of the same exercise.
- Making the **same mistake twice** skips straight to the level-3 treatment.
- A **right answer with a weak explanation** (rote answer) is not counted as mastery.
- Fast wrong answers, slow wrong answers and hint dependence each trigger a different tutor message.
- A parked exercise blocks only the parts that depend on it; the learner keeps going with the rest.

## The system behind the UI

Lumina Tutor is the front end of a ten-step system built from an instructional-design document (Gagné's nine events of instruction and Merrill's five principles).

**Loop A: build the lesson**

1. Setup, source chunks and configuration
2. Strict data schemas (Pydantic): blueprint, exercise, answer key, failure log, learner state
3. Blueprint agent: a fixed 21-minute lesson template and prerequisite graph
4. Writer agent: lesson text, exercises, hints, variants, source links
5. Pacing lint, sandboxed code runner and grader
6. Simulated student that tries the lesson and writes failure logs
7. Repair loop that fixes the lesson from those failures

**Loop B: teach the learner**

8. Tutor engine: pre-test routing, fail ladder, mood flags, teach-back
9. Park & handoff packet, spaced revisit, aggregate flags
10. LangGraph state machine, release gate and metrics dashboard

## Two ways to run it

| | Demo engine | Live engine |
|---|---|---|
| Where | Streamlit Community Cloud (the link above) | Google Colab, Steps 1 to 10 in the same session |
| Data | Built-in sample lesson | Real LangGraph + Step 8 tutor engine |
| Setup | None | Run the notebook, then the bridge cell |
| When to use | Anytime, no setup | A full live demo of the real engine |

The app picks the backend automatically. If it can reach the live bridge it shows a green **Live engine connected** badge; otherwise it falls back to the demo engine and shows a yellow **Demo engine** badge.

The cohort numbers on the **System metrics** tab come from a synthetic cohort of scripted learners, not from real students.

## Run it on your own computer

```bash
git clone https://github.com/AfzalManihar/lumina-tutor-Agent.git
cd lumina-tutor-Agent
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501. With no live engine running, the app starts in demo mode.

To point the app at a live engine, set the bridge address before starting:

```bash
TUTOR_BACKEND_URL=http://127.0.0.1:8765 streamlit run app.py
```

## Repository contents

```
app.py             # the whole UI: styling, chat, dashboard, demo engine, live-engine client
requirements.txt   # Streamlit is the only dependency
README.md
```

## Tech

- **Streamlit** for the app, with custom HTML, CSS and JavaScript for the dark glass look
- **LangGraph** for the live tutoring graph (in the Colab engine)
- **Groq** language models for lesson writing and the simulated student (in the Colab engine)
- **Pydantic** for strict data schemas (in the Colab engine)

## Author

Built by **Afzal Manihar** as a final project.

## License

MIT. See the `LICENSE` file.
