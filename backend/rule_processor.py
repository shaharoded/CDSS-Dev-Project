"""
Rule Processor with Two Logic Types: TABLE_LOOKUP and Default (Combination-Key)
Handles both formats efficiently while keeping the natural structure for each
"""
import json
import os
import pandas as pd
from datetime import datetime, timedelta
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
        self.rule_paths = self._discover_rule_paths()

    def _discover_rule_paths(self):
        """
        Discover and sort rule file paths by hierarchy level.
        Recursively searches through subfolders for JSON rule files.
        Only reads the hierarchy_level field from each file.

        Returns:
            dict: Organized rule file paths by tier level
        """
        rule_paths = {"first_tier": [], "second_tier": []}

        if not os.path.exists(self.rules_folder):
            print(f"[Warning] Rules folder not found: {self.rules_folder}")
            return rule_paths

        # Recursively walk through all subdirectories
        for root, dirs, files in os.walk(self.rules_folder):
            for file_name in files:
                if file_name.endswith('.json'):
                    file_path = os.path.join(root, file_name)

                    try:
                        with open(file_path, 'r') as f:
                            rule_data = json.load(f)

                        hierarchy_level = rule_data.get('hierarchy_level')
                        rule_name = rule_data.get('rule_name', file_name)
                        synthetic_loinc = rule_data.get('synthetic_loinc', 'UNKNOWN')

                        if hierarchy_level in ["first_tier", "second_tier"]:
                            rule_paths[hierarchy_level].append({
                                'file_path': file_path,
                                'rule_name': rule_name,
                                'synthetic_loinc': synthetic_loinc
                            })

                            # Get relative path for cleaner logging
                            rel_path = os.path.relpath(file_path, self.rules_folder)
                            #print(f"[Info] Discovered {hierarchy_level} rule: {rule_name} ({synthetic_loinc}) at {rel_path}")
                        else:
                            print()

                    except Exception as e:
                        print(f"[Error] Failed to read rule file {file_name}: {e}")

        #print(f"[Info] Discovered {len(rule_paths['first_tier'])} first-tier and {len(rule_paths['second_tier'])} second-tier rule files")
        return rule_paths
    def _load_rule(self, rule_path_info):
        """
        Load a single rule file on demand.

        Args:
            rule_path_info (dict): Rule path information containing 'file_path'

        Returns:
            dict or None: Loaded rule data or None if loading failed
        """
        try:
            with open(rule_path_info['file_path'], 'r') as f:
                rule_data = json.load(f)

            # Validate required fields
            required_fields = ['rule_name', 'hierarchy_level', 'synthetic_loinc', 'input_parameters']
            missing_fields = [field for field in required_fields if field not in rule_data]

            if missing_fields:
                print(f"[Warning] Missing required fields in {rule_path_info['file_path']}: {missing_fields}")
                return None

            return rule_data

        except Exception as e:
            print(f"[Error] Failed to load rule file {rule_path_info['file_path']}: {e}")
            return None

    def get_param(self, rule_json):
        """
        Extract required input parameters from rule definition.

        Args:
            rule_json (dict): Rule definition containing input_parameters

        Returns:
            list: List of parameter names required for this rule
        """
        return rule_json.get('input_parameters', [])

    def search_param(self, param_list, df, patient_id=None):
        """
        Retrieve the latest value for each parameter from patient DataFrame or Patients table.
        Special handling for 'gender' parameter which comes from Patients table.

        Args:
            param_list (list): List of parameter names to search for
            df (pd.DataFrame): Patient-specific abstracted measurements DataFrame
            patient_id (str, optional): Patient ID for querying Patients table

        Returns:
            dict: Dictionary mapping parameter names to their latest values
        """
        param_values = {}

        for param in param_list:
            if param.lower() in ['gender', 'sex'] and patient_id:
                try:
                    gender_result = self.db.fetch_records(
                        "SELECT Sex FROM Patients WHERE PatientId = ?",
                        (patient_id,)
                    )
                    if gender_result:
                        param_values[param] = gender_result[0][0]
                        #print(f"[Debug] Found {param} in Patients table: {param_values[param]}")
                        continue
                    else:
                        print(f"[Warning] Patient {patient_id} not found in Patients table")
                except Exception as e:
                    print(f"[Warning] Failed to get gender from Patients table: {e}")

            # Search for the exact parameter name in the DataFrame
            exact_match = df[df['Concept Name'] == param]
            if not exact_match.empty:
                latest_row = exact_match.loc[exact_match['StartDateTime'].idxmax()]
                param_values[param] = latest_row['Value']
                #print(f"[Debug] Found {param} in DataFrame: {param_values[param]}")
            else:
                param_values[param] = None
                #print(f"[Warning] Parameter '{param}' not found in patient data")
                #print(f"[Debug] Available concepts: {df['Concept Name'].tolist()}")

        return param_values
    def apply_rule(self, rule_json, input_values):
        """
        Apply rule logic based on the rule's logic type.

        Args:
            rule_json (dict): Rule definition
            input_values (dict): Parameter values to classify

        Returns:
            str or None: Classification result or None if no match
        """
        logic_type = rule_json.get('logic_type', 'DEFAULT')

        if logic_type == 'TABLE_LOOKUP':
            return self._apply_table_lookup(rule_json, input_values)
        else:
            # Default logic: combination-key lookup (for hematological and treatment rules)
            return self._apply_combination_lookup(rule_json, input_values)

    def _apply_combination_lookup(self, rule_json, input_values):
        """
        Apply combination-key lookup logic with enhanced error handling for treatment rules.
        """
        rules = rule_json.get('rules', {})
        input_params = rule_json.get('input_parameters', [])
        rule_name = rule_json.get('rule_name', '')

        # Check if this is a treatment rule (needs special handling)
        is_treatment_rule = 'treatment' in rule_name.lower()

        # Create the combination key and track missing parameters
        param_values = []
        missing_params = []

        for param in input_params:
            value = input_values.get(param)
            if value is None or value == "Unknown":
                missing_params.append(param)
            param_values.append(str(value))

        combination_key = ",".join(param_values)

        # Look up the combination in the rules mapping
        if combination_key in rules:
            result = rules[combination_key]
            if isinstance(result, list):
                return "; ".join(result)
            return result

        # Enhanced error handling for treatment rules
        if is_treatment_rule:
            if missing_params:
                return f"Missing information of sub state: {', '.join(missing_params)}"
            else:
                return "No exact match to the protocol"

        # For non-treatment rules, return None as before
        #print(f"[Debug] No match found for combination: '{combination_key}'")
        #print(f"[Debug] Available keys: {list(rules.keys())}")
        return None

    def _apply_table_lookup(self, rule_json, input_values):
        """
        Simplified toxicity grading with only 2 scenarios:
        1. No relevant measurements → "No toxicity identified"
        2. Any relevant measurements → Apply maximal OR logic and return grade
        """
        lookup_table = rule_json.get('lookup_table', {})
        max_grade = 0
        max_grade_name = None

        grade_order = {"GRADE I": 1, "GRADE II": 2, "GRADE III": 3, "GRADE IV": 4}

        # Check if we have ANY relevant measurements
        has_any_relevant_measurement = False
        for param_name in lookup_table.get("GRADE I", {}).keys():
            input_value = input_values.get(param_name)
            if input_value is not None and input_value != "Unknown":
                has_any_relevant_measurement = True
                break

        # Scenario 1: No relevant measurements at all
        if not has_any_relevant_measurement:
            return "No toxicity identified"

        # Scenario 2: We have relevant measurements - apply maximal OR logic
        for grade_name, criteria in lookup_table.items():
            grade_num = grade_order.get(grade_name, 0)
            matches_grade = False

            # Check if ANY parameter matches this grade's criteria (OR logic)
            for param_name, allowed_values in criteria.items():
                input_value = input_values.get(param_name)
                if input_value is None or input_value == "Unknown":
                    continue  # Skip missing parameters

                # Check if input value matches any of the allowed values for this grade
                if input_value in allowed_values:
                    matches_grade = True
                    break  # Found a match for this grade

            # If this grade matches and is higher than current max, update
            if matches_grade and grade_num > max_grade:
                max_grade = grade_num
                max_grade_name = grade_name

        return max_grade_name if max_grade_name else "No toxicity identified"

    def _apply_combination_lookup(self, rule_json, input_values):
        """
        Apply combination-key lookup logic with custom messages for specific rules.
        """
        rules = rule_json.get('rules', {})
        input_params = rule_json.get('input_parameters', [])
        rule_name = rule_json.get('rule_name', '')

        # Check rule types
        is_treatment_rule = 'treatment' in rule_name.lower()
        is_hematological_rule = 'hematological' in rule_name.lower()

        # Create the combination key
        param_values = []
        for param in input_params:
            value = input_values.get(param)
            param_values.append(str(value))

        combination_key = ",".join(param_values)

        # Look up the combination in the rules mapping
        if combination_key in rules:
            result = rules[combination_key]
            if isinstance(result, list):
                return "; ".join(result)
            return result

        # Custom error handling based on rule type
        if is_treatment_rule:
            # Treatment rule logic (existing)
            systemic_toxicity = input_values.get('systemic_toxicity')
            hematological_state=input_values.get('hematological_state')
            if systemic_toxicity == "No toxicity identified" or hematological_state=="Due to partial information, the state cannot be determined":
                return "No exact match to the protocol"


        elif is_hematological_rule:
            # Custom message for hematological rule
            return "Due to partial information, the state cannot be determined"

        # For other rules, return None
        #print(f"[Debug] No match found for combination: '{combination_key}'")
        #print(f"[Debug] Available keys: {list(rules.keys())}")
        return None
    def process_patient_rules(self, patient_id, df):
        """
        Process all rules for a single patient with consistent key ordering.
        """
        # Initialize results with desired key order
        results = {
            "PatientId": patient_id,
            "hematological_state": "Unknown",  # Default, may be overwritten
            "systemic_toxicity": "Unknown",  # Default, may be overwritten
            "treatment_recommendations": "No exact match to the protocol"  # Default, may be overwritten
        }

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_time = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
        end_time = (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')

        # Process first-tier rules
        #print(f"[Debug] Processing first-tier rules for patient {patient_id}")
        for rule_path_info in self.rule_paths["first_tier"]:
            rule_json = self._load_rule(rule_path_info)
            if rule_json is None:
                continue

            param_list = self.get_param(rule_json)
            input_values = self.search_param(param_list, df, patient_id)
            classification = self.apply_rule(rule_json, input_values)

            if classification:
                rule_name = rule_json['rule_name']
                results[rule_name] = classification  # This overwrites the default
                #print(f"[Debug] First-tier result - {rule_name}: {classification}")

                # Add result to temporary DataFrame
                new_row = pd.DataFrame({
                    'PatientId': [patient_id],
                    'LOINC-Code': [rule_json['synthetic_loinc']],
                    'Concept Name': [rule_name],
                    'Value': [classification],
                    'StartDateTime': [pd.to_datetime(start_time)],
                    'EndDateTime': [pd.to_datetime(end_time)]
                })
                df = pd.concat([df, new_row], ignore_index=True)
                #print(f"[Debug] Added {rule_name} result to temporary DataFrame")
            else:
                print()

        # Process second-tier rules
        #print(f"[Debug] Processing second-tier rules for patient {patient_id}")
        for rule_path_info in self.rule_paths["second_tier"]:
            rule_json = self._load_rule(rule_path_info)
            if rule_json is None:
                continue

            param_list = self.get_param(rule_json)
            input_values = self.search_param(param_list, df, patient_id)
            classification = self.apply_rule(rule_json, input_values)

            rule_name = rule_json['rule_name']

            if classification:
                results[rule_name] = classification  # This overwrites the default
                #print(f"[Debug] Second-tier result - {rule_name}: {classification}")

                # Add to DataFrame
                new_row = pd.DataFrame({
                    'PatientId': [patient_id],
                    'LOINC-Code': [rule_json['synthetic_loinc']],
                    'Concept Name': [rule_name],
                    'Value': [classification],
                    'StartDateTime': [pd.to_datetime(start_time)],
                    'EndDateTime': [pd.to_datetime(end_time)]
                })
                df = pd.concat([df, new_row], ignore_index=True)
                #print(f"[Debug] Added {rule_name} result to temporary DataFrame")
            else:
                print()

        return results