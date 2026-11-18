/*==============================================================================
DO FILE NAME:			PF_WP2_obj1_Jul26
PROJECT:				Pharmacy First WP2
AUTHOR:					A Taylor							
DESCRIPTION OF FILE:	analysis for Objective 3
DATASETS USED:			output/pf_consultations_by_month.csv
OUTPUT: 		    	logfiles, printed to folder $Logdir
					
==============================================================================*/

*Set and display filepaths
global projectdir `c(pwd)'
di "$projectdir"

/*
capture mkdir "$projectdir/output/data"
capture mkdir "$projectdir/output/tables"
capture mkdir "$projectdir/output/figures"
*/

*Set and display log filepaths - logdir is set but not used
global logdir "$projectdir/logs"
di "$logdir"

*Close any log file
cap log close
*Open a log file
log using "output/PF_WP2_P2_obj3_totals.log", replace


*Load data for obj3 analysis, and save a copy dta
cd "$projectdir"
import delimited "output/dataset_patients_combined_obj3.csv", clear
*import delimited "output/dataset_patients_combined.csv", clear
save "output/PF WP2 P2 Obj3 dummy patient raw data updates Nov26.dta", replace

*generate index_date_stata = date(index_date, "YMD")
generate index_date_stata = date(index_date, "DMY")
format index_date_stata %td
*create variable for all PF conditions added together (consultation level)
gen num_PF_GP_cons_all=num_gp_cons_uti+num_gp_cons_sinusitis+num_gp_cons_ibite+num_gp_cons_otitismedia+num_gp_cons_sorethroat+num_gp_cons_shingles+num_gp_cons_impetigo+num_gp_cons_ibite_strict

preserve

contract num_PF_GP_cons_all, freq(count) percent(percentage) nomiss
export delimited using "output/pf_GP_cons_general obj3.csv", replace

restore

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

drop num_gp_cons_cellulitis_only num_gp_cons_ibite_strict_or_all num_gp_cons_ibite_all_plus_cellu num_gp_cons_ibite_strict_or_all_ num_gp_cons_ibite_all
set more off


*log using "output/PF_WP2_P2_obj1_totals.log", text replace

**********************************************************
***One-way comparison: total PF consultations by...
**********************************************************
*num_gp_cons_uti num_gp_cons_sinusitis num_gp_cons_ibite num_gp_cons_otitismedia num_gp_cons_sorethroat num_gp_cons_shingles num_gp_cons_impetigo num_gp_cons_ibite_strict num_gp_cons_lbp

*------------------------------------------------------------
* PF consultations by condition
*------------------------------------------------------------
preserve

* Exclude the overall total variable from reshape
rename num_PF_GP_cons_all total_gp_pf_cons
gen long row_id = _n

*condition (row)
* Convert condition-specific variables from wide to long
reshape long num_gp_cons_, i(row_id) j(condition) string
rename num_gp_cons_ num_gp_cons

statsby sum=r(sum), by(condition) clear: summarize num_gp_cons
*collapse (sum) sum=num_pf_cons_all, by(condition)
export delimited using "output/oneway_date_condition_obj3.csv",replace

restore

*------------------------------------------------------------
* Total PF consultations by date
*------------------------------------------------------------
preserve

*statsby sum=r(sum), by(index_date_stata) clear: summarize num_pf_cons_all
collapse (sum) sum=num_PF_GP_cons_all, by(index_date_stata)
format index_date_stata %tdDD/NN/CCYY
*format index_date_stata %tdCCYY/NN/DD
*gen date = string(index_date_stata, "%tdCCYY/NN/DD")
gen date = string(index_date_stata, "%tdDD/NN/CCYY")
order date
export delimited using "output/oneway_date_obj3.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by region
*------------------------------------------------------------
preserve

*statsby sum=r(sum), by(region) clear: summarize num_pf_cons_all
collapse (sum) sum=num_PF_GP_cons_all, by(region)
export delimited using "output/oneway_region_obj3.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by STP
*------------------------------------------------------------
preserve

*statsby sum=r(sum), by(stp) clear: summarize num_pf_cons_all
collapse (sum) sum=num_PF_GP_cons_all, by(stp)
export delimited using "output/oneway_stp.csv_obj3.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by age group
*------------------------------------------------------------
preserve

*statsby sum=r(sum), by(age_group) clear: summarize num_pf_cons_all
collapse (sum) sum=num_PF_GP_cons_all, by(age_group)
export delimited using "output/oneway_age_group_obj3.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by sex
*------------------------------------------------------------
preserve

*statsby sum=r(sum), by(sex) clear: summarize num_pf_cons_all
collapse (sum) sum=num_PF_GP_cons_all, by(sex)
export delimited using "output/oneway_sex_obj3.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by ethnicity
*------------------------------------------------------------
preserve

*statsby sum=r(sum), by(ethnicity) clear: summarize num_pf_cons_all
collapse (sum) sum=num_PF_GP_cons_all, by(ethnicity)
export delimited using "output/oneway_ethnicity_obj3.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by IMD
*------------------------------------------------------------
preserve

*statsby sum=r(sum), by(imd) clear: summarize num_pf_cons_all
collapse (sum) sum=num_PF_GP_cons_all, by(imd)
export delimited using "output/oneway_imd_obj3.csv", replace

restore



**********************************************************
***Two way comparisons : number of PF consultations by condition and by...
**********************************************************
preserve

gen long row_id = _n

* Includes num_pf_cons_all as condition = "all"
reshape long num_gp_cons_, i(row_id) j(condition) string
rename num_gp_cons_ num_gp_cons

* Save reshaped data temporarily
tempfile reshaped
save `reshaped'

restore


*------------------------------------------------------------
* Date × condition
*------------------------------------------------------------
use `reshaped', clear
collapse (sum) sum=num_PF_GP_cons_all, by(index_date_stata condition)
*statsby sum=r(sum), by(index_date_stata condition) clear: summarize num_pf_cons
reshape wide sum, i(index_date_stata) j(condition) string
format index_date_stata %tdDD/NN/CCYY
*format index_date_stata %tdCCYY/NN/DD
*gen date = string(index_date_stata, "%tdCCYY/NN/DD")
gen date = string(index_date_stata, "%tdDD/NN/CCYY")
order date
export delimited using "output/twoway_date_condition_obj3.csv", replace


*------------------------------------------------------------
* Region × condition
*------------------------------------------------------------
use `reshaped', clear
collapse (sum) sum=num_PF_GP_cons_all, by(region condition)
*statsby sum=r(sum), by(region condition) clear: summarize num_pf_cons
reshape wide sum, i(region) j(condition) string
export delimited using "output/twoway_region_condition_obj3.csv", replace


*------------------------------------------------------------
* STP × condition
*------------------------------------------------------------
use `reshaped', clear
collapse (sum) sum=num_PF_GP_cons_all, by(stp condition)
*statsby sum=r(sum), by(stp condition) clear: summarize num_pf_cons
reshape wide sum, i(stp) j(condition) string
export delimited using "output/twoway_stp_conditio_obj3n.csv", replace


*------------------------------------------------------------
* Age group × condition
*------------------------------------------------------------
use `reshaped', clear
collapse (sum) sum=num_PF_GP_cons_all, by(age_group condition)
*statsby sum=r(sum), by(age_group condition) clear: summarize num_pf_cons
reshape wide sum, i(age_group) j(condition) string
export delimited using "output/twoway_age_group_condition_obj3.csv", replace


*------------------------------------------------------------
* Sex × condition
*------------------------------------------------------------
use `reshaped', clear
collapse (sum) sum=num_PF_GP_cons_all, by(sex condition)
*statsby sum=r(sum), by(sex condition) clear: summarize num_pf_cons
reshape wide sum, i(sex) j(condition) string

export delimited using "output/twoway_sex_condition_obj3.csv", replace


*------------------------------------------------------------
* Ethnicity × condition
*------------------------------------------------------------
use `reshaped', clear
collapse (sum) sum=num_PF_GP_cons_all, by(ethnicity condition)
*statsby sum=r(sum), by(ethnicity condition) clear: summarize num_pf_cons
reshape wide sum, i(ethnicity) j(condition) string

export delimited using "output/twoway_ethnicity_condition_obj3.csv", replace


*------------------------------------------------------------
* IMD × condition
*------------------------------------------------------------
use `reshaped', clear
collapse (sum) sum=num_PF_GP_cons_all, by(imd condition)
*statsby sum=r(sum), by(imd condition) clear: summarize num_pf_cons
reshape wide sum, i(imd) j(condition) string

export delimited using "output/twoway_imd_condition_obj3.csv", replace


**********************************************************
*** Three-way comparisons:Consultation counts by condition, date and subgroup
**********************************************************

*------------------------------------------------------------
* Condition × date × region
*------------------------------------------------------------
use `reshaped', clear

*statsby sum=r(sum), by(condition index_date_stata region) clear: summarize num_pf_cons
collapse (sum) sum=num_PF_GP_cons_all, by(condition index_date_stata region)
format index_date_stata %tdCCYY-NN-DD

replace region="North_East" if region=="North East"
replace region="North_West" if region=="North West"
replace region="South _East" if region=="South East"
replace region="South _West" if region=="South West"
replace region="West_Midlands" if region=="West Midlands"
replace region="Yorkshire_and_The_Humber" if region=="Yorkshire and The Humber"
encode region, generate(region_num)
drop region
reshape wide sum, i(index_date_stata region_num) j(condition) string
*gen date = string(index_date_stata, "%tdCCYY/NN/DD")
gen date = string(index_date_stata, "%tdDD/NN/CCYY")
order date
export delimited using "output/threeway_condition_date_region_obj3.csv", replace


*------------------------------------------------------------
* Condition × date × STP
*------------------------------------------------------------
use `reshaped', clear

*statsby sum=r(sum), by(condition index_date_stata stp) clear: summarize num_pf_cons
collapse (sum) sum=num_PF_GP_cons_all, by(condition index_date_stata stp)
format index_date_stata %tdCCYY-NN-DD
reshape wide sum, i(stp index_date_stata) j(condition) string
*gen date = string(index_date_stata, "%tdCCYY/NN/DD")
gen date = string(index_date_stata, "%tdDD/NN/CCYY")
order date
export delimited using "output/threeway_condition_date_stp_obj3.csv", replace


*------------------------------------------------------------
* Condition × date × age group
*------------------------------------------------------------
use `reshaped', clear

*statsby sum=r(sum), by(condition index_date_stata age_group) clear: summarize num_pf_cons
collapse (sum) sum=num_PF_GP_cons_all, by(condition index_date_stata age_group)
format index_date_stata %tdCCYY-NN-DD
*encode age_group, generate(age_group_num)
*drop age_group
reshape wide sum, i(age_group index_date_stata) j(condition) string
*gen date = string(index_date_stata, "%tdCCYY/NN/DD")
gen date = string(index_date_stata, "%tdDD/NN/CCYY")
order date
export delimited using "output/threeway_condition_date_age_group_obj3.csv", replace

*------------------------------------------------------------
* Condition × date × sex
*------------------------------------------------------------
use `reshaped', clear

*statsby sum=r(sum), by(condition index_date_stata sex) clear: summarize num_pf_cons
collapse (sum) sum=num_PF_GP_cons_all, by(condition index_date_stata sex)
format index_date_stata %tdCCYY-NN-DD
reshape wide sum, i(sex index_date_stata) j(condition) string
*gen date = string(index_date_stata, "%tdCCYY/NN/DD")
gen date = string(index_date_stata, "%tdDD/NN/CCYY")
order date
export delimited using "output/threeway_condition_date_sex_obj3.csv", replace


*------------------------------------------------------------
* Condition × date × ethnicity
*------------------------------------------------------------
use `reshaped', clear

*statsby sum=r(sum), by(condition index_date_stata ethnicity) clear: summarize num_pf_cons
collapse (sum) sum=num_PF_GP_cons_all, by(condition index_date_stata ethnicity)
format index_date_stata %tdCCYY-NN-DD
replace ethnicity = subinstr(ethnicity, " ", "_", .)
reshape wide sum, i(ethnicity index_date_stata) j(condition) string
*gen date = string(index_date_stata, "%tdCCYY/NN/DD")
gen date = string(index_date_stata, "%tdDD/NN/CCYY")
order date
export delimited using "output/threeway_condition_date_ethnicity_obj3.csv", replace


*------------------------------------------------------------
* Condition × date × IMD
*------------------------------------------------------------
use `reshaped', clear

*statsby sum=r(sum), by(condition index_date_stata imd) clear: summarize num_pf_cons
collapse (sum) sum=num_PF_GP_cons_all, by(condition index_date_stata imd)
format index_date_stata %tdCCYY-NN-DD
replace imd="5" if imd== "5 (Least Deprived)"
reshape wide sum, i(imd index_date_stata) j(condition) string
*gen date = string(index_date_stata, "%tdCCYY/NN/DD")
gen date = string(index_date_stata, "%tdDD/NN/CCYY")
order date
export delimited using "output/threeway_condition_date_imd_obj3.csv", replace


*log close



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
