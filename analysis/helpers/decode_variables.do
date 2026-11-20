
/*
Decode categorical variables using the shared mapping CSV.

Run after aggregation and immediately before exporting results.
*/

local mapping_file "analysis/helpers/categorical_mapping.csv"

* Create a temporary frame for the mapping data
local original_frame `c(frame)'
tempname mapping_frame

frame create `mapping_frame'
frame change `mapping_frame'

import delimited using "`mapping_file'", clear stringcols(1 2)

* Validate the mapping
confirm numeric variable encoded_value
assert !missing(encoded_value)

isid variable encoded_value
isid variable original_value

levelsof variable, local(variables) clean
local n = _N

* Store mappings in local macros
forvalues i = 1/`n' {
    local var`i' = variable[`i']
    local code`i' = encoded_value[`i']
    local text`i' = original_value[`i']
}

* Return to the analysis dataset
frame change `original_frame'
frame drop `mapping_frame'

* Decode categorical variables
foreach var of local variables {

    * Skip variables not present in the current dataset
    capture confirm variable `var', exact

    if _rc {
        continue
    }

    confirm numeric variable `var'

    tempvar decoded
    quietly generate strL `decoded' = ""

    forvalues i = 1/`n' {

        if "`var`i''" == "`var'" {

            quietly replace `decoded' = `"`text`i''"' ///
                if `var' == `code`i''
        }
    }

    * Check for unmapped non-missing values
    quietly count if !missing(`var') & missing(`decoded')

    if r(N) > 0 {
        display as error "Unmapped numerical codes found in `var'."
        drop `decoded'
        exit 459
    }

    * Retain the original column position and name
    order `decoded', before(`var')
    drop `var'
    rename `decoded' `var'
}
