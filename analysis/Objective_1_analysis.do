/*==============================================================================
DO FILE NAME:			PF_WP2_obj1_Jul26
PROJECT:				Pharmacy First WP2
AUTHOR:					A Taylor							
DESCRIPTION OF FILE:	analysis for Objective 1
DATASETS USED:			output/pf_consultations_by_month.csv
OUTPUT: 		    	logfiles, printed to folder $Logdir
					
==============================================================================*/

*Set filepaths
global projectdir `c(pwd)'
di "$projectdir"

/*
capture mkdir "$projectdir/output/data"
capture mkdir "$projectdir/output/tables"
capture mkdir "$projectdir/output/figures"
*/

global logdir "$projectdir/logs"
di "$logdir"

*Open a log file
cap log close
log using "output/PF_WP2_P2_obj1_totals.log", replace



cd "$projectdir"
import delimited "output/dataset_patients_combined_obj1.csv", clear
save "output/PF WP2 P2 dummy patient raw data updates Aug26.dta", replace


preserve

contract pf_cons_general, freq(count) percent(percentage) nomiss
export delimited using "pf_cons_general", replace

restore


*Consultations are counted by identifying events with these codes and calculating the number of distinct consultation IDs. Multiple condition-specific PF codes recorded within the same consultation are counted as a single consultation.



generate index_date_stata = date(index_date, "DMY")
format index_date_stata %td
*create variable for all PF conditions added together (consultation level)
gen num_pf_cons_all=num_pf_cons_uti +num_pf_cons_sinusitis +num_pf_cons_ibite +num_pf_cons_otitismedia +num_pf_cons_sorethroat +num_pf_cons_shingles +num_pf_cons_impetigo

gen index_date2 = index_date_stata
format index_date2 %tdmon_yy

gen age_group=""
replace age_group= "0 to 19" if age>=0 & age<=19 
replace age_group= "20 to 39" if age>=20 & age<=39 
replace age_group= "40 to 59" if age>=40 & age<=59 
replace age_group= "60 to 79" if age>=60 & age<=79 
replace age_group= "80 and over" if age>=80

set linesize 255


replace inc_pt_otitis_media="1" if inc_pt_otitis_media=="T"
replace inc_pt_otitis_media="0" if inc_pt_otitis_media=="F"

replace inc_pt_sinusitis="1" if inc_pt_sinusitis =="T"
replace inc_pt_sinusitis="0" if inc_pt_sinusitis =="F"

replace inc_pt_sore_throat="1" if inc_pt_sore_throat =="T"
replace inc_pt_sore_throat="0" if inc_pt_sore_throat =="F"

replace inc_pt_insect_bites="1" if inc_pt_insect_bites =="T"
replace inc_pt_insect_bites="0" if inc_pt_insect_bites =="F"

replace inc_pt_shingles="1" if inc_pt_shingles =="T"
replace inc_pt_shingles="0" if inc_pt_shingles =="F"

replace inc_pt_impetigo="1" if inc_pt_impetigo =="T"
replace inc_pt_impetigo="0" if inc_pt_impetigo =="F"

replace inc_pt_uuti="1" if inc_pt_uuti =="T"
replace inc_pt_uuti="0" if inc_pt_uuti =="F"

replace inc_pt_all_eligible="1" if inc_pt_all_eligible =="T"
replace inc_pt_all_eligible="0" if inc_pt_all_eligible =="F"

destring inc_pt_otitis_media inc_pt_sinusitis inc_pt_sore_throat inc_pt_insect_bites inc_pt_shingles inc_pt_impetigo inc_pt_uuti inc_pt_all_eligible, replace    


set more off


*log using "output/PF_WP2_P2_obj1_totals.log", text replace

**********************************************************
***One-way comparison: total PF consultations by...
**********************************************************
*------------------------------------------------------------
* PF consultations by condition
*------------------------------------------------------------
preserve

* Exclude the overall total variable from reshape
rename pf_cons_general total_pf_cons
gen long row_id = _n

*condition (row)
* Convert condition-specific variables from wide to long
reshape long num_pf_cons_, i(row_id) j(condition) string
rename num_pf_cons_ num_pf_cons

statsby sum=r(sum), by(condition) clear: summarize num_pf_cons

export delimited using "oneway_date_condition.csv",replace

restore


*------------------------------------------------------------
* Total PF consultations by date
*------------------------------------------------------------
preserve

statsby sum=r(sum), by(index_date_stata) clear: summarize num_pf_cons_all

format index_date_stata %tdDD/NN/CCYY
export delimited using "oneway_date.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by region
*------------------------------------------------------------
preserve

statsby sum=r(sum), by(region) clear: summarize num_pf_cons_all

export delimited using "oneway_region.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by STP
*------------------------------------------------------------
preserve

statsby sum=r(sum), by(stp) clear: summarize num_pf_cons_all

export delimited using "oneway_stp.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by age group
*------------------------------------------------------------
preserve

statsby sum=r(sum), by(age_group) clear: summarize num_pf_cons_all

export delimited using "oneway_age_group.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by sex
*------------------------------------------------------------
preserve

statsby sum=r(sum), by(sex) clear: summarize num_pf_cons_all

export delimited using "oneway_sex.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by ethnicity
*------------------------------------------------------------
preserve

statsby sum=r(sum), by(ethnicity) clear: summarize num_pf_cons_all

export delimited using "oneway_ethnicity.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by IMD
*------------------------------------------------------------
preserve

statsby sum=r(sum), by(imd) clear: summarize num_pf_cons_all

export delimited using "oneway_imd.csv", replace

restore


**********************************************************
***Two way comparisons : number of PF consultations by condition and by...
**********************************************************
preserve

gen long row_id = _n

* Includes num_pf_cons_all as condition = "all"
reshape long num_pf_cons_, i(row_id) j(condition) string
rename num_pf_cons_ num_pf_cons

* Save reshaped data temporarily
tempfile reshaped
save `reshaped'

restore


*------------------------------------------------------------
* Date × condition
*------------------------------------------------------------
use `reshaped', clear
statsby sum=r(sum), by(index_date_stata condition) clear: summarize num_pf_cons
reshape wide sum, i(index_date_stata) j(condition) string
format index_date_stata %tdCCYY-NN-DD
export delimited using "twoway_date_condition.csv", replace





*------------------------------------------------------------
* Region × condition
*------------------------------------------------------------
use `reshaped', clear
statsby sum=r(sum), by(region condition) clear: summarize num_pf_cons
reshape wide sum, i(region) j(condition) string
export delimited using "twoway_region_condition.csv", replace


*------------------------------------------------------------
* STP × condition
*------------------------------------------------------------
use `reshaped', clear
statsby sum=r(sum), by(stp condition) clear: summarize num_pf_cons
reshape wide sum, i(stp) j(condition) string
export delimited using "twoway_stp_condition.csv", replace


*------------------------------------------------------------
* Age group × condition
*------------------------------------------------------------
use `reshaped', clear
statsby sum=r(sum), by(age_group condition) clear: summarize num_pf_cons
reshape wide sum, i(age_group) j(condition) string
export delimited using "twoway_age_group_condition.csv", replace


*------------------------------------------------------------
* Sex × condition
*------------------------------------------------------------
use `reshaped', clear
statsby sum=r(sum), by(sex condition) clear: summarize num_pf_cons
reshape wide sum, i(sex) j(condition) string

export delimited using "twoway_sex_condition.csv", replace


*------------------------------------------------------------
* Ethnicity × condition
*------------------------------------------------------------
use `reshaped', clear
statsby sum=r(sum), by(ethnicity condition) clear: summarize num_pf_cons
reshape wide sum, i(ethnicity) j(condition) string

export delimited using "twoway_ethnicity_condition.csv", replace


*------------------------------------------------------------
* IMD × condition
*------------------------------------------------------------
use `reshaped', clear
statsby sum=r(sum), by(imd condition) clear: summarize num_pf_cons
reshape wide sum, i(imd) j(condition) string

export delimited using "twoway_imd_condition.csv", replace


**********************************************************
*** Three-way comparisons:Consultation counts by condition, date and subgroup
**********************************************************

*------------------------------------------------------------
* Condition × date × region
*------------------------------------------------------------
use `reshaped', clear

statsby sum=r(sum), ///
    by(condition index_date_stata region) clear: ///
    summarize num_pf_cons

format index_date_stata %tdCCYY-NN-DD
reshape wide sum, i(condition index_date_stata) j(region) string
export delimited using "threeway_condition_date_region.csv", replace


*------------------------------------------------------------
* Condition × date × STP
*------------------------------------------------------------
use `reshaped', clear

statsby sum=r(sum), ///
    by(condition index_date_stata stp) clear: ///
    summarize num_pf_cons

format index_date_stata %tdCCYY-NN-DD
reshape wide sum, i(stp index_date_stata) j(condition) string
export delimited using "threeway_condition_date_stp.csv", replace


*------------------------------------------------------------
* Condition × date × age group
*------------------------------------------------------------
use `reshaped', clear

statsby sum=r(sum), ///
    by(condition index_date_stata age_group) clear: ///
    summarize num_pf_cons

format index_date_stata %tdCCYY-NN-DD
reshape wide sum, i(condition index_date_stata) j(age_group) string
export delimited using "threeway_condition_date_age_group.csv", replace


*------------------------------------------------------------
* Condition × date × sex
*------------------------------------------------------------
use `reshaped', clear

statsby sum=r(sum), ///
    by(condition index_date_stata sex) clear: ///
    summarize num_pf_cons

format index_date_stata %tdCCYY-NN-DD
reshape wide sum, i(condition index_date_stata) j(sex) string
export delimited using "threeway_condition_date_sex.csv", replace


*------------------------------------------------------------
* Condition × date × ethnicity
*------------------------------------------------------------
use `reshaped', clear

statsby sum=r(sum), ///
    by(condition index_date_stata ethnicity) clear: ///
    summarize num_pf_cons

format index_date_stata %tdCCYY-NN-DD
reshape wide sum, i(condition index_date_stata) j(ethnicity) string
export delimited using "threeway_condition_date_ethnicity.csv", replace


*------------------------------------------------------------
* Condition × date × IMD
*------------------------------------------------------------
use `reshaped', clear

statsby sum=r(sum), ///
    by(condition index_date_stata imd) clear: ///
    summarize num_pf_cons

format index_date_stata %tdCCYY-NN-DD
reshape wide sum, i(condition index_date_stata) j(imd) string
export delimited using "threeway_condition_date_imd.csv", replace


log close


/*
**************************************************
* Close totals log and open rates log
**************************************************
capture log close


log using "output/PF_WP2_P2_obj1_rates.log", replace


****************************************
****************************************
****************************************
*Calculating rates by practice and patient characteristics

* Variables that need to be summed before calculating rates
local collapse_vars ///
    num_pf_cons_uti ///
    num_pf_cons_sinusitis ///
    num_pf_cons_ibite ///
    num_pf_cons_otitismedia ///
    num_pf_cons_sorethroat ///
    num_pf_cons_shingles ///
    num_pf_cons_impetigo ///
    inc_pt_otitis_media ///
    inc_pt_sinusitis ///
    inc_pt_sore_throat ///
    inc_pt_insect_bites ///
    inc_pt_shingles ///
    inc_pt_impetigo ///
    inc_pt_uuti


* Run the same analysis for each subgroup
foreach subgroup in region stp age_group sex ethnicity imd {

    preserve

    * Obtain totals for each practice, month and subgroup
    collapse (sum) `collapse_vars', ///
        by(index_date_stata practice `subgroup')

    * Rates per 100 eligible patients
    gen rate_pf_cons_uti = ///
        100 * num_pf_cons_uti / inc_pt_uuti ///
        if inc_pt_uuti > 0

    gen rate_pf_cons_sinusitis = ///
        100 * num_pf_cons_sinusitis / inc_pt_sinusitis ///
        if inc_pt_sinusitis > 0

    gen rate_pf_cons_ibite = ///
        100 * num_pf_cons_ibite / inc_pt_insect_bites ///
        if inc_pt_insect_bites > 0

    gen rate_pf_cons_otitismedia = ///
        100 * num_pf_cons_otitismedia / inc_pt_otitis_media ///
        if inc_pt_otitis_media > 0

    gen rate_pf_cons_sorethroat = ///
        100 * num_pf_cons_sorethroat / inc_pt_sore_throat ///
        if inc_pt_sore_throat > 0

    gen rate_pf_cons_shingles = ///
        100 * num_pf_cons_shingles / inc_pt_shingles ///
        if inc_pt_shingles > 0

    gen rate_pf_cons_impetigo = ///
        100 * num_pf_cons_impetigo / inc_pt_impetigo ///
        if inc_pt_impetigo > 0

    * Convert condition-specific rates to long format
    gen long rate_row_id = _n

    reshape long rate_pf_cons_, ///
        i(rate_row_id) j(condition) string

    rename rate_pf_cons_ rate_pf_cons

    * Mean practice-level rate by condition, date and subgroup
    table condition index_date_stata `subgroup', ///
        contents(mean rate_pf_cons)

    restore
}

log close 
*/