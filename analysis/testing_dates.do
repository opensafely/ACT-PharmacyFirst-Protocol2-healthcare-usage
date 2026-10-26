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



cd "$projectdir"
import delimited "output/dataset_patients_combined_obj1.csv", clear
save "output/PF WP2 P2 dummy patient raw data updates Aug26.dta", replace



*Consultations are counted by identifying events with these codes and calculating the number of distinct consultation IDs. Multiple condition-specific PF codes recorded within the same consultation are counted as a single consultation.

/*tostring index_date, replace
generate index_date_stata = date(index_date, "YMD")
**generate index_date_stata = daily(index_date, "DMY")

*generate index_date_stata = date(index_date, "YMD")
format index_date_stata %td
*create variable for all PF conditions added together (consultation level)
gen num_pf_cons_all=num_pf_cons_uti +num_pf_cons_sinusitis +num_pf_cons_ibite +num_pf_cons_otitismedia +num_pf_cons_sorethroat +num_pf_cons_shingles +num_pf_cons_impetigo

gen index_date2 = index_date_stata
format index_date2 %tdmon_yy

keep index_date
export delimited using "output/oneway_test_date.csv",replace
*/