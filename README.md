# cdss-dev-project
Developing a CDSS as a mini project

## Project Structure

```bash
cdss-dev-project/
│
├── data/
│   ├── project_db.xlsx       # Patients file
│   ├── cdss.db               # Processed DB for all operations. Created on the first run
│   ├── Loinc_2.80.zip
│
├── queries/                  # All of the queries for initialization, data access and business logic
│
├── backend/
│   ├── backend_config.py     # Configuration file for the backend operations
│   ├── dataaccess.py
│   ├── businesslogic.py
│
├── frontend/
│   ├── images/               # Images used for design
│   ├── userinterface.py
│
├── README.md
├── requirements.txt
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
(from root)
python -m backend.dataaccess
```

You can run the folowing PowerShell command in the root repository to test your business logic:
```bash
(from root)
python -m backend.businesslogic
```

Need to remove the DB you created?

```bash
rm cdss.db
```

### Run APP
In order to run the application, you'll need to navigate to the frontend folder and run the code from there:

```bash
(from root)
cd frontend
python userinterface.py
```

## GIT Commit Tips
Once you've made changes, commit and push as usual:

```bash
git add .
git commit -m "Commit message"
git push -u origin main
```
