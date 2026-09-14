from ehrql import create_measures, months
from analysis.validation_pf_code.dataset_definition_pf_code_validation import dataset

measures = create_measures()
measures.configure_disclosure_control(enabled=False)

measure_base_population = (
    dataset.alive
    & dataset.registered_start
    & dataset.registered_index
    & (dataset.age <= 120)
)

pf_code_usage_measures = {
    "minor_illness_events": dataset.num_minor_illness_events,
    "minor_illness_consultations": dataset.num_minor_illness_consultations,
    "pf_service_events": dataset.num_pf_service_events,
    "pf_service_consultations": dataset.num_pf_service_consultations,
    "pf_cp_service_events": dataset.num_pf_cp_service_events,
    "pf_cp_service_consultations": dataset.num_pf_cp_service_consultations,
    "minorillness_and_pf_service_same_consultations": (
        dataset.num_minorillness_and_pf_service_same_consultations
    ),
    "minorillness_events_within_7days_of_pf_service_event": (
        dataset.num_minorillness_events_within_7days_of_pf_service_event
    ),
    "minorillness_consultations_within_7days_of_pf_service_event": (
        dataset.num_minorillness_consultations_within_7days_of_pf_service_event
    ),
    "pf_service_events_within_7days_of_minorillness_event": (
        dataset.num_pf_service_events_within_7days_of_minorillness_event
    ),
    "pf_service_consultations_within_7days_of_minorillness_event": (
        dataset.num_pf_service_consultations_within_7days_of_minorillness_event
    ),
}

for name, numerator in pf_code_usage_measures.items():
    measures.define_measure(
        name=name,
        numerator=numerator,
        denominator=measure_base_population,
        intervals=months(48).starting_on("2022-02-01"),
    )

pf_conditions = [
    "uti",
    "sinusitis",
    "insectbite",
    "otitismedia",
    "sorethroat",
    "shingles",
    "impetigo",
]

for condition in pf_conditions:
    measures.define_measure(
        name=f"pf_consultation_{condition}",
        numerator=getattr(dataset, f"numerator_pf_consultation_{condition}"),
        denominator=measure_base_population,
        intervals=months(2).starting_on("2025-10-01"),
    )

    measures.define_measure(
        name=f"minorillness_pf_consultation_{condition}",
        numerator=getattr(dataset, f"minorillness_pf_consultation_{condition}"),
        denominator=measure_base_population,
        intervals=months(2).starting_on("2025-10-01"),
    )

    measures.define_measure(
        name=f"pfservice_pf_consultation_{condition}",
        numerator=getattr(dataset, f"pfservice_pf_consultation_{condition}"),
        denominator=measure_base_population,
        intervals=months(2).starting_on("2025-10-01"),
    )