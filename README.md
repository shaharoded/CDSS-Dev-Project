# cdss-dev-project
Developing a CDSS as a mini project

## Project Structure

```bash
cdss-dev-project/
│
├── data/
│   ├── patients.csv
│   ├── Loinc_2.80.zip
│   ├── loinc_extracted/      # Extracted on first run   
│
├── queries/                  # All of the queries for initialization, data access and business logic
│
├── backend/
│   ├── dataaccess.py
│   ├── businesslogic.py
│
├── frontend/
│   ├── userinterface.py
│
├── README.md
├── requirements.txt
└── main.py
```

## Installation
### Prerequisites

- Python 3.7 or higher.
- Loinc_2.80.zip (Downloaded from [Loinc-Org](https://loinc.org/downloads/)) - Should be placed under `data` repository.

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

## How to use
### Backend Tests

Once you updates the __main__ of each module:

You can run the folowing PowerShell command in the root repository to initiate the DataAccess class and build your DB:
```bash
python -m backend.dataaccess
```

You can run the folowing PowerShell command in the root repository to test your business logic:
```bash
python -m backend.businesslogic
```

Need to remove the DB you created?

```bash
rm cdss.db
```

### Run APP
TO-DO

## GIT Commit Tips
Once you've made changes, commit and push as usual:

```bash
git add .
git commit -m "Commit message"
git push -u origin main
```
