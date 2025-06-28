import streamlit as st
from graphviz import Digraph
import re

st.set_page_config(layout="wide")  # Makes the app use the full width of the browser

st.title("Process Flow Generator with Decision Branches and Colors")

default_steps = """1. Receive application form
2. Check if application fee is paid
DECISION: Is the application fee paid?
CHOICE: Yes -> Proceed to document verification
CHOICE: No -> Send fee reminder to applicant
3. Verify submitted documents
DECISION: Are all required documents provided?
CHOICE: Yes -> Schedule entrance exam
CHOICE: No -> Request missing documents
4. Conduct entrance exam
DECISION: Did the applicant pass the exam?
CHOICE: Yes -> Schedule interview
CHOICE: No -> Notify applicant of rejection
5. Conduct interview
DECISION: Interview result?
CHOICE: Pass -> Move to merit list evaluation
CHOICE: Waitlist -> Place applicant on waitlist
CHOICE: Fail -> Notify applicant of rejection
6. Evaluate merit list
DECISION: Is applicant on merit list?
CHOICE: Yes -> Offer admission
CHOICE: No -> Notify applicant of rejection
7. Send admission offer
DECISION: Did applicant accept offer?
CHOICE: Yes -> Collect enrollment fee
CHOICE: No -> Close application as declined
8. Collect enrollment fee
DECISION: Is enrollment fee paid?
CHOICE: Yes -> Complete enrollment
CHOICE: No -> Send payment reminder
9. Complete enrollment
10. Send welcome email
11. Assign student ID
12. Register for orientation
13. End process
"""

# Make two columns: left (1/3) for input, right (2/3) for diagram
col1, col2 = st.columns([1, 2])

with col1:
    st.write("""
    **Enter your process steps below:**  
    - For decisions, use `DECISION: ...`  
    - For choices, use `CHOICE: label -> outcome` right after a DECISION.
    - Regular steps are just lines.

    **Colors:**  
    - Green: Start/End  
    - Yellow: Decision  
    - Blue: Normal step  
    - Red: Rejection/Failure/No/Decline
    """)
    steps_input = st.text_area("Process Steps", height=700, value=default_steps)
    generate = st.button("Generate Process Flow")

def parse_steps(lines):
    steps = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.upper().startswith("DECISION:"):
            question = line[len("DECISION:"):].strip()
            choices = []
            i += 1
            while i < len(lines) and lines[i].strip().upper().startswith("CHOICE:"):
                choice_line = lines[i].strip()[len("CHOICE:"):].strip()
                if "->" in choice_line:
                    label, outcome = map(str.strip, choice_line.split("->", 1))
                else:
                    label, outcome = "Choice", choice_line
                choices.append((label, outcome))
                i += 1
            steps.append({"type": "decision", "question": question, "choices": choices})
        else:
            steps.append({"type": "action", "text": line})
            i += 1
    return steps

with col2:
    if 'steps_input' in locals() and (st.session_state.get('generate', False) or st.session_state.get('auto_generate', True)):
        if 'generate' in locals() and generate:
            st.session_state['auto_generate'] = True
        lines = [l for l in steps_input.strip().split('\n') if l.strip()]
        parsed = parse_steps(lines)

        dot = Digraph(comment="Process Flow")
        node_count = [0]
        prev_node = None

        def add_step(step, prev_node):
            idx = node_count[0]
            if step["type"] == "action":
                node_id = f"node{idx}"
                text_lower = step["text"].lower()
                if "start" in text_lower or "begin" in text_lower or "receive" in text_lower:
                    color = "palegreen"
                elif "end" in text_lower or "complete" in text_lower or "close" in text_lower:
                    color = "palegreen"
                elif any(word in text_lower for word in ["reject", "fail", "decline", "no"]):
                    color = "salmon"
                else:
                    color = "lightblue"
                dot.node(node_id, step["text"], shape="rectangle", style="filled", fillcolor=color)
                if prev_node:
                    dot.edge(prev_node, node_id)
                node_count[0] += 1
                return node_id
            elif step["type"] == "decision":
                node_id = f"node{idx}"
                dot.node(node_id, step["question"], shape="diamond", style="filled", fillcolor="khaki")
                if prev_node:
                    dot.edge(prev_node, node_id)
                node_count[0] += 1
                last_ids = []
                for label, outcome in step["choices"]:
                    choice_id = f"node{node_count[0]}"
                    outcome_lower = outcome.lower()
                    if any(word in outcome_lower for word in ["reject", "fail", "decline", "no"]):
                        color = "salmon"
                    elif "end" in outcome_lower or "complete" in outcome_lower or "close" in outcome_lower:
                        color = "palegreen"
                    else:
                        color = "lightblue"
                    dot.node(choice_id, outcome, shape="rectangle", style="filled", fillcolor=color)
                    dot.edge(node_id, choice_id, label=label)
                    node_count[0] += 1
                    last_ids.append(choice_id)
                return last_ids[0]

        prev = None
        i = 0
        while i < len(parsed):
            step = parsed[i]
            prev = add_step(step, prev)
            i += 1

        svg_bytes = dot.pipe(format='svg')
        svg = svg_bytes.decode('utf-8')
        st.caption("Diagram Preview")
        st.components.v1.html(svg, height=800, scrolling=True)

        # Download button for SVG (works for PowerPoint, Lucidchart, Word, etc.)
        st.download_button(
            label="Download SVG Diagram",
            data=svg_bytes,
            file_name="process_flow.svg",
            mime="image/svg+xml"
        )

        st.write("""
        **How to use the SVG:**
        - Download the SVG file using the button above.
        - You can drag and drop or insert the SVG into PowerPoint, Word, Lucidchart, Miro, or most modern diagram tools.
        - In PowerPoint: Go to **Insert > Pictures > This Device...** and select your SVG file.
        - In Lucidchart: Use **File > Import Diagram > Import SVG**.
        - You can also open the SVG in a browser and copy-paste the image directly.
        """)