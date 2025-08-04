# cdss-dev-project
Developing a CDSS as a mini project.
The system is designed to offer patients management front and patients state dashboard, which reports on the patients in risk within your DB as of a chosen date.

---

## Project Structure

```bash
cdss-dev-project/
│
├── data/
│   ├── project_db.xlsx       # Patients batch file
│   ├── cdss.db               # Processed DB for all operations. Created automatically.
│   └── Loinc_2.80.zip
│
├── backend/
├── ├── queries/                        # All of the queries for initialization, data access and business logic
│   │   ├── create_patients_table.sql
│   │   ├── create_loinc_table.sql
│   │   ├── insert_patient.sql
│   │   └── ...
│   │
├── ├── tak/                            # All abstraction rules (TAK files).
│   │   ├── hemoglobin_state.xml
│   │   ├── wbc_state.xml
│   │   └── ...
├── ├── rules/                          
│   │   ├── declarative_knowledge/      # All state rules (Json files).
│   │   │   ├── hematological_rules.json
│   │   │   └── toxicity_rules.json
│   │   └── procedural_knowledge/       # All procedural rules (Json files).
│   │       └── treatment_rules.json
│   │
│   ├── backend_config.py               # Configuration file for the backend operations
│   ├── dataaccess.py                   # DB connection module
│   ├── businesslogic.py                # Business logic module
│   ├── mediator.py                     # Data abstraction calculation module
│   └── rule_processor.py               # Rule-based patient's state inference module
│
├── frontend/
│   ├── images/                         # Images used for design
│   ├── userinterface.py                # UI - Data management system
│   └── dashboard.py                    # UI - Streamlit recommendation board
│
├── README.md
└── requirements.txt
```
---

## Installation
### Prerequisites

- Python 3.7 or higher.
- Loinc_2.80.zip (Downloaded from [Loinc-Org](https://loinc.org/downloads/)) - Should be placed under `data` repository.

NOTE: For the recommendation system section of thsi project, the LOINC table was modified, re-zipped and used, adding a few SNOMED codes to it for the engine's rules. 

### Setup

1. Clone the repository:

```bash
git clone https://github.com/shaharoded/cdss-dev-project.git
cd cdss-dev-project
```

2. Create and activate a virtual environment:

```bash
# On Windows
python -m venv venv
.\venv\Scripts\Activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```
---

## How to use
### Backend Tests

Once you updates the __main__ of each module:

You can run the following PowerShell command in the root repository to initiate the DataAccess class and build your DB:
```bash
(from root)
python -m backend.dataaccess
```

You can run the following PowerShell command in the root repository to test your business logic:
```bash
(from root)
python -m backend.businesslogic
```

You can run the following PowerShell command in the root repository to test your abstraction logic:
```bash
(from root)
python -m backend.mediator
```

Need to remove the DB you created?

```bash
rm cdss.db
```

### Run APP
In order to run the application, you'll need to run the following command from root repo:

```bash
(from root)
python -m frontend.userinterface
```

Within the app you'll have the option to open the patient's state screen (streamlit dashboard).

---

## GIT Commit Tips
Once you've made changes, commit and push as usual:

```bash
git add .
git commit -m "Commit message"
git push -u origin main
```
