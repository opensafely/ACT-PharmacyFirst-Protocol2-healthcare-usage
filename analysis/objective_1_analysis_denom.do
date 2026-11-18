/*==============================================================================
DO FILE NAME:			PF_WP2_obj1_Jul26
PROJECT:				Pharmacy First WP2
AUTHOR:					A Taylor							
DESCRIPTION OF FILE:	analysis for Objective 1
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
*log using "output/PF_WP2_P2_obj1_totals_denom.log", replace


*Load data for obj1 analysis, and save a copy dta
cd "$projectdir"
import delimited "output/dataset_patients_combined_denom_obj1.csv", clear

save "output/PF WP2 P2 obj1 dummy patient raw data updates denom_Nov26.dta", replace



preserve

contract inc_pt_all_eligible, freq(count) percent(percentage) nomiss
export delimited using "output/pf_cons_general_denom.csv", replace

restore


*Consultations are counted by identifying events with these codes and calculating the number of distinct consultation IDs. Multiple condition-specific PF codes recorded within the same consultation are counted as a single consultation.

tostring index_date, replace
**generate index_date_stata = date(index_date, "YMD")
generate index_date_stata = daily(index_date, "DMY")

*generate index_date_stata = date(index_date, "YMD")
format index_date_stata %td

*keep only post PF
keep if index_date_stata >= td(29feb2024)


gen index_date2 = index_date_stata
format index_date2 %tdmon_yy

gen age_group=""
replace age_group= "0_to_19" if age>=0 & age<=19 
replace age_group= "20_to_39" if age>=20 & age<=39 
replace age_group= "40_to_59" if age>=40 & age<=59 
replace age_group= "60_to_79" if age>=60 & age<=79 
replace age_group= "80_and_over" if age>=80

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


**********************************************************
***One-way comparison: total PF consultations by...
**********************************************************
*------------------------------------------------------------
* PF consultations by condition denominator
*------------------------------------------------------------
preserve

* Exclude the overall total variable from reshape
rename inc_pt_all_eligible total_pf_pts
gen long row_id = _n

*condition (row)
* Convert condition-specific variables from wide to long
reshape long inc_pt_, i(row_id) j(condition) string
rename inc_pt_ inc_pt

statsby sum=r(sum), by(condition) clear: summarize inc_pt
*collapse (sum) sum=num_pf_cons_all, by(condition)
export delimited using "output/oneway_date_condition_denom.csv",replace

restore


*------------------------------------------------------------
* Total PF consultations by date
*------------------------------------------------------------
preserve

*statsby sum=r(sum), by(index_date_stata) clear: summarize num_pf_cons_all
collapse (sum) sum=inc_pt_all_eligible, by(index_date_stata)
*format index_date_stata %tdDD/NN/CCYY
format index_date_stata %tdCCYY/NN/DD
gen date = string(index_date_stata, "%tdCCYY/NN/DD")
*gen date = string(index_date_stata, "%tdDD/NN/CCYY")
order date
export delimited using "output/oneway_date_denom.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by region
*------------------------------------------------------------
preserve

*statsby sum=r(sum), by(region) clear: summarize num_pf_cons_all
collapse (sum) sum=inc_pt_all_eligible, by(region)
export delimited using "output/oneway_region_denom.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by STP
*------------------------------------------------------------
preserve

*statsby sum=r(sum), by(stp) clear: summarize num_pf_cons_all
collapse (sum) sum=inc_pt_all_eligible, by(stp)
export delimited using "output/oneway_stp_denom.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by age group
*------------------------------------------------------------
preserve

*statsby sum=r(sum), by(age_group) clear: summarize num_pf_cons_all
collapse (sum) sum=inc_pt_all_eligible, by(age_group)
export delimited using "output/oneway_age_group_denom.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by sex
*------------------------------------------------------------
preserve

*statsby sum=r(sum), by(sex) clear: summarize num_pf_cons_all
collapse (sum) sum=inc_pt_all_eligible, by(sex)
export delimited using "output/oneway_sex_denom.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by ethnicity
*------------------------------------------------------------
preserve

*statsby sum=r(sum), by(ethnicity) clear: summarize num_pf_cons_all
collapse (sum) sum=inc_pt_all_eligible, by(ethnicity)
export delimited using "output/oneway_ethnicity_denom.csv", replace

restore


*------------------------------------------------------------
* Total PF consultations by IMD
*------------------------------------------------------------
preserve

*statsby sum=r(sum), by(imd) clear: summarize num_pf_cons_all
collapse (sum) sum=inc_pt_all_eligible, by(imd)
export delimited using "output/oneway_imd_denom.csv", replace

restore

*/

**********************************************************
***Two way comparisons : number of PF consultations by condition and by...
**********************************************************
preserve

gen long row_id = _n

* Includes num_pf_cons_all as condition = "all"
reshape long inc_pt_, i(row_id) j(condition) string
rename inc_pt_ num_pf_pts

* Save reshaped data temporarily
tempfile reshaped_denom
save `reshaped_denom'

restore


*------------------------------------------------------------
* Date × condition
*------------------------------------------------------------
use `reshaped_denom', clear
collapse (sum) sum=num_pf_pts, by(index_date_stata condition)
*statsby sum=r(sum), by(index_date_stata condition) clear: summarize num_pf_cons
reshape wide sum, i(index_date_stata) j(condition) string
*format index_date_stata %tdDD/NN/CCYY
format index_date_stata %tdCCYY-NN-DD
gen date = string(index_date_stata, "%tdCCYY/NN/DD")
*gen date = string(index_date_stata, "%tdDD/NN/CCYY")
order date
export delimited using "output/twoway_date_condition_denom.csv", replace


*------------------------------------------------------------
* Region × condition
*------------------------------------------------------------
use `reshaped_denom', clear
collapse (sum) sum=num_pf_pts, by(region condition)
*statsby sum=r(sum), by(region condition) clear: summarize num_pf_cons
reshape wide sum, i(region) j(condition) string
export delimited using "output/twoway_region_condition_denom.csv", replace


*------------------------------------------------------------
* STP × condition
*------------------------------------------------------------
use `reshaped_denom', clear
collapse (sum) sum=num_pf_pts, by(stp condition)
*statsby sum=r(sum), by(stp condition) clear: summarize num_pf_cons
reshape wide sum, i(stp) j(condition) string
export delimited using "output/twoway_stp_condition_denom.csv", replace


*------------------------------------------------------------
* Age group × condition
*------------------------------------------------------------
use `reshaped_denom', clear
collapse (sum) sum=num_pf_pts, by(age_group condition)
*statsby sum=r(sum), by(age_group condition) clear: summarize num_pf_cons
reshape wide sum, i(age_group) j(condition) string
export delimited using "output/twoway_age_group_condition_denom.csv", replace


*------------------------------------------------------------
* Sex × condition
*------------------------------------------------------------
use `reshaped_denom', clear
collapse (sum) sum=num_pf_pts, by(sex condition)
*statsby sum=r(sum), by(sex condition) clear: summarize num_pf_cons
reshape wide sum, i(sex) j(condition) string

export delimited using "output/twoway_sex_condition_denom.csv", replace


*------------------------------------------------------------
* Ethnicity × condition
*------------------------------------------------------------
use `reshaped_denom', clear
collapse (sum) sum=num_pf_pts, by(ethnicity condition)
*statsby sum=r(sum), by(ethnicity condition) clear: summarize num_pf_cons
reshape wide sum, i(ethnicity) j(condition) string

export delimited using "output/twoway_ethnicity_condition_denom.csv", replace


*------------------------------------------------------------
* IMD × condition
*------------------------------------------------------------
use `reshaped_denom', clear
collapse (sum) sum=num_pf_pts, by(imd condition)
*statsby sum=r(sum), by(imd condition) clear: summarize num_pf_cons
reshape wide sum, i(imd) j(condition) string

export delimited using "output/twoway_imd_condition_denom.csv", replace


**********************************************************
*** Three-way comparisons:Consultation counts by condition, date and subgroup
**********************************************************

*------------------------------------------------------------
* Condition × date × region
*------------------------------------------------------------
use `reshaped_denom', clear

*statsby sum=r(sum), by(condition index_date_stata region) clear: summarize num_pf_cons
collapse (sum) sum=num_pf_pts, by(condition index_date_stata region)
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
gen date = string(index_date_stata, "%tdCCYY/NN/DD")
*gen date = string(index_date_stata, "%tdDD/NN/CCYY")
order date
export delimited using "output/threeway_condition_date_region_denom.csv", replace


*------------------------------------------------------------
* Condition × date × STP
*------------------------------------------------------------
use `reshaped_denom', clear

*statsby sum=r(sum), by(condition index_date_stata stp) clear: summarize num_pf_cons
collapse (sum) sum=num_pf_pts, by(condition index_date_stata stp)
format index_date_stata %tdCCYY-NN-DD
reshape wide sum, i(stp index_date_stata) j(condition) string
gen date = string(index_date_stata, "%tdCCYY/NN/DD")
*gen date = string(index_date_stata, "%tdDD/NN/CCYY")
order date
export delimited using "output/threeway_condition_date_stp_denom.csv", replace


*------------------------------------------------------------
* Condition × date × age group
*------------------------------------------------------------
use `reshaped_denom', clear

*statsby sum=r(sum), by(condition index_date_stata age_group) clear: summarize num_pf_cons
collapse (sum) sum=num_pf_pts, by(condition index_date_stata age_group)
format index_date_stata %tdCCYY-NN-DD
*encode age_group, generate(age_group_num)
*drop age_group
reshape wide sum, i(age_group index_date_stata) j(condition) string
gen date = string(index_date_stata, "%tdCCYY/NN/DD")
*gen date = string(index_date_stata, "%tdDD/NN/CCYY")
order date
export delimited using "output/threeway_condition_date_age_group_denom.csv", replace

*------------------------------------------------------------
* Condition × date × sex
*------------------------------------------------------------
use `reshaped_denom', clear

*statsby sum=r(sum), by(condition index_date_stata sex) clear: summarize num_pf_cons
collapse (sum) sum=num_pf_pts, by(condition index_date_stata sex)
format index_date_stata %tdCCYY-NN-DD
reshape wide sum, i(sex index_date_stata) j(condition) string
gen date = string(index_date_stata, "%tdCCYY/NN/DD")
*gen date = string(index_date_stata, "%tdDD/NN/CCYY")
order date
export delimited using "output/threeway_condition_date_sex_denom.csv", replace


*------------------------------------------------------------
* Condition × date × ethnicity
*------------------------------------------------------------
use `reshaped_denom', clear

*statsby sum=r(sum), by(condition index_date_stata ethnicity) clear: summarize num_pf_cons
collapse (sum) sum=num_pf_pts, by(condition index_date_stata ethnicity)
format index_date_stata %tdCCYY-NN-DD
replace ethnicity = subinstr(ethnicity, " ", "_", .)
reshape wide sum, i(ethnicity index_date_stata) j(condition) string
gen date = string(index_date_stata, "%tdCCYY/NN/DD")
*gen date = string(index_date_stata, "%tdDD/NN/CCYY")
order date
export delimited using "output/threeway_condition_date_ethnicity_denom.csv", replace


*------------------------------------------------------------
* Condition × date × IMD
*------------------------------------------------------------
use `reshaped_denom', clear

*statsby sum=r(sum), by(condition index_date_stata imd) clear: summarize num_pf_cons
collapse (sum) sum=num_pf_pts, by(condition index_date_stata imd)
format index_date_stata %tdCCYY-NN-DD
replace imd="5" if imd== "5 (Least Deprived)"
reshape wide sum, i(imd index_date_stata) j(condition) string
gen date = string(index_date_stata, "%tdCCYY/NN/DD")
*gen date = string(index_date_stata, "%tdDD/NN/CCYY")
order date
export delimited using "output/threeway_condition_date_imd_denom.csv", replace


*log close

