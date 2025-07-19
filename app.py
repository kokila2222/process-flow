import streamlit as st
from graphviz import Digraph
import re

st.set_page_config(layout="wide", page_title="Process Flow Builder")

st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stTextArea textarea {
        font-family: monospace;
    }
    .card {
        background-color: #f9f9f9;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }
    .example-box {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 6px;
        font-family: monospace;
        border: 1px solid #e0e0e0;
    }
    .node-key {
        display: flex;
        gap: 10px;
        font-size: 0.9rem;
        margin-top: 1rem;
    }
    .node-key span {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 6px;
        font-weight: 500;
        color: #fff;
    }
    .green { background-color: #60c172; }
    .blue { background-color: #3a8ee6; }
    .yellow { background-color: #f4b400; }
    .red { background-color: #e85c5c; }
    </style>
""", unsafe_allow_html=True)

st.title("Build Your Flow")
st.caption("Create and manage your process flows with ease.")

# Instructions + Example Side by Side
col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="header">How to Write Your Process Flow</div>', unsafe_allow_html=True)
    st.markdown("""
    - Start by listing all the major steps in your process.  
    - Use clear and concise language for each step.  
    - Put each step on a new line in the 'Add Steps' box.  
    - Specify the type of step (e.g., Action, Decision) for better visualization.  
    - Don’t forget to include a 'Start' and 'End' point for your flow.
    """)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="header">For Example</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="example-box">
    1. Receive application form<br>
    2. Check if application fee is paid<br>
    DECISION: Is the application fee paid?<br>
    CHOICE: Yes -> Proceed to document verification<br>
    CHOICE: No -> Send fee reminder to applicant
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Input + Flow Preview Side by Side
default_steps = """1. Receive application form
2. Check if application fee is paid
DECISION: Is the application fee paid?
CHOICE: Yes -> Proceed to document verification
CHOICE: No -> Send fee reminder to applicant
"""

col3, col4 = st.columns([1, 2])
with col3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="header">Add Steps</div>', unsafe_allow_html=True)
    st.markdown("""
    Write out the steps of your flow below. Each step should be a single action or decision.  
    New steps are added with a default type.
    """)

    st.markdown("""
    <div class="node-key">
        <span class="green">Start/End</span>
        <span class="blue">Action</span>
        <span class="yellow">Decision</span>
        <span class="red">Error</span>
    </div>
    """, unsafe_allow_html=True)

    steps_input = st.text_area(" ", value=default_steps, height=400)
    generate = st.button("Add Steps")
    st.markdown('</div>', unsafe_allow_html=True)

# Parsing logic (unchanged)
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

# Flow generator
with col4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="header">Flow Preview</div>', unsafe_allow_html=True)

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
                if "start" in text_lower or "receive" in text_lower:
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
                if last_ids:
                    return last_ids[0]
                else:
                    st.warning(f"No valid CHOICE found for decision: '{step['question']}'")
                    return prev_node

        prev = None
        i = 0
        while i < len(parsed):
            step = parsed[i]
            prev = add_step(step, prev)
            i += 1

        svg_bytes = dot.pipe(format='svg')
        svg = svg_bytes.decode('utf-8')
        st.components.v1.html(svg, height=800, scrolling=True)

        st.download_button(
            label="Download SVG Diagram",
            data=svg_bytes,
            file_name="process_flow.svg",
            mime="image/svg+xml"
        )

    st.markdown('</div>', unsafe_allow_html=True)
