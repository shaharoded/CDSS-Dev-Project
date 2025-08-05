"""
Rule Processor with Two Logic Types: TABLE_LOOKUP and Default (Combination-Key)
Handles both formats efficiently while keeping the natural structure for each
"""
import json
import os
import pandas as pd
from datetime import timedelta
from backend.backend_config import *
from backend.dataaccess import DataAccess


class RuleProcessor:
    """
    Rule processor with two logic types:
    1. Default (combination-key lookup) - for hematological and treatment rules
    2. TABLE_LOOKUP - for toxicity rules with maximal OR approach
    """

    def __init__(self, rules_folder=RULES_FOLDER):
        """
        Initialize the rule processor by discovering and sorting rule file paths.

        Args:
            rules_folder (str): Path to folder containing rule JSON files. Defaults to folder in config.
        """
        self.rules_folder = rules_folder
        self.db = DataAccess()
        self._validate_rules()
        self.rule_paths = self._discover_rule_paths()


    def _validate_rules(self):
        """
        Validates the structure and logic of the rules folder.
        - Ensures 'declarative_knowledge' and 'procedural_knowledge' folders exist (creates if missing).
        - Ensures no unexpected subdirectories exist.
        - Ensures all rule files contain required keys.
        - Ensures all 'rules' condition keys are unique and have matching entries in 'values'.
        - Ensures all procedural rules have higher execution_order than all declarative ones (unless declarative is empty).

        Raises:
            Exception: If validation fails.
        """
        required_subdirs = ['declarative_knowledge', 'procedural_knowledge']
        required_keys = ['rule_name', 'execution_order', 'synthetic_loinc', 
                         'input_parameters', 'logic_type', 'rules', 'values', 'fallback_value']
        errors = []

        # Ensure base rules folder exists
        if not os.path.exists(self.rules_folder):
            os.makedirs(self.rules_folder)

        # Create missing required subdirectories and list actual ones
        actual_subdirs = []
        for req in required_subdirs:
            full_path = os.path.join(self.rules_folder, req)
            if not os.path.exists(full_path):
                print(f"[Info] Creating missing rules folder: {req}")
                os.makedirs(full_path)
            actual_subdirs.append(req)

        # Check for unexpected subdirectories
        all_subdirs = [d for d in os.listdir(self.rules_folder) if os.path.isdir(os.path.join(self.rules_folder, d))]
        for extra in set(all_subdirs) - set(required_subdirs):
            errors.append(f"Unexpected subdirectory in rules folder: {extra}")

        declarative_orders = []
        procedural_orders = []

        # Validate files in each folder
        for subdir in required_subdirs:
            full_path = os.path.join(self.rules_folder, subdir)
            for fname in os.listdir(full_path):
                if not fname.endswith('.json'):
                    continue
                path = os.path.join(full_path, fname)
                try:
                    rule_data = self._load_rule(path)

                    # Check required keys
                    missing = [k for k in required_keys if k not in rule_data]
                    if missing:
                        errors.append(f"{subdir}/{fname} missing required keys: {missing}")
                        continue

                    # Check execution order
                    order = int(rule_data['execution_order'])
                    if subdir == 'declarative_knowledge':
                        declarative_orders.append(order)
                    else:
                        procedural_orders.append(order)

                    # Check logic is valid
                    logic = rule_data['logic_type']
                    if logic not in ['AND', 'OR']:
                        errors.append(f"{logic} is not a valid logic_type. Allowed values are AND / OR")


                    # Validate condition ID uniqueness and mapping
                    rule_conditions = rule_data['rules']
                    rule_values = rule_data['values']

                    cond_ids = list(rule_conditions.keys())
                    duplicate_ids = {cid for cid in cond_ids if cond_ids.count(cid) > 1}
                    if duplicate_ids:
                        errors.append(f"{subdir}/{fname} has duplicate condition IDs: {sorted(duplicate_ids)}")

                    missing_values = [cid for cid in cond_ids if cid not in rule_values]
                    if missing_values:
                        errors.append(f"{subdir}/{fname} is missing 'values' entries for: {missing_values}")
                    
                    # Type enforcement: values and fallback_value
                    is_declarative = (subdir == 'declarative_knowledge')
                    is_procedural = (subdir == 'procedural_knowledge')

                    # Check types of all condition values
                    for cid, val in rule_values.items():
                        if is_declarative and not isinstance(val, str):
                            errors.append(f"{subdir}/{fname} → 'values[{cid}]' must be a string (got {type(val).__name__})")
                        if is_procedural and not isinstance(val, list):
                            errors.append(f"{subdir}/{fname} → 'values[{cid}]' must be a list (got {type(val).__name__})")

                    # Check fallback_value type
                    fallback_value = rule_data['fallback_value']
                    if is_declarative and not isinstance(fallback_value, str):
                        errors.append(f"{subdir}/{fname} → 'fallback_value' must be a string (got {type(fallback_value).__name__})")
                    if is_procedural and not isinstance(fallback_value, list):
                        errors.append(f"{subdir}/{fname} → 'fallback_value' must be a list (got {type(fallback_value).__name__})")

                except Exception as e:
                    errors.append(f"Failed to read/parse {subdir}/{fname}: {e}")

        # Check execution order hierarchy
        if declarative_orders and procedural_orders:
            max_decl = max(declarative_orders)
            min_proc = min(procedural_orders)
            if min_proc <= max_decl:
                errors.append(
                    f"Execution order constraint violated: "
                    f"procedural min ({min_proc}) must be > declarative max ({max_decl})"
                )

        if errors:
            raise Exception("Rules validation failed:\n" + "\n".join(errors))


    def _discover_rule_paths(self):
        """
        Discovers and categorizes rule paths by execution tier:
        - declarative_knowledge → first_tier
        - procedural_knowledge → second_tier

        Each rule JSON must include:
            - 'execution_order'
            - 'rule_name'
            - 'synthetic_loinc'
            - 'input_parameters'
            - 'rules'
            - 'values'
            - 'fallback_value'
            
        Returns:
            dict: {"first_tier": [...], "second_tier": [...]}
        """
        first_tier = []
        second_tier = []

        for subfolder, tier_list in {
            'declarative_knowledge': first_tier,
            'procedural_knowledge': second_tier
        }.items():
            full_path = os.path.join(self.rules_folder, subfolder)
            if not os.path.exists(full_path):
                continue

            for fname in os.listdir(full_path):
                if not fname.endswith('.json'):
                    continue

                path = os.path.join(full_path, fname)
                rule_data = self._load_rule(path)
                tier_list.append({
                    'file_path': path,
                    'execution_order': int(rule_data['execution_order']),
                    'rule_name': rule_data['rule_name'],
                    'synthetic_loinc': rule_data['synthetic_loinc']
                })

        return {
            "first_tier": sorted(first_tier, key=lambda r: r["execution_order"]),
            "second_tier": sorted(second_tier, key=lambda r: r["execution_order"]),
        }
    

    def _load_rule(self, rule_path):
        """
        Load a single rule file on demand.
        Assumes all rules are valid to engine demands (pass _validate_rule_repository_structure())

        Args:
            rule_path (str): Rule path

        Returns:
            dict: Loaded rule data
        """
        try:
            with open(rule_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load rule: {rule_path}: {e}")
    

    def _search_param(self, param_list, df, patient_id, state=None):
        """
        Retrieve latest value for each parameter from:
        1) Patients table (columns returned by GET_PATIENT_PARAMS_QUERY)
        2) Current in-memory state cache (results already computed in this run)
        3) The abstracted DataFrame (via ConceptName)
        
        The query GET_PATIENT_PARAMS_QUERY will return all available column parameters of a patient.

        Args:
            param_list (list): List of parameter names (case-insensitive)
            df (pd.DataFrame): Abstracted measurements for a single patient
            patient_id (str): Patient ID (required for Patients table lookup)
            state (dict, optional): Current calculated state based on prior calculated rules.

        Returns:
            dict: {original_param_name: value for patient or None}
        
        NOTE: This function outputs param_values which is a dict of all existing parameters in current df + state
              that can satisfy a specific rule (based on its param_list).
        """
        state = state or {}
        param_list_lower = [p.lower() for p in param_list]
        param_values = {original: None for original in param_list}

        # --- Patients table ---
        try:
            results = self.db.fetch_records(GET_PATIENT_PARAMS_QUERY, (patient_id,))
            if not results:
                raise Exception(f"No record found for PatientId {patient_id}")
            row = results[0]
            columns = [desc[0].lower() for desc in self.db.cursor.description]
            patients_data = dict(zip(columns, row))
        except Exception as e:
            raise Exception(f"Failed to retrieve Patients table data for {patient_id}: {e}")

        # --- Resolve each param ---
        for original_param, param_lower in zip(param_list, param_list_lower):
            # 1) Patients table
            if param_lower in patients_data:
                param_values[original_param] = patients_data[param_lower]
                continue

            # 2) State cache (results already computed in this run)
            #    Keep lookup case-insensitive by normalizing keys
            state_lookup = {k.lower(): v for k, v in state.items()}
            if param_lower in state_lookup and state_lookup[param_lower] is not None:
                param_values[original_param] = state_lookup[param_lower]
                continue

            # 3) DataFrame (synthetic/abstracted rows)
            match = df[df['ConceptName'].str.lower() == param_lower]
            if not match.empty:
                latest_row = match.loc[match['StartDateTime'].idxmax()]
                param_values[original_param] = latest_row['Value']
            else:
                # Populate non-found parameters with None
                param_values[original_param] = None

        return param_values
    

    def _apply_AND_rule(self, rule_json, input_values):
        """
        Apply a structured AND rule to the input values.
        Input values are the direct output of the function _search_param() on the current patient's state.

        Args:
            rule_json (dict): A single rule object with 'rules', 'values', and 'fallback_value'
            input_values (dict): {param_name: value} for this patient at this rule application step

        Returns:
            str: The resulting classification from rule evaluation (or fallback). 
                 Either str (declarative) or list (procedural).
        """
        rules, values, fallback = rule_json["rules"], rule_json["values"], rule_json["fallback_value"]

        for cond_id, condition in rules.items():
            match = True
            for param, allowed_values in condition.items():
                actual_value = input_values.get(param)

                # If any param is missing or doesn't match allowed list → rule fails
                if actual_value is None or str(actual_value) not in allowed_values:
                    match = False
                    break

            if match:
                return values.get(cond_id, fallback)

        return fallback
    

    def _apply_OR_rule(self, rule_json, input_values):
        """
        Apply an OR logic rule where we select the maximal severity based on partial param matches.

        Args:
            rule_json (dict): Rule definition.
            input_values (dict): Patient values.

        Returns:
            str: The most severe matched condition's output (or fallback).
        """
        rules, values, fallback = rule_json["rules"], rule_json["values"], rule_json["fallback_value"]

        max_idx = -1
        matched_cond_id = None

        for idx, (cond_id, condition) in enumerate(rules.items()):
            for param, allowed_values in condition.items():
                actual_value = input_values.get(param)
                if actual_value is not None and str(actual_value) in allowed_values:
                    if idx > max_idx:
                        max_idx = idx
                        matched_cond_id = cond_id
                    break  # OR logic → one match is enough in this condition

        return values.get(matched_cond_id, fallback)
    

    def _apply_rule(self, rule_json, input_values):
        """Wrapper to choose which logic to use"""
        logic = rule_json.get("logic_type", "AND")
        if logic == "OR":
            return self._apply_OR_rule(rule_json, input_values)
        else:
            return self._apply_AND_rule(rule_json, input_values)
    

    def run(self, patient_id, df):
        """
        Process all rules for a single patient with consistent key ordering.

        Args:
            patient_id (str or int): The unique ID of a patient from the DB.
            df (pd.DataFrame): The patient's abstracted data extracted from the DB.

        Returns: 
            results (dict): A patient's state dictionary that collects all state information + treatment.

            NOTE: results.keys() Should be equal to all names (rule['rule_name']) that exists in the self.rules_folder.
        """
        df = df.copy() # In case of df mutation down the road
        
        # Initialize results with desired key order
        results = {
            "PatientId": patient_id
        }

        # Process rules iteratively tier-by-tier (each tier sorted by execution_order)
        for tier in self.rule_paths.keys():
            for rule_path_info in self.rule_paths[tier]:
                # Get next rule in queue
                path = rule_path_info['file_path']
                rule_json = self._load_rule(path)
                rule_name, param_list = rule_json['rule_name'], rule_json['input_parameters']

                # Apply rule on current calculated state
                input_values = self._search_param(param_list, df, patient_id, state=results)
                classification = self._apply_rule(rule_json, input_values)

                # Add results to patient's state
                classification = ';'.join(classification) if isinstance(classification, list) else classification
                results[rule_name] = classification

        return results
    

    def debug_patient_rule_flow(self, patient_id, df):
        """
        Debug one patient's rule progression across tiers.
        Prints input values and classifications for each rule.
        """
        df = df.copy()
        print(f"\n[DEBUG] Starting rule trace for patient {patient_id}")
        print(f"\n[Initial Abstracted Dataset]")
        print(df)
        results = {"PatientId": patient_id}

        for tier in self.rule_paths.keys():
            print(f"\n[DEBUG] Processing tier: {tier}")
            for rule_path_info in self.rule_paths[tier]:
                path = rule_path_info['file_path']
                rule_json = self._load_rule(path)
                rule_name, param_list = rule_json['rule_name'], rule_json['input_parameters']

                input_values = self._search_param(param_list, df, patient_id, state=results)
                print(f"[DEBUG] Rule: {rule_name}")
                print(f"[DEBUG] Input Values: {input_values}")

                classification = self._apply_rule(rule_json, input_values)

                # Add results to patient's state
                classification = ';'.join(classification) if isinstance(classification, list) else classification
                results[rule_name] = classification
                print(f"[DEBUG] Classification: {classification}")

        return results
    

if __name__ == "__main__":
    snapshot_date = "2025-08-02 23:59:59"
    data = DataAccess()
    proc = RuleProcessor()
    patient_id = '147258369'
    df = pd.DataFrame(data.fetch_records(
    GET_ABSTRACTED_DATA_QUERY,
    (snapshot_date, snapshot_date)), columns=[
            'PatientId', 'LOINC-Code', 'ConceptName', 'Value', 'StartDateTime', 'EndDateTime'
        ])

    # --- Validate results / abstract ---
    if df.empty:
        from backend.businesslogic import abstract_data
        abstract_data(snapshot_date)
        df = pd.DataFrame(data.fetch_records(
        GET_ABSTRACTED_DATA_QUERY,
        (snapshot_date, snapshot_date)), columns=[
                'PatientId', 'LOINC-Code', 'ConceptName', 'Value', 'StartDateTime', 'EndDateTime'
            ])
        if df.empty:
            raise ValueError(f"No patients found with relevant data in the selected snapshot date-time {snapshot_date}")
    
    df = df[df['PatientId'] == patient_id].copy()
    proc.debug_patient_rule_flow(patient_id, df)