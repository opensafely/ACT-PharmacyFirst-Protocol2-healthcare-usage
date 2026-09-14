# This file defines the population and selects the fields that need to be included in the data for analysis. 
# Most code is the same as dataset_definition_patients.py, but with additional fields for the measures dataset AND date specified with INTERVAL.
# An important change is that the dataset population is defined as all patients rather than using the variables for alive, registered etc because the date should be specified with INTERVAL.
# To filter to general eligible population, we can use the variables for alive, registered etc in denominators in measures.


from ehrql import create_dataset, days, weeks, months, case, when, INTERVAL
from ehrql.tables.tpp import (patients, practice_registrations, clinical_events, addresses, 
                              ethnicity_from_sus)
import analysis.codelists as codelists

from analysis.pf_variable_library import (get_imd, get_latest_ethnicity, 
                                          select_events_between, select_events_from_codelist, select_events_by_consultation_id,
                                          has_event_count, select_events_within_days_of_dates)

dataset = create_dataset()
dataset.configure_dummy_data(population_size=500)

# One month time period (to start with this is Nov 25) 
start_date = INTERVAL.start_date    
index_date = INTERVAL.end_date

"""
Monthly patient-level denominator + numerator dataset
Patient table key fields:
- Patient identifiers: patient_id, month (start_date, index_date), registration_status, alive_status, 
- Demographics: age, sex, ethnicity, IMD
- Practice info: practice_id, STP, region
- PF service code validation variables and PF consultation count
- Eligibility/clinical characteristics flag (True/False)

Eligibility/clinical characteristics flag for study population denominator:
- include_patient_otitis_media
- include_patient_sinusitis
- include_patient_sore_throat
- include_patient_insect_bites
- include_patient_shingles
- include_patient_impetigo
- include_patient_uti
- include_patient_overall_eligible: at least one condition

The above variables require:
- pregnant_this_month: True/False, developed by Helen
- bullous_impetigo_this_month
- recurrent_impetigo_this_year
- catheter_status
- recurrent_uti

"""

########################################################
# Patient identifiers: alive_status, registration_status
alive = patients.is_alive_on(index_date) # alive at the end of month
alive_start = patients.is_alive_on(start_date) # alive at the start of month
# Only include the patient if they were registered for the whole month, 
# so registered before the month starts and not deregistered or died during the month
registered_start = practice_registrations.for_patient_on(start_date).exists_for_patient()
registered_index = practice_registrations.for_patient_on(index_date).exists_for_patient()

# Demographics: sex, age, patient_imd
sex = patients.sex
age = patients.age_on(index_date)

# Define population
age_valid = (patients.age_on(index_date) <= 120) # "Exclude any patients over 120 years old as the date of birth is most likely to be missing"
dataset.define_population(patients.exists_for_patient())

dataset.start_date = start_date
dataset.index_date = index_date
dataset.registered_start = registered_start
dataset.registered_index = registered_index
dataset.alive = alive
dataset.sex = sex
dataset.age = age

dataset.imd = get_imd(addresses, index_date)
dataset.ethnicity = get_latest_ethnicity(index_date,clinical_events,codelists.ethnicity_group16_codelist,ethnicity_from_sus,grouping=16,)
# Patient identifiers: practice_id, stp, region
dataset.practice = practice_registrations.for_patient_on(index_date).practice_pseudo_id
dataset.stp = practice_registrations.for_patient_on(index_date).practice_stp
# dataset.region = practice_registrations.for_patient_on(index_date).practice_nuts1_region_name
dataset.region = case(
    when(practice_registrations.for_patient_on(index_date).practice_nuts1_region_name.is_null()).then("Missing"),
    otherwise=practice_registrations.for_patient_on(index_date).practice_nuts1_region_name,
)
########################################################
'''
This section counts the number of PF consultations for each PF service code.

It outputs patient-month level counts for each service code, 
overlap between the minor illness and PF service codes, 
and counts of PF condition consultations recorded alongside each of the two main service codes.
'''

selected_events = select_events_between(clinical_events, start_date, index_date)

pf_cp_minorillness_events = select_events_from_codelist(
    selected_events,
    codelists.pf_consultation_events_dict["pf_consultation_cp_minorillness"]
)

pf_service_events = select_events_from_codelist(
    selected_events,
    codelists.pf_consultation_events_dict["pf_consultation_service"]
)

pf_cp_service_events = select_events_from_codelist(
    selected_events,
    codelists.pf_consultation_events_dict["pf_consultation_cp_service"]
)

# Patient-month counts of the PF minor illness code
dataset.num_minor_illness_events = pf_cp_minorillness_events.count_for_patient()
dataset.num_minor_illness_consultations = pf_cp_minorillness_events.consultation_id.count_distinct_for_patient()

# Patient-month counts of the PF service code
dataset.num_pf_service_events = pf_service_events.count_for_patient()
dataset.num_pf_service_consultations = pf_service_events.consultation_id.count_distinct_for_patient()

# Patient-month counts of the PF CP service code
dataset.num_pf_cp_service_events = pf_cp_service_events.count_for_patient()
dataset.num_pf_cp_service_consultations = pf_cp_service_events.consultation_id.count_distinct_for_patient()

# Consultations where both the PF minor illness code and PF service code are recorded within the same consultation ID
pf_cp_minorillness_ids = pf_cp_minorillness_events.consultation_id
pf_service_ids = pf_service_events.consultation_id
pf_minorillness_and_service_same_consultation_events = pf_cp_minorillness_events.where(
    pf_cp_minorillness_events.consultation_id.is_in(pf_service_ids)
)
dataset.num_minorillness_and_pf_service_same_consultations = (
    pf_minorillness_and_service_same_consultation_events.consultation_id.count_distinct_for_patient()
)

# Date-level overlap between the PF service code and the PF minor illness code.
#
# For each patient-month, we check whether events for one code occur within
# +/- 7 days of event dates for the other code. The anchor event dates are taken
# from events in the current month, and the matched events are searched in a
# wider window around the month to allow matches near month boundaries.
#
# Note: these are date-level overlap checks using event dates, but the outputs
# are still patient-month level variables.

selected_events_7day_window = select_events_between(
    clinical_events,
    start_date - days(7),
    index_date + days(7),
)

# -------------------------------------------------------------------------
# Minor illness events within +/- 7 days of PF service event dates
pf_cp_minorillness_events_7day_window = select_events_from_codelist(
    selected_events_7day_window,
    codelists.pf_consultation_events_dict["pf_consultation_cp_minorillness"],
)

pf_service_dates = pf_service_events.date
minorillness_within_7days_of_pf_service_events = select_events_within_days_of_dates(
    pf_cp_minorillness_events_7day_window,
    pf_service_dates,
    window_days=7,
)

dataset.num_minorillness_events_within_7days_of_pf_service_event = (
    minorillness_within_7days_of_pf_service_events.count_for_patient()
)

dataset.num_minorillness_consultations_within_7days_of_pf_service_event = (
    minorillness_within_7days_of_pf_service_events.consultation_id.count_distinct_for_patient()
)

# -------------------------------------------------------------------------
# PF service events within +/- 7 days of minor illness event dates
pf_service_events_7day_window = select_events_from_codelist(
    selected_events_7day_window,
    codelists.pf_consultation_events_dict["pf_consultation_service"],
)

pf_cp_minorillness_dates = pf_cp_minorillness_events.date
pf_service_within_7days_of_minorillness_events = select_events_within_days_of_dates(
    pf_service_events_7day_window,
    pf_cp_minorillness_dates,
    window_days=7,
)

dataset.num_pf_service_events_within_7days_of_minorillness_event = (
    pf_service_within_7days_of_minorillness_events.count_for_patient()
)

dataset.num_pf_service_consultations_within_7days_of_minorillness_event = (
    pf_service_within_7days_of_minorillness_events.consultation_id.count_distinct_for_patient()
)

# When the minor illness code is used, how many associated PF condition codes are recorded?
# When the PF service code is used, how many associated PF condition codes are recorded?
# Events belonging to consultations identified by each service code
selected_pf_cp_minorillness_id_events = select_events_by_consultation_id(
    selected_events,
    pf_cp_minorillness_ids,
)
selected_pf_service_id_events = select_events_by_consultation_id(
    selected_events,
    pf_service_ids,
)

pf_conditions_pf_codes = {
    "uti": codelists.uti_code,
    "sinusitis": codelists.sinusitis_code,
    "insectbite": codelists.insectbite_code,
    "otitismedia": codelists.otitismedia_code,
    "sorethroat": codelists.sorethroat_code,
    "shingles": codelists.shingles_code,
    "impetigo": codelists.impetigo_code,
}

for name, codes in pf_conditions_pf_codes.items():
    _, count_minorillness_pf_consultation, _ = has_event_count(
        selected_pf_cp_minorillness_id_events,
        codes,
    )
    setattr(dataset, f"minorillness_pf_consultation_{name}", count_minorillness_pf_consultation)

    _, count_pfservice_pf_consultation, _ = has_event_count(
        selected_pf_service_id_events,
        codes,
    )
    setattr(dataset, f"pfservice_pf_consultation_{name}", count_pfservice_pf_consultation)

# Count PF consultations using the combined general PF service code definition.
# This is the main PF consultation definition used in the analysis.

pf_consultation_events = select_events_from_codelist(
    selected_events, 
    codelists.pf_consultation_events_dict["pf_consultation_services_combined"]
)
# 'pf_ids' is a set of consultation ids where their clinical events have any of the three general PF codes
pf_ids = pf_consultation_events.consultation_id
selected_pf_id_events = select_events_by_consultation_id(selected_events, pf_ids)

dataset.pf_consultation_general = (
    pf_consultation_events.consultation_id.count_distinct_for_patient()
)

for name, codes in pf_conditions_pf_codes.items():
    _, count_pf_consultation, _ = has_event_count(
        selected_pf_id_events,
        codes,
    )
    setattr(dataset, f"numerator_pf_consultation_{name}", count_pf_consultation)

########################################################
"""
Clinical variables for eligible population denominator:
- pregnant_this_month
- bullous_impetigo_this_month
- recurrent_impetigo_this_year
- catheter_status
- recurrent_uti
"""

from analysis.pf_variable_library import check_code_in_time_window, check_recurrent_status
# -- pregnancy_status - naive version
# pregnant_this_month = check_code_in_time_window(index_date-months(1),index_date, clinical_events, codelists.gp_snomed_codelist_pregnancy)
# dataset.pregnant_this_month = pregnant_this_month
# -- pregancy_status developed by Helen
# look back for recent end-of-pregnancy codes -- assume no longer pregnant if in last 12 weeks
dataset.pregnancy_end_recent = clinical_events.where(
    clinical_events.snomedct_code.is_in(codelists.gp_snomed_codelist_end_pregnancy) &
    clinical_events.date.is_on_or_between(start_date - weeks(32), start_date - days(1))
    ).sort_by(clinical_events.date).last_for_patient().date
# look ahead 40 weeks for end-of-pregnancy codes
dataset.pregnancy_end = clinical_events.where(
    clinical_events.snomedct_code.is_in(codelists.gp_snomed_codelist_end_pregnancy) &
    clinical_events.date.is_on_or_between(start_date, start_date + weeks(40))
    ).sort_by(clinical_events.date).first_for_patient().date
# estimated date of delivery (EDD) - very recent or in future to estimate the known start of pregnancy
dataset.pregnancy_edd = clinical_events.where(
    clinical_events.date.is_on_or_between(start_date - weeks(2), start_date + weeks(34)) &
    clinical_events.snomedct_code.is_in(codelists.gp_snomed_codelist_pregnancy_edd)
    ).sort_by(clinical_events.date).first_for_patient().date
# recent "pregnant" codes - this is to be used where no delivery or EDD recorded
dataset.pregnancy_code = clinical_events.where(
    clinical_events.snomedct_code.is_in(codelists.gp_snomed_codelist_pregnancy) &
    clinical_events.date.is_on_or_between(start_date - weeks(12), start_date + weeks(4))
    ).sort_by(clinical_events.date).first_for_patient().date
# combine criteria to create a pregnancy status for the current month:
dataset.pregnant = case(
    # recent delivery -> not pregnant now:
    when(dataset.pregnancy_end_recent.is_on_or_after(start_date - weeks(12))).then("0-R"),
    # EDD in month or next 8 months, not preceeded by an end-of-pregnancy
    when(dataset.pregnancy_edd.is_not_null() 
        # check that the pregnancy linked to the EDD did not end very early,
        # i.e prior to the last 12 weeks which is already captured above
         & (dataset.pregnancy_end_recent.is_null() # no past delivery captured
            | ~dataset.pregnancy_end_recent.is_on_or_between(dataset.pregnancy_edd-weeks(28),dataset.pregnancy_edd+weeks(3))
            )).then("P-EDD"),
    # end of pregnancy in month or next 2 months - currently pregnant:
    when(dataset.pregnancy_end.is_on_or_before(start_date + weeks(12))).then("P-E"),
    # recent pregnancy code
    when(dataset.pregnancy_code.is_not_null()).then("P"),
    otherwise="0",)
# pregnant_this_month = dataset.pregnant.is_in(("P-E", "P-EDD", "P"))
# Age <= 11: pregnancy flags are considered too unreliable and are not counted as pregnant.
pregnant_this_month = (dataset.pregnant.is_in(("P-E", "P-EDD", "P")) & (age >= 12))
dataset.pregnant_this_month = pregnant_this_month

# Anchor date for impetigo exclusion
# anchor is the day before the monthly interval start
impetigo_exclusion_anchor_date = start_date

# bullous_impetigo in one month
# When start_date = 2025-10-01, impetigo_exclusion_anchor_date = 2025-10-01
# the lookback window is [2025-09-01, 2025-09-30]
# bullous_impetigo_this_month = check_code_in_time_window(start_date,index_date,clinical_events,codelists.gp_snomed_codelist_bullous_impetigo)
bullous_impetigo_last_month = check_code_in_time_window(
    impetigo_exclusion_anchor_date-months(1),
    impetigo_exclusion_anchor_date-days(1),
    clinical_events,
    codelists.gp_snomed_codelist_bullous_impetigo)
dataset.bullous_impetigo_last_month = bullous_impetigo_last_month

# recurrent_impetigo: (defined as 2 or more episodes in one year) 
# episodes are distinguished using 4 weeks gap, so any codes within 4 weeks are considered to be part of the same episode.
# For recurrent eligibility criteria, 
# we use the start of the study month as the anchor date and exclude the study month from the lookback window. 
# Therefore, criteria defined over N months are implemented as N-1 months before the anchor date, 
# ending on two weeks before the study month starts.
recurrent_impetigo_window_start = impetigo_exclusion_anchor_date - months(11)
recurrent_impetigo_window_end = impetigo_exclusion_anchor_date - days(15)
recurrent_impetigo_12m = check_recurrent_status(
    recurrent_impetigo_window_start, 
    recurrent_impetigo_window_end,
    clinical_events, 
    codelists.gp_snomed_codelist_impetigo,
    gap_weeks=4, 
    min_episodes=2)
dataset.recurrent_impetigo_12m = recurrent_impetigo_12m

# Anchor date for uti exclusion
# anchor is the day before the monthly interval start
uti_exclusion_anchor_date = start_date

# catheter_status: excluding patients who clearly have a catheter, and for following 12 months after code is included
catheter_12m = check_code_in_time_window(
    uti_exclusion_anchor_date - months(11),
    uti_exclusion_anchor_date - days(1),
    clinical_events,
    codelists.gp_snomed_codelist_urinary_catheter,
)
dataset.catheter_12m = catheter_12m

# recurrent_uti: (2 episodes in last 6 months, or 3 episodes in last 12 months) an episode is defined as a 4 week period, so any codes within this time are considered to be part of the same episode.
# To avoid counting consultations in the study month itself, 
# criteria defined over N months are implemented as N-1 months before the anchor date, 
# ending on one week before the study month starts.
recurrent_uti_6m_window_start = uti_exclusion_anchor_date - months(5)
recurrent_uti_12m_window_start = uti_exclusion_anchor_date - months(11)
recurrent_uti_window_end = uti_exclusion_anchor_date - days(8)
recurrent_uti_6m = check_recurrent_status(
    recurrent_uti_6m_window_start, 
    recurrent_uti_window_end,
    clinical_events, 
    codelists.gp_snomed_codelist_uti,
    gap_weeks=4, 
    min_episodes=2)
recurrent_uti_12m = check_recurrent_status(
    recurrent_uti_12m_window_start, 
    recurrent_uti_window_end,
    clinical_events, 
    codelists.gp_snomed_codelist_uti,
    gap_weeks=4, 
    min_episodes=3)
recurrent_uti = recurrent_uti_6m | recurrent_uti_12m
dataset.recurrent_uti_6m = recurrent_uti_6m
dataset.recurrent_uti_12m = recurrent_uti_12m
dataset.recurrent_uti = recurrent_uti

########################################################
"""
Eligibility/clinical characteristics flag for study population denominator:
- include_patient_otitis_media
- include_patient_sinusitis
- include_patient_sore_throat
- include_patient_insect_bites
- include_patient_shingles
- include_patient_impetigo
- include_patient_uti
- include_patient_overall_eligible
"""
female = patients.sex.is_in(["female"])

# Condition: acute otitis media
# - inclusion: children aged 1 to 17 years
# - exclusion: none
include_patient_otitis_media = (age >= 1) & (age <= 17) 
dataset.include_patient_otitis_media = include_patient_otitis_media

# Condition: acute sinusitis
# - inclusion: age >= 12
# - exclusion: none
include_patient_sinusitis = (age >= 12)
dataset.include_patient_sinusitis = include_patient_sinusitis

# Condition: acute sore throat
# - inclusion: age >= 5
# - exclusion: pregnant female under 16s
age_eligible_sore_throat = (age >= 5)
exclusion_sore_throat = pregnant_this_month & (age < 16) & (female)
include_patient_sore_throat = (age_eligible_sore_throat & ~exclusion_sore_throat)
dataset.include_patient_sore_throat = include_patient_sore_throat

# Condition: infected insect bites
# - inclusion: age >= 1
# - exclusion: pregnant female under 16s
age_eligible_insect_bites = (age >= 1)
exclusion_insect_bites = pregnant_this_month & (age < 16) & (female)
include_patient_insect_bites = (age_eligible_insect_bites & ~exclusion_insect_bites)
dataset.include_patient_insect_bites = include_patient_insect_bites

# Condition: shingles
# - inclusion: age >= 18
# - exclusion: pregnant female
age_eligible_shingles = (age >= 18)
exclusion_shingles = pregnant_this_month & (female)
include_patient_shingles = (age_eligible_shingles & ~exclusion_shingles)
dataset.include_patient_shingles = include_patient_shingles

# Condition: impetigo
# - inclusion: age >= 1
# - exclusion: 
# - - bullous impetigo, 
# - - recurrent impetigo (defined as 2 or more episodes in the same year), 
# - - pregnant female under 16 years
impetigo_age_eligible = (age >= 1)
impetigo_exclusion = (bullous_impetigo_last_month | recurrent_impetigo_12m | (pregnant_this_month & (age < 16) & female))
include_patient_impetigo = (impetigo_age_eligible & ~impetigo_exclusion)
dataset.include_patient_impetigo = include_patient_impetigo

# Condition: Uncomplicated UTI
# - inclusion: women aged 16 to 64 years
# - exclusion: 
# - - pregnant female
# - - urinary catheter
# - - recurrent UTI: 2 episodes in last 6 months, or 3 episodes in last 12 months
uuti_eligible = (age >= 16) & (age <= 64) & female
uuti_exclusion = (pregnant_this_month | catheter_12m | recurrent_uti)
include_patient_uuti = (uuti_eligible & ~uuti_exclusion)
dataset.include_patient_uuti = include_patient_uuti

# include_patient_overall_eligible
include_patient_overall_eligible = (include_patient_otitis_media|include_patient_sinusitis
                                  |include_patient_sore_throat|include_patient_insect_bites
                                  |include_patient_shingles|include_patient_impetigo|include_patient_uuti)
dataset.include_patient_overall_eligible = include_patient_overall_eligible
