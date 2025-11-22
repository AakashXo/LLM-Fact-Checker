import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import streamlit as st
import json
from src.fact_checker import FactChecker

st.set_page_config(page_title="Fact Checker", layout="wide")
st.title(" Fact Checking System using PIB Verified Data")

input_text = st.text_area(
    "Enter any claim or headline to verify:",
    height=150,
    placeholder="Example: The government is giving free electricity to all farmers from July 2025."
)

if st.button("🔍 Check Facts"):
    if input_text.strip():
        with st.spinner("Checking facts... Please wait"):
            checker = FactChecker()
            results = checker.fact_check_text(input_text)

        if not results:
            st.warning(
                "⚠ I couldn't detect any clear factual claim. "
                "Please enter a full sentence like: "
                "'The government has announced free electricity to all farmers from July 2025.'"
            )
        else:
            st.subheader("📜 Results:")
            for res in results:
                st.write(f"### Claim: {res['claim']}")
                verdict = res["verdict"]
                if verdict == "True":
                    st.markdown("**Verdict:** 🟢 **True**")
                elif verdict == "False":
                    st.markdown("**Verdict:** 🔴 **False**")
                else:
                    st.markdown("**Verdict:** ⚪ **Unverifiable**")
                st.write(f"**📝 Reasoning:** {res['reasoning']}")

                if verdict in ("True", "False") and res.get("evidence"):
                    st.write("**📚 Evidence from PIB:**")
                    for ev in res["evidence"]:
                        st.write(f"🔹 {ev}")
    # For Unverifiable, do not show evidence at all  
                st.write("---")


    
