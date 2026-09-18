from ehrql import create_measures, months, years
from analysis.dataset_definition_patients_measures import dataset
# opensafely exec ehrql:v1 generate-measures analysis/practice_variables/measures_practice.py --output output/measures_practice.csv

from ehrql import claim_permissions
claim_permissions("appointments")

# Create measures object
measures = create_measures()
measures.configure_disclosure_control(enabled=False)
measures.define_defaults(
    # intervals=months(2).starting_on("2025-10-01"),
    # intervals=years(2).starting_on("2024-02-01")
    intervals=months(48).starting_on("2022-02-01"),
)

measure_base_population = (
    dataset.alive
    & dataset.registered_start
    & dataset.registered_index
    & (dataset.age <= 120)
)

pf_eligible_population = (
    dataset.include_patient_overall_eligible
    & measure_base_population
)

group = {
    "practice": dataset.practice,
    "stp": dataset.stp,
    "region": dataset.region,
}

# appointments
measures.define_measure(
    name="appointments_scheduled",
    numerator=dataset.appointment_scheduled,
    denominator=measure_base_population,
    group_by=group,
)

measures.define_measure(
    name="appointments_seen",
    numerator=dataset.appointment_seen,
    denominator=measure_base_population,
    group_by=group,
)

# # PF consultations for testing purpose
# measures.define_measure(
#     name="pf_consultation_general",
#     numerator=dataset.pf_consultation_general,
#     denominator=pf_eligible_population,
#     group_by=group,
# )

# measures.define_measure(
#     name="pf_consultation_uti",
#     numerator=dataset.numerator_pf_consultation_uti,
#     denominator=measure_base_population & dataset.include_patient_uuti,
#     group_by=group,
# )

eligibility_variables = {
    "inc_pt_otitis_media": dataset.include_patient_otitis_media,
    "inc_pt_sinusitis": dataset.include_patient_sinusitis,
    "inc_pt_sore_throat": dataset.include_patient_sore_throat,
    "inc_pt_insect_bites": dataset.include_patient_insect_bites,
    "inc_pt_shingles": dataset.include_patient_shingles,
    "inc_pt_impetigo": dataset.include_patient_impetigo,
    "inc_pt_uuti": dataset.include_patient_uuti,
    "inc_pt_all_eligible": dataset.include_patient_overall_eligible,
}

for name, eligibility_variable in eligibility_variables.items():
    measures.define_measure(
        name=name,
        numerator=eligibility_variable,
        denominator=measure_base_population,
        group_by=group,
    )