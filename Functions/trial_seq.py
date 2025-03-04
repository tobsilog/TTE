import pandas as pd

def prepare_data_for_tte(data, estimand_type):
    """
    Prepares observational data for Target Trial Emulation,
    considering the chosen estimand.

    Args:
        data: pandas DataFrame, your observational data
        estimand_type: str, either "PP" (Per-Protocol) or "ITT" (Intention-to-Treat)

    Returns:
        pandas DataFrame, prepared data (may need to add weights, etc.)
    """
    if estimand_type not in ["PP", "ITT"]:
        raise ValueError("Estimand type must be 'PP' or 'ITT'")

    # **Assumptions about your 'data' DataFrame (you'll need to adjust these):**
    # - Let's assume you have columns like:
    #   - 'participant_id': Unique identifier for each participant
    #   - 'treatment_received':  Indicates the treatment actually received (e.g., "New Method", "Old Method", "Switched", "Dropout")
    #   - 'treatment_intended':  Indicates the treatment initially intended or assigned (if you have this in your observational data - could be relevant for ITT)
    #   - 'protocol_adherence': Boolean or numerical measure of how well the participant followed the intended protocol (for PP)
    #   - 'time_points':  Column representing time (e.g., week, month)
    #   - 'outcome': Column representing the outcome measure (e.g., test score)
    #   - 'eligibility_criteria_met': Boolean indicating if the participant meets pre-defined eligibility (you might want to filter based on this initially)


    # **--- Common Initial Data Preparation (for both PP and ITT) ---**
    print("Performing initial data cleaning and preparation...")

    # Example: Filter based on eligibility criteria (if you have such a column)
    if 'eligibility_criteria_met' in data.columns:
        data = data[data['eligibility_criteria_met'] == True].copy() # Keep only eligible participants
        print(f"  Filtered data to {len(data)} participants meeting eligibility criteria.")
    else:
        print("  No 'eligibility_criteria_met' column found. Ensure eligibility is handled appropriately elsewhere if needed.")


    # **--- Per-Protocol (PP) Estimand Logic ---**
    if estimand_type == "PP":
        print("Preparing data for Per-Protocol estimand.")

        # **Define 'Per-Protocol Adherence' (YOU NEED TO CUSTOMIZE THIS)**
        # This is where you need to be very specific based on your data and research question.
        # What constitutes "adhering to the protocol" for each treatment group in your observational setting?

        def is_per_protocol_pp(row): # Function to determine PP for EACH ROW
            treatment = row['treatment_received'] # Or maybe 'treatment_intended' depending on your definition
            adherence_measure = row.get('protocol_adherence', None) # Try to get protocol adherence column, if it exists

            if treatment == "New Method": # Define PP for "New Method" group
                # Example: Assume 'protocol_adherence' is a score 0-10, higher is better. PP is score >= 8
                if adherence_measure is not None and adherence_measure >= 8:
                    return True
                # Example: Or, maybe PP for "New Method" means they *never* switched to "Old Method"
                elif row['treatment_received'] == "New Method": # Assuming 'treatment_received' stays "New Method" consistently
                    return True
                else:
                    return False

            elif treatment == "Old Method": # Define PP for "Old Method" group
                # Example: Similar adherence criteria for "Old Method" - maybe less strict
                if adherence_measure is not None and adherence_measure >= 6: # Different threshold for old method?
                    return True
                elif row['treatment_received'] == "Old Method": # Consistent "Old Method" use
                    return True
                else:
                    return False
            else: # For any other treatment category (e.g., "Switched", "Dropout") - NOT PP
                return False

        # Apply the PP definition to each row to create a 'is_per_protocol' column
        data['is_per_protocol'] = data.apply(is_per_protocol_pp, axis=1)

        # **Filter to include only Per-Protocol participants**
        data_pp = data[data['is_per_protocol'] == True].copy() # Keep only PP participants
        print(f"  Filtered data to {len(data_pp)} participants considered Per-Protocol.")
        return data_pp # Return the PP dataset


    # **--- Intention-to-Treat (ITT) Estimand Logic ---**
    elif estimand_type == "ITT":
        print("Preparing data for Intention-to-Treat estimand.")

        # **Handle "Intention-to-Treat Assignment" in Observational Data (YOU NEED TO CUSTOMIZE)**
        # In a true RCT, ITT is based on *random assignment*. In observational data, we need a proxy.
        # Options for observational ITT approximation:

        # Option 1: Use 'treatment_intended' if you have it (Best approximation in observational data if available)
        if 'treatment_intended' in data.columns:
            print("  Using 'treatment_intended' column as proxy for ITT assignment.")
            # In ITT, we analyze based on 'treatment_intended', regardless of what they actually received.
            # For data preparation, you might not need to *filter* here significantly for ITT,
            # but you will analyze groups based on 'treatment_intended' in later steps (MSM).
            data_itt = data.copy() #  Keep all eligible, analysis will be by 'treatment_intended'

        # Option 2: Use 'first_treatment_received' as a proxy (If 'treatment_intended' is not available, and you have time-series data)
        elif 'time_points' in data.columns:
            print("  Using 'first_treatment_received' (approximated from time series) as proxy for ITT assignment.")
            #  This is more complex, you'd need to:
            #  1. Sort data by participant and time.
            #  2. For each participant, find their treatment at the *earliest* time point.
            #  3. Create a new column 'itt_assignment_proxy' based on this first treatment.
            #  **Example (simplified - you might need to adjust based on time data structure):**
            data_sorted_time = data.sort_values(by=['participant_id', 'time_points']) # Ensure time order
            first_treatment = data_sorted_time.groupby('participant_id')['treatment_received'].first().reset_index()
            first_treatment.rename(columns={'treatment_received': 'itt_assignment_proxy'}, inplace=True)
            data_itt = pd.merge(data, first_treatment, on='participant_id', how='left') # Merge back
            print("    Created 'itt_assignment_proxy' column based on first observed treatment.")


        # Option 3: If you have no clear 'intended' or 'first' treatment,  ITT may be less directly applicable in data prep.
        # You might need to focus on analyzing *all eligible participants as a single group* initially
        # and then use MSM to adjust for confounding, while being mindful of the limitations of ITT in this context.
        else:
            print("  Warning: No 'treatment_intended' or 'time_points' column found to approximate ITT assignment.")
            print("  For ITT in this case, you might need to focus on analyzing all eligible participants and adjusting for confounding in later stages (MSM).")
            data_itt = data.copy() # Keep all eligible participants

        if 'data_itt' not in locals(): # In case Option 3 was used and no data_itt is created yet.
            data_itt = data.copy() # Default to using the original (eligibility-filtered) data for ITT if no specific ITT proxy was created above.

        return data_itt # Return the ITT dataset (or data prepared for ITT analysis)

    # If somehow estimand_type is neither PP nor ITT (shouldn't happen due to input validation)
    else:
        return data.copy() # Return original data as a fallback (though error should have been raised)


