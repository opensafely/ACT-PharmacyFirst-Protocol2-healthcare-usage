
/*
This script tests whether Stata can successfully import the Objective 1
numerator and denominator datasets.

It reports basic dataset information and memory usage.
*/

clear all
set more off
set linesize 255

capture log close
log using "output/test_stata_import.log", text replace


* =============================================================================
* Test numerator dataset
* =============================================================================

display "Testing numerator dataset"

import delimited using ///
    "output/dataset_patients_obj1_numerator.csv", clear

display "Numerator import successful"

* Dataset dimensions and size
describe, short

* Memory usage
memory

* Basic descriptive statistics
summarize age pf_cons_general

* Check encoded variable types
describe region stp sex ethnicity imd


* Release memory before importing the denominator dataset
clear


* =============================================================================
* Test denominator dataset
* =============================================================================

display "Testing denominator dataset"

import delimited using ///
    "output/dataset_patients_obj1_denominator.csv", clear

display "Denominator import successful"

* Dataset dimensions and size
describe, short

* Memory usage
memory

* Basic descriptive statistics
summarize age

* Check encoded variable types
describe region stp sex ethnicity imd


clear

display "Both import tests completed successfully"

log close
