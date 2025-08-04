import sys
import os
# Override default Streamlit port to avoid conflicts - must be set before importing streamlit

import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from io import BytesIO


from backend.dataaccess import DataAccess
da = DataAccess()


# ---------- Helpers ---------- #
def _get_patient_name(patient_id):
    """Helper to extract patient name based on ID"""
    query = "SELECT [FirstName], [LastName] FROM Patients WHERE PatientId = ?"
    result = da.fetch_records(query, (patient_id,))
    first, last = result[0]
    full_name = f"{first} {last}"
    return full_name


def _load_snapshot_data(path):
    """Load pre-calculated json with patients states"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == '__main__':

    # Extract snapshot path from CLI args
    snapshot_path = None
    for arg in sys.argv:
        if arg.startswith("--snapshot_path="):
            snapshot_path = arg.split("=", 1)[1]
            break

    # Page Setup
    st.set_page_config(page_title="Patient Dashboard", layout="wide")

    # JavaScript for treatment checkbox UI
    st.markdown("""
    <script>
    function toggleTreatment(patientId, treatmentIndex) {
        const checkbox = document.getElementById(check_${patientId}_${treatmentIndex});
        const text = document.getElementById(text_${patientId}_${treatmentIndex});
        if (checkbox.checked) {
            text.classList.add('treatment-completed');
        } else {
            text.classList.remove('treatment-completed');
        }
        localStorage.setItem(treatment_${patientId}_${treatmentIndex}, checkbox.checked);
    }
    window.addEventListener('load', function() {
        document.querySelectorAll('.treatment-checkbox').forEach(cb => {
            const key = cb.id.replace('check_', 'treatment_');
            if (localStorage.getItem(key) === 'true') {
                cb.checked = true;
                const text = document.getElementById(cb.id.replace('check_', 'text_'));
                if (text) text.classList.add('treatment-completed');
            }
        });
    });

    function shareThisPage() {
        const url = window.location.href;

        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(url).then(function() {
                console.log('URL copied successfully');
            }).catch(function(err) {
                console.error('Failed to copy URL: ', err);
                fallbackCopyTextToClipboard(url);
            });
        } else {
            fallbackCopyTextToClipboard(url);
        }
    }

    function fallbackCopyTextToClipboard(text) {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.top = "0";
        textArea.style.left = "0";
        textArea.style.position = "fixed";
        textArea.style.opacity = "0";

        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            const successful = document.execCommand('copy');
            console.log('Fallback: Copy command was ' + (successful ? 'successful' : 'unsuccessful'));
        } catch (err) {
            console.error('Fallback: Oops, unable to copy', err);
        }

        document.body.removeChild(textArea);
    }
    </script>
    """, unsafe_allow_html=True)

    # CSS Styling
    st.markdown("""
    <style>
        .stApp { 
            background-color: #f2f6fc; 
            transition: all 0.3s ease;
        }

        .main-title h1 {
            color: #1e3a8a !important;
            font-weight: 800 !important;
            font-size: 48px !important;
        }

        .section-title {
            color: #1e3a8a;
            font-weight: 700;
            font-size: 26px;
            margin-top: 30px;
            margin-bottom: 10px;
            transition: color 0.3s ease;
        }

        .snapshot-date {
            font-size: 18px;
            font-weight: 600;
            color: #374151;
            margin-bottom: 20px;
            transition: color 0.3s ease;
        }

        .patient-card {
            background-color: #ffffff;
            padding: 35px;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
            height: 450px;
            font-size: 16px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.3s ease;
            cursor: pointer;
            border: 2px solid transparent;
        }

        .patient-card:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.15);
            border-color: #3b82f6;
            background-color: #fafbff;
        }

        .patient-card:hover .patient-name {
            color: #2563eb;
            text-shadow: 0 1px 3px rgba(37, 99, 235, 0.3);
        }

        .patient-card:hover .indicator-circle {
            transform: scale(1.1);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }

        .patient-card.critical {
            animation: urgentBlinkSequence 8s forwards;
            border: 4px solid #dc2626;
        }

        .patient-card.critical:hover {
            transform: translateY(-8px) scale(1.02) !important;
            box-shadow: 0 12px 35px rgba(220, 38, 38, 0.4) !important;
            border-color: #dc2626 !important;
            background-color: #fef2f2 !important;
            animation-play-state: paused;
            transition: transform 0.3s ease, box-shadow 0.3s ease, background-color 0.3s ease !important;
        }

        .patient-card.critical {
            animation: urgentBlinkSequence 8s forwards;
            border: 4px solid #dc2626;
            transition: transform 0.3s ease, box-shadow 0.3s ease !important;
        }

        @keyframes urgentBlinkSequence {
            0%, 12.5%, 25%, 37.5%, 50%, 62.5%, 75%, 87.5% { 
                background-color: #ffffff;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                border-color: #dc2626;
                transform: scale(1);
            }
            6.25%, 18.75%, 31.25%, 43.75%, 56.25%, 68.75%, 81.25%, 93.75% { 
                background-color: #fef2f2;
                box-shadow: 0 12px 40px rgba(220, 38, 38, 0.8);
                border-color: #ff0000;
                transform: scale(1.02);
            }
            100% {
                background-color: #fef2f2;
                box-shadow: 0 6px 25px rgba(220, 38, 38, 0.3);
                border-color: #dc2626;
                transform: scale(1);
                animation: none;
            }
        }

        .grade-I { background-color: #ecfdf5; border-left: 6px solid #10b981; }
        .grade-II { background-color: #fefce8; border-left: 6px solid #facc15; }
        .grade-III { background-color: #fef2f2; border-left: 6px solid #f87171; }
        .grade-IV { background-color: #fef2f2; border-left: 6px solid #dc2626; }

        .patient-name { 
            font-size: 26px; 
            font-weight: 700; 
            color: #1e3a8a; 
            margin-bottom: 12px;
            transition: color 0.3s ease;
        }

        .field-title { 
            font-weight: 700; 
            color: #111827; 
            margin-bottom: 8px; 
            font-size: 22px;
            transition: color 0.3s ease;
        }

        .treatment-item { display: flex; align-items: center; margin-bottom: 10px; }
        .treatment-checkbox { margin-right: 12px; width: 20px; height: 20px; cursor: pointer; }
        .treatment-text { 
            color: #374151; 
            font-size: 20px;
            transition: color 0.3s ease;
        }
        .treatment-completed { text-decoration: line-through; color: #9ca3af; }
        .indicator-container { display: flex; justify-content: center; gap: 50px; margin-top: 25px; }
        .indicator { display: flex; flex-direction: column; align-items: center; }
        .indicator-circle { width: 80px; height: 80px; border-radius: 50%; margin-bottom: 12px; }
        .indicator-label { 
            font-size: 18px; 
            color: #374151; 
            font-weight: 600;
            transition: color 0.3s ease;
        }

        /* Footer Action Icons Styling */
        .footer-actions {
            margin-top: 50px;
            padding: 30px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        }

        .action-icons-container {
            display: flex;
            justify-content: center;
            gap: 80px;
            align-items: center;
        }

        .action-icon {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 25px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 2px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            min-width: 140px;
        }

        .action-icon:hover {
            transform: translateY(-5px) scale(1.05);
            background: rgba(255, 255, 255, 0.2);
            border-color: rgba(255, 255, 255, 0.4);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }

        .icon-symbol {
            font-size: 52px;
            margin-bottom: 12px;
            filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.3));
        }

        .icon-label {
            color: white;
            font-weight: 600;
            font-size: 18px;
            text-align: center;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
        }

        .footer-title {
            color: white;
            font-size: 24px;
            font-weight: 700;
            text-align: center;
            margin-bottom: 30px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }

        /* Download Buttons Styling */
        .stDownloadButton > button {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 15px !important;
            padding: 15px 25px !important;
            font-size: 18px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
            margin: 10px 0 !important;
        }

        .stDownloadButton > button:hover {
            transform: translateY(-3px) scale(1.05) !important;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3) !important;
            background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header with Dark/Light Mode Toggle
    header_cols = st.columns([3, 1])
    with header_cols[0]:
        st.markdown('<div class="main-title"><h1>🧑‍⚕️ Patient Dashboard</h1></div>', unsafe_allow_html=True)

    with header_cols[1]:
        # Theme toggle button
        if 'dark_mode' not in st.session_state:
            st.session_state.dark_mode = False

        if st.button("🌙 Dark Mode" if not st.session_state.dark_mode else "☀️ Light Mode", key="theme_toggle"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

    # Apply theme based on session state
    if st.session_state.dark_mode:
        st.markdown("""
        <style>
            .stApp { background-color: #1a1b23 !important; }
            .stSelectbox > div > div { background-color: #2d2e3f !important; color: #e5e7eb !important; }
            .stTextInput > div > div > input { background-color: #2d2e3f !important; color: #e5e7eb !important; }
            .stMarkdown { color: #e5e7eb !important; }
            .section-title { color: #60a5fa !important; }
            .snapshot-date { color: #e5e7eb !important; }
            .patient-card { background-color: #2d2e3f !important; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important; }
            .patient-name { color: #60a5fa !important; }
            .field-title { color: #e5e7eb !important; }
            .treatment-text { color: #e5e7eb !important; }
            .indicator-label { color: #e5e7eb !important; }
            .grade-I { background-color: #064e3b !important; }
            .grade-II { background-color: #451a03 !important; }
            .grade-III { background-color: #450a0a !important; }
            .grade-IV { background-color: #450a0a !important; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
            .stApp { background-color: #f2f6fc !important; }
            .patient-card { background-color: #ffffff !important; }
        </style>
        """, unsafe_allow_html=True)

    # Validate snapshot path
    if not snapshot_path or not os.path.exists(snapshot_path):
        st.error("❌ Snapshot file not found. Use --snapshot_path= to specify JSON path.")
        st.stop()

    # Load raw JSON and metadata
    raw = _load_snapshot_data(snapshot_path)
    # Determine snapshot date (from JSON fields)
    snapshot_date = raw.get('snapshot_date') or raw.get('date')
    # Fallback to file modified time
    if not snapshot_date:
        m = os.path.getmtime(snapshot_path)
        snapshot_date = datetime.datetime.fromtimestamp(m).strftime('%Y-%m-%d %H:%M')
    # Extract only patient entries
    patient_data = {k: v for k, v in raw.items() if k not in ['snapshot_date', 'date']}

    # Display snapshot date above filters
    st.markdown(f'<div class="snapshot-date">Snapshot date: {snapshot_date}</div>', unsafe_allow_html=True)

    # Prepare lookup for display names
    patient_names = {pid: _get_patient_name(pid) for pid in patient_data}

    # ------------------ Filters ------------------
    st.markdown('<div class="section-title">🔍 Patient Filters</div>', unsafe_allow_html=True)
    id_filter = st.text_input("", placeholder="Search patients by ID or name...", key="id_filter")
    filtered = {pid: info for pid, info in patient_data.items()
                if not id_filter or id_filter.lower() in pid.lower() or id_filter.lower() in patient_names.get(pid, "").lower()}

    # Sort by toxicity
    toxicity_order = {"GRADE IV": 4, "GRADE III": 3, "GRADE II": 2, "GRADE I": 1, "UNKNOWN": 0}
    filtered = dict(sorted(
        filtered.items(),
        key=lambda item: toxicity_order.get(item[1].get('systemic_toxicity', 'UNKNOWN').strip().upper(), 0),
        reverse=True
    ))

    # ------------------ Patient Records ------------------
    st.markdown('<div class="section-title">🗂️ Patient Records</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for idx, (pid, info) in enumerate(filtered.items()):
        col = cols[idx % 2]
        name = patient_names.get(pid, pid)
        treatments = [t.strip() for t in info.get('treatment_recommendations', '').split(';')] if info.get('treatment_recommendations') else []
        tox_val = info.get('systemic_toxicity', '').strip().upper()
        hema_val = info.get('hematological_state', '').strip().upper()

        # Determine grade class & colors
        toxicity_grades = ['GRADE I', 'GRADE II', 'GRADE III', 'GRADE IV']
        if tox_val in toxicity_grades:
            # All toxicity levels in red
            if tox_val == 'GRADE I':
                cls = 'grade-I'
            elif tox_val == 'GRADE II':
                cls = 'grade-II'
            elif tox_val == 'GRADE III':
                cls = 'grade-III'
            elif tox_val == 'GRADE IV':
                cls = 'grade-IV'
            tox_col = '#dc2626'  # Red for all toxicity levels
            tox_tooltip = tox_val  # Display original value
        elif tox_val == 'UNKNOWN':
            cls = ''
            tox_col = '#10b981'  # Green for UNKNOWN
            tox_tooltip = 'No toxicity related concepts'  # Custom text for UNKNOWN
        else:
            cls = ''
            tox_col = '#10b981'  # Green for all other values (including NO FIT etc.)
            tox_tooltip = 'No toxicity related concepts'  # Custom text for other values

        # Determine Hematological color
        hematological_values = ['PANCYTOPENIA', 'LEUKOPENIA', 'SUSPECTED POLYCYTEMIA VERA', 'ANEMIA', 'NORMAL', 'POLYHEMIA', 'SUSPECTED LEUKEMIA',
                                'LEUKEMOID REACTION', 'SUSPECTED POLYCYTEMIA VERA']
        if hema_val == 'NORMAL':
            hema_col = '#10b981'  # Green for Normal
        elif hema_val in hematological_values:
            hema_col = '#dc2626'  # Red for all other values in the list
        else:
            hema_col = '#3b82f6'  # Blue for values not in the list

        # Determine CSS class for blinking in urgent cases
        critical_class = 'critical' if tox_val == 'GRADE IV' else ''

        items_html = ''.join(
            f"<li class='treatment-item'><input type='checkbox' id='check_{pid}_{i}' class='treatment-checkbox' onchange=\"toggleTreatment('{pid}',{i})\"><span id='text_{pid}_{i}' class='treatment-text'>{t}</span></li>"
            for i, t in enumerate(treatments)
        ) or '<li>No recommendations</li>'
        card = f"""
        <div class='patient-card {cls} {critical_class}'>
        <div class='patient-name'>👤 {name} (ID: {pid})</div>
        <div class='field-title'>Treatment:</div>
        <ul>{items_html}</ul>
        <div class='indicator-container'>
            <div class='indicator'>
            <div class='indicator-circle' title='{tox_tooltip}' style='background-color:{tox_col};'></div>
            <div class='indicator-label'>Toxicity</div>
            </div>
            <div class='indicator'>
            <div class='indicator-circle' title='{hema_val}' style='background-color:{hema_col};'></div>
            <div class='indicator-label'>Hematological</div>
            </div>
        </div>
        </div>
        """
        col.markdown(card, unsafe_allow_html=True)

    # ------------------ Summary Statistics ------------------
    st.markdown('<div class="section-title">📊 Summary Statistics</div>', unsafe_allow_html=True)

    # Calculate total number of patients
    total_patients = len(filtered)
    st.markdown(f'''
    <div style="
        text-align: center; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px 40px;
        border-radius: 20px;
        margin: 20px auto;
        max-width: 400px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        border: 3px solid rgba(255, 255, 255, 0.2);
    ">
        <div style="font-size: 16px; font-weight: 500; margin-bottom: 8px; opacity: 0.9;">
            👥 TOTAL PATIENTS
        </div>
        <div style="font-size: 48px; font-weight: 800; letter-spacing: 2px;">
            {total_patients}
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Create 3 columns - empty column, chart, chart
    chart_cols = st.columns([0.5, 3, 3])

    # Toxicity Pie Chart
    with chart_cols[1]:  # Column 2
        # Replace 'Unknown' with 'No toxicity related concepts' for display
        toxicity_data = [info.get('systemic_toxicity', 'Unknown') for info in filtered.values()]
        toxicity_data = ['No toxicity related concepts' if x == 'Unknown' else x for x in toxicity_data]
        toxicity_series = pd.Series(toxicity_data)
        counts1 = toxicity_series.value_counts()

        fig1, ax1 = plt.subplots(figsize=(4, 2.5))

        # Define colors for different categories
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']


        # Create pie chart with counts instead of percentages
        def make_autopct(values):
            def my_autopct(pct):
                total = sum(values)
                val = int(round(pct * total / 100.0))
                return f'{val}'

            return my_autopct


        wedges, texts, autotexts = ax1.pie(counts1.values, labels=counts1.index,
                                        autopct=make_autopct(counts1.values),
                                        colors=colors[:len(counts1)], startangle=90,
                                        textprops={'fontsize': 7})

        # Style the pie chart
        ax1.set_title("Toxicity", fontsize=11, color="#1e3a8a", pad=6, fontweight='bold')

        # Make count text bold and white
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(8)

        # Style labels
        for text in texts:
            text.set_fontsize(6)
            text.set_color('#374151')

        # Equal aspect ratio ensures that pie is drawn as a circle
        ax1.axis('equal')
        fig1.patch.set_facecolor("white")

        plt.tight_layout()
        st.pyplot(fig1, use_container_width=True)

    # Hematological Pie Chart
    with chart_cols[2]:  # Column 3
        hematological_series = pd.Series([info.get('hematological_state', 'Unknown') for info in filtered.values()])
        counts2 = hematological_series.value_counts()

        fig2, ax2 = plt.subplots(figsize=(4, 2.5))

        # Define colors for different categories
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7B801', '#E17055']


        # Create pie chart with counts instead of percentages
        def make_autopct(values):
            def my_autopct(pct):
                total = sum(values)
                val = int(round(pct * total / 100.0))
                return f'{val}'

            return my_autopct


        wedges, texts, autotexts = ax2.pie(counts2.values, labels=counts2.index,
                                        autopct=make_autopct(counts2.values),
                                        colors=colors[:len(counts2)], startangle=90,
                                        textprops={'fontsize': 7})

        # Style the pie chart
        ax2.set_title("Hematological", fontsize=11, color="#1e3a8a", pad=6, fontweight='bold')

        # Make count text bold and white
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(8)

        # Style labels
        for text in texts:
            text.set_fontsize(6)
            text.set_color('#374151')

        # Equal aspect ratio ensures that pie is drawn as a circle
        ax2.axis('equal')
        fig2.patch.set_facecolor("white")

        plt.tight_layout()
        st.pyplot(fig2, use_container_width=True)

    # ------------------ Footer Action Icons ------------------
    st.markdown('<div class="section-title">📋 Dashboard Actions</div>', unsafe_allow_html=True)

    # Create two columns for the action buttons
    action_cols = st.columns([1, 1])

    # Excel Export Button
    with action_cols[0]:
        try:
            # Prepare data for Excel export
            rows = []
            for pid, info in filtered.items():
                row = {
                    'Patient_ID': pid,
                    'Patient_Name': patient_names.get(pid, pid),
                    'Systemic_Toxicity': info.get('systemic_toxicity', ''),
                    'Hematological_State': info.get('hematological_state', ''),
                    'Treatment_Recommendations': info.get('treatment_recommendations', '')
                }
                rows.append(row)

            df = pd.DataFrame(rows)

            # Create Excel file
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Patient_Data')

            st.download_button(
                label="📊 Export to Excel",
                data=output.getvalue(),
                file_name=f"patient_dashboard_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="excel_download",
                help="Download patient data as Excel file",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error creating Excel file: {str(e)}")

    # JSON Export Button
    with action_cols[1]:
        json_data = {
            'snapshot_date': snapshot_date,
            'total_patients': total_patients,
            'patients': filtered
        }

        json_string = json.dumps(json_data, indent=2, ensure_ascii=False)

        st.download_button(
            label="💾 Download JSON",
            data=json_string,
            file_name=f"patient_dashboard_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key="json_download",
            help="Download complete dataset as JSON",
            use_container_width=True
        )