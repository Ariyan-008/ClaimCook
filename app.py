
import streamlit as st
from pathlib import Path
import re
import io

# =========================================================
# CLAIMCOOK — INSURANCE CLAIM ASSISTANT
# =========================================================

st.set_page_config(
    page_title="ClaimCook | Insurance, Made Clear",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).parent
LOGO_PATH = BASE_DIR / "claimcook_logo.jpeg"

# Brand colours from your logo
NAVY = "#10234F"
NAVY_LIGHT = "#193768"
MINT = "#61C9A5"
BG = "#F5F8FC"
MUTED = "#65738B"
BORDER = "#E1E8F1"

# =========================================================
# CUSTOM DESIGN
# =========================================================

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
}}

.stApp {{
    background: {BG};
}}

[data-testid="stSidebar"] {{
    background: white;
    border-right: 1px solid {BORDER};
}}

.block-container {{
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}}

h1, h2, h3, h4 {{
    font-family: 'Manrope', sans-serif !important;
    color: {NAVY};
    letter-spacing: -0.025em;
}}

.hero {{
    background: linear-gradient(120deg, {NAVY}, {NAVY_LIGHT});
    color: white;
    border-radius: 23px;
    padding: 36px;
    margin: 20px 0 25px 0;
}}

.hero h1 {{
    color: white !important;
    font-size: 42px;
    line-height: 1.15;
}}

.hero p {{
    color: #DCE7F8;
    font-size: 16px;
    max-width: 650px;
    line-height: 1.7;
}}

.eyebrow {{
    color: {MUTED};
    font-size: 11px;
    font-weight: 800;
    letter-spacing: .13em;
    text-transform: uppercase;
}}

.panel {{
    background: white;
    border: 1px solid {BORDER};
    border-radius: 17px;
    padding: 23px;
    margin-bottom: 16px;
    box-shadow: 0 5px 18px rgba(16,35,79,.025);
}}

.panel-title {{
    color: {NAVY};
    font-weight: 800;
    font-size: 18px;
    margin: 8px 0;
}}

.muted {{
    color: {MUTED};
    font-size: 13px;
    line-height: 1.6;
}}

.metric {{
    color: {NAVY};
    font-family: 'Manrope', sans-serif;
    font-size: 25px;
    font-weight: 800;
    margin: 8px 0;
}}

.pill {{
    display: inline-block;
    background: #E8F8F1;
    color: #176B52;
    border-radius: 999px;
    padding: 6px 11px;
    font-size: 11px;
    font-weight: 800;
}}

.stButton button {{
    border-radius: 10px;
    min-height: 43px;
    font-weight: 700;
}}

.stButton button[kind="primary"] {{
    background: {NAVY};
    color: white;
    border: 1px solid {NAVY};
}}

.stButton button[kind="primary"]:hover {{
    background: {NAVY_LIGHT};
    border-color: {NAVY_LIGHT};
}}

div[data-testid="stTextArea"] textarea,
div[data-testid="stTextInput"] input {{
    border-radius: 10px;
}}

.footer {{
    color: {MUTED};
    font-size: 12px;
    border-top: 1px solid {BORDER};
    padding-top: 17px;
    margin-top: 30px;
}}
</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "claim_ref": "CC-2026-001",
    "claim_type": "Health insurance",
    "claim_stage": "Documents requested",
    "claim_status": "Awaiting your action",
    "message": "",
    "draft": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =========================================================
# DOCUMENT DETECTION RULES
# =========================================================

DOCUMENT_RULES = {
    "Identity proof": [
        "identity proof", "identity document",
        "id proof", "identity card", "aadhaar"
    ],
    "Medical bills": [
        "medical bill", "hospital bill",
        "treatment bill", "itemized bill"
    ],
    "Discharge summary": [
        "discharge summary", "hospital discharge"
    ],
    "Prescription": [
        "prescription", "doctor's advice",
        "doctors advice"
    ],
    "Diagnostic reports": [
        "diagnostic report", "lab report",
        "test report", "scan report"
    ],
    "Claim form": [
        "claim form", "completed claim form"
    ],
    "Repair estimate": [
        "repair estimate", "repair quotation",
        "garage estimate"
    ],
    "FIR / Police report": [
        "fir", "police report",
        "first information report"
    ],
    "Photographs": [
        "photographs", "photos of damage",
        "pictures of damage"
    ],
    "Bank details": [
        "bank details", "cancelled cheque",
        "bank account proof"
    ],
}

def detect_documents(message):
    text = message.lower()
    found = []

    for document, keywords in DOCUMENT_RULES.items():
        if any(word in text for word in keywords):
            found.append(document)

    return found


def read_uploaded_file(uploaded_file):
    """Read text from PDF or TXT uploads."""
    if uploaded_file is None:
        return ""

    filename = uploaded_file.name.lower()

    try:
        if filename.endswith(".txt"):
            return uploaded_file.getvalue().decode(
                "utf-8", errors="ignore"
            )

        if filename.endswith(".pdf"):
            from pypdf import PdfReader

            reader = PdfReader(
                io.BytesIO(uploaded_file.getvalue())
            )

            return "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

    except Exception:
        return ""

    return ""


def check_document(document, uploaded_files):
    """Check whether a document name appears in uploaded filenames/text."""
    terms = [
        term for term in re.findall(
            r"[a-z]+", document.lower()
        ) if len(term) > 2
    ]

    for uploaded_file in uploaded_files or []:
        filename = (
            uploaded_file.name.lower()
            .replace("_", " ")
            .replace("-", " ")
        )

        content = read_uploaded_file(uploaded_file).lower()
        combined = filename + " " + content

        if document.lower() in combined:
            return True

        if terms and all(term in combined for term in terms):
            return True

    return False


def explain_insurer_message(message):
    """Simple rule-based explanations for common insurer messages."""
    text = message.lower()
    explanations = []

    if any(word in text for word in [
        "additional documents",
        "supporting documents",
        "submit documents",
        "required documents",
        "provide the following"
    ]):
        explanations.append(
            "The insurer is asking you to provide documents "
            "or information before continuing its assessment."
        )

    if any(word in text for word in [
        "under review", "under assessment",
        "being processed", "in process"
    ]):
        explanations.append(
            "Your claim appears to be under review. "
            "This message alone does not confirm approval or rejection."
        )

    if any(word in text for word in [
        "rejected", "repudiated", "denied", "declined"
    ]):
        explanations.append(
            "The message appears to communicate a rejection or decline. "
            "Check the stated reason, relevant policy terms, and "
            "any available review or grievance process."
        )

    if any(word in text for word in [
        "approved", "accepted", "settled"
    ]):
        explanations.append(
            "The message appears to indicate approval or settlement. "
            "Check the amount, deductions, conditions, and remaining steps."
        )

    if any(word in text for word in [
        "deficiency", "incomplete",
        "missing information", "shortfall"
    ]):
        explanations.append(
            "The insurer may believe some information is missing "
            "or incomplete. Look for the exact item requested."
        )

    if not explanations:
        explanations.append(
            "Check the message for the requested action, reason, "
            "documents, and any deadline. This prototype could not "
            "confidently classify the wording."
        )

    return explanations


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
    else:
        st.markdown(
            f"<h2 style='color:{NAVY}'>✓ ClaimCook</h2>",
            unsafe_allow_html=True
        )

    st.caption("Insurance, made clearer.")
    st.divider()

    page = st.radio(
        "WORKSPACE",
        [
            "Overview",
            "Understand a Message",
            "Document Checker",
            "Reply Assistant",
            "Claim Timeline",
        ],
    )

    st.divider()

    st.markdown(
        "<span class='pill'>SIH 2026 · PROTOTYPE</span>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p class='muted'>Understand requirements. "
        "Prepare documents. Know your next step.</p>",
        unsafe_allow_html=True
    )

# =========================================================
# PAGE HEADER
# =========================================================

st.markdown(
    "<div class='eyebrow'>YOUR CLAIM, WITHOUT THE CONFUSION</div>",
    unsafe_allow_html=True
)

st.markdown(
    f"<h2 style='margin-top:5px'>Welcome to ClaimCook.</h2>",
    unsafe_allow_html=True
)

# =========================================================
# OVERVIEW PAGE
# =========================================================

if page == "Overview":

    st.markdown("""
    <div class="hero">
        <div style="color:#61C9A5;font-weight:800;
                    letter-spacing:2px;font-size:12px">
            A CLEARER CLAIM JOURNEY
        </div>
        <h1>Know what to do next.</h1>
        <p>
            Understand insurer messages, identify potential document
            gaps, and prepare replies through one simple workspace.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="panel">
            <div class="eyebrow">SAMPLE CLAIM</div>
            <div class="metric">{st.session_state.claim_ref}</div>
            <div class="muted">{st.session_state.claim_type}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="panel">
            <div class="eyebrow">CURRENT STAGE</div>
            <div class="metric" style="font-size:19px">
                {st.session_state.claim_stage}
            </div>
            <div class="muted">Manually updated</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="panel">
            <div class="eyebrow">STATUS</div>
            <div class="metric" style="font-size:20px">
                {st.session_state.claim_status}
            </div>
            <div class="muted">Not connected to insurer systems</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### What do you need help with?")

    left, right = st.columns(2)

    with left:
        st.markdown("""
        <div class="panel">
            <div style="font-size:27px">⌕</div>
            <div class="panel-title">Understand a message</div>
            <div class="muted">
                Simplify confusing insurer language and identify
                common requests.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(
            "Understand a message →",
            type="primary",
            use_container_width=True
        ):
            st.session_state.page_target = "Understand a Message"
            st.rerun()

    with right:
        st.markdown("""
        <div class="panel">
            <div style="font-size:27px">▤</div>
            <div class="panel-title">Check your documents</div>
            <div class="muted">
                Compare requested document types with the files
                you currently have.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(
            "Check documents →",
            use_container_width=True
        ):
            st.session_state.page_target = "Document Checker"
            st.rerun()

    st.markdown("### How ClaimCook works")

    a, b, c = st.columns(3)

    with a:
        st.markdown("""
        <div class="panel">
            <span class="pill">01 · UNDERSTAND</span>
            <div class="panel-title">Paste the message</div>
            <div class="muted">
                Start with the communication you received from your insurer.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with b:
        st.markdown("""
        <div class="panel">
            <span class="pill">02 · PREPARE</span>
            <div class="panel-title">Review the checklist</div>
            <div class="muted">
                Check requested documents and potential gaps.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c:
        st.markdown("""
        <div class="panel">
            <span class="pill">03 · RESPOND</span>
            <div class="panel-title">Draft a reply</div>
            <div class="muted">
                Prepare a response and verify it before sending.
            </div>
        </div>
        """, unsafe_allow_html=True)

    if "page_target" in st.session_state:
        target = st.session_state.pop("page_target")
        st.info(
            f"Select **{target}** from the sidebar to continue."
        )

# =========================================================
# UNDERSTAND MESSAGE PAGE
# =========================================================

elif page == "Understand a Message":

    st.markdown("## Understand an insurer message")

    st.write(
        "Paste the message from your insurer to get a simpler "
        "explanation of common wording."
    )

    message = st.text_area(
        "Insurer message",
        value=st.session_state.message,
        placeholder=(
            "Example: Please submit the hospital bills and "
            "discharge summary before further assessment."
        ),
        height=170,
    )

    if st.button("Explain message", type="primary"):

        if not message.strip():
            st.warning("Please paste a message first.")

        else:
            st.session_state.message = message

            st.markdown("### In simpler language")

            for explanation in explain_insurer_message(message):
                st.info(explanation)

            requirements = detect_documents(message)

            if requirements:
                st.markdown("### Documents mentioned")

                for document in requirements:
                    st.write(f"✓ {document}")

            else:
                st.caption(
                    "No supported document types were detected "
                    "by the current keyword rules."
                )

            st.warning(
                "This is a rule-based prototype. It does not provide "
                "an official insurer interpretation or decide coverage."
            )

# =========================================================
# DOCUMENT CHECKER PAGE
# =========================================================

elif page == "Document Checker":

    st.markdown("## Document checklist")

    st.write(
        "Enter the insurer's request and upload the documents "
        "you currently have."
    )

    request = st.text_area(
        "What did your insurer request?",
        placeholder=(
            "Example: Please provide the medical bills, "
            "discharge summary and prescriptions."
        ),
        height=130,
    )

    uploaded_files = st.file_uploader(
        "Upload available documents",
        type=["pdf", "txt", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help=(
            "PDF and TXT text can be searched. Image files are accepted "
            "but their contents are not read in this prototype."
        ),
    )

    if st.button("Check my documents", type="primary"):

        if not request.strip():
            st.warning("Please enter the insurer's request.")

        else:
            requirements = detect_documents(request)

            if not requirements:
                st.warning(
                    "No supported document names were detected. "
                    "Review the original request manually."
                )

            else:
                matches = 0

                for document in requirements:

                    if check_document(document, uploaded_files):
                        matches += 1
                        st.success(
                            f"Possible match found: {document}"
                        )

                    else:
                        st.warning(
                            f"Potential gap: {document}"
                        )

                st.progress(matches / len(requirements))

                st.markdown(
                    f"**Potential matches:** {matches} of "
                    f"{len(requirements)} requested document types."
                )

                st.caption(
                    "A filename or text match does not prove that "
                    "a document is complete, valid, or accepted by "
                    "the insurer. Please verify each result."
                )

# =========================================================
# REPLY ASSISTANT PAGE
# =========================================================

elif page == "Reply Assistant":

    st.markdown("## Reply assistant")

    st.write(
        "Prepare a polite draft response. You can edit and "
        "download it before sending."
    )

    insurer = st.text_input(
        "Insurer name (optional)"
    )

    claim_ref = st.text_input(
        "Claim reference (optional)",
        value=st.session_state.claim_ref
    )

    original_message = st.text_area(
        "Insurer's original message",
        height=120,
        placeholder="Paste the original message here..."
    )

    reply_type = st.selectbox(
        "What do you want to do?",
        [
            "Submit requested documents",
            "Ask what is missing",
            "Request a claim update",
            "Ask for clarification about a decision",
        ]
    )

    if st.button("Generate reply", type="primary"):

        if not original_message.strip():
            st.warning(
                "Paste the insurer's message before generating a reply."
            )

        else:

            replies = {
                "Submit requested documents": (
                    "I am responding to your request regarding my "
                    "insurance claim. I am submitting the available "
                    "documents for your review. Please confirm receipt "
                    "and let me know if further information is required."
                ),

                "Ask what is missing": (
                    "Could you please specify which documents or "
                    "information are still outstanding, along with "
                    "any required format and submission deadline?"
                ),

                "Request a claim update": (
                    "Could you please provide an update on the current "
                    "status of my claim and let me know whether any "
                    "action is required from my side?"
                ),

                "Ask for clarification about a decision": (
                    "Could you please explain the reasons for the "
                    "decision and identify the relevant policy terms "
                    "or documents considered? Please also share any "
                    "applicable review or grievance process."
                ),
            }

            draft = f"""Subject: Regarding my insurance claim {claim_ref}

Dear Claims Team{f' at {insurer}' if insurer else ''},

{replies[reply_type]}

For reference, the message I received was:
"{original_message}"

Thank you for your assistance.

Kind regards,
[Your name]
"""

            st.session_state.draft = draft

    if st.session_state.draft:

        st.markdown("### Review your draft")

        edited_draft = st.text_area(
            "Edit before sending",
            value=st.session_state.draft,
            height=280,
        )

        st.session_state.draft = edited_draft

        st.download_button(
            "Download reply as TXT",
            data=edited_draft,
            file_name="claimcook_reply.txt",
            mime="text/plain",
        )

        st.caption(
            "The reply is not sent automatically. Verify all details "
            "and attach the correct documents before sending."
        )

# =========================================================
# CLAIM TIMELINE PAGE
# =========================================================

elif page == "Claim Timeline":

    st.markdown("## Your claim timeline")

    st.write(
        "Update the timeline using information from your insurer. "
        "Updates are manual in this prototype."
    )

    stages = [
        "Claim initiated",
        "Documents submitted",
        "Documents requested",
        "Under assessment",
        "Decision communicated",
        "Claim completed",
    ]

    statuses = [
        "In progress",
        "Awaiting your action",
        "Awaiting insurer",
        "Completed",
    ]

    with st.form("claim_timeline_form"):

        current_stage = st.selectbox(
            "Current stage",
            stages,
            index=(
                stages.index(st.session_state.claim_stage)
                if st.session_state.claim_stage in stages
                else 0
            ),
        )

        current_status = st.selectbox(
            "Claim status",
            statuses,
            index=(
                statuses.index(st.session_state.claim_status)
                if st.session_state.claim_status in statuses
                else 0
            ),
        )

        claim_reference = st.text_input(
            "Claim reference",
            value=st.session_state.claim_ref,
        )

        claim_type = st.selectbox(
            "Claim type",
            [
                "Health insurance",
                "Motor insurance",
                "Travel insurance",
                "Other",
            ],
            index=[
                "Health insurance",
                "Motor insurance",
                "Travel insurance",
                "Other",
            ].index(st.session_state.claim_type)
            if st.session_state.claim_type in [
                "Health insurance",
                "Motor insurance",
                "Travel insurance",
                "Other",
            ] else 0,
        )

        submitted = st.form_submit_button(
            "Save timeline",
            type="primary",
        )

    if submitted:
        st.session_state.claim_stage = current_stage
        st.session_state.claim_status = current_status
        st.session_state.claim_ref = claim_reference
        st.session_state.claim_type = claim_type

        st.success("Timeline updated for this session.")

    st.markdown("### Claim progress")

    current_index = stages.index(
        st.session_state.claim_stage
    )

    for index, stage in enumerate(stages):

        if index < current_index:
            st.success(f"✓ {stage} — previous stage")

        elif index == current_index:
            st.info(
                f"● {stage} — CURRENT: "
                f"{st.session_state.claim_status}"
            )

        else:
            st.write(f"○ {stage} — upcoming")

    st.caption(
        "The timeline is manually updated and is not connected "
        "to your insurer's systems."
    )

# =========================================================
# FOOTER
# =========================================================

st.markdown("""
<div class="footer">
    <b>ClaimCook</b> · SIH 2026 prototype<br>
    General process guidance only. ClaimCook does not guarantee
    claim approval, decide policy coverage, or replace official
    insurer communication.
</div>
""", unsafe_allow_html=True)
