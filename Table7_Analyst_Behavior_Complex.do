* ==============================================================================
* 进一步分析终极版：高业务复杂度下的分析师"认知挣扎与深度追问"
* ==============================================================================
eststo clear

* 确认控制变量宏 (以你之前的设定为准)
global controls "Size Lev ROA Board Indep CashFlow HHI Dual Big4 SA指数_abs"

* ------------------------------------------------------------------------------
* (1) 行为发生频率：调研次数 (ln_VisitCount)
* ------------------------------------------------------------------------------
eststo Final_Vis: quietly reghdfe ln_VisitCount did $controls if High_Complexity == 1, absorb(id year) vce(cluster id)
estadd local firm_fe "YES" : Final_Vis
estadd local year_fe "YES" : Final_Vis

* ------------------------------------------------------------------------------
* (2) 认知挣扎强度：提问数量 (ln_TotalQues) -> 核心显著指标！！！
* ------------------------------------------------------------------------------
eststo Final_Ques: quietly reghdfe ln_TotalQues did $controls if High_Complexity == 1, absorb(id year) vce(cluster id)
estadd local firm_fe "YES" : Final_Ques
estadd local year_fe "YES" : Final_Ques

* ------------------------------------------------------------------------------
* (3) 描述性努力：提问字数 (ln_TotalWords)
* ------------------------------------------------------------------------------
eststo Final_Words: quietly reghdfe ln_TotalWords did $controls if High_Complexity == 1, absorb(id year) vce(cluster id)
estadd local firm_fe "YES" : Final_Words
estadd local year_fe "YES" : Final_Words

* ==============================================================================
* 输出完美的 Word (.rtf) 表格
* ==============================================================================
esttab Final_Vis Final_Ques Final_Words using "Table7_Analyst_Behavior_Complex.rtf", replace ///
    b(%9.3f) t(%9.2f) star(* 0.10 ** 0.05 *** 0.01) ///
    mtitle("ln调研频次" "ln提问数量" "ln提问字数") ///
    order(did $controls) ///
    scalars("firm_fe Firm FE" "year_fe Year FE" "N Observations" "r2_a Adj-R2") ///
    compress nogap label ///
    title("Table 7: Further Analysis - Analyst Information Acquisition under High Cognitive Load") ///
    addnotes("Note: The sample is restricted to firms with high business complexity. Standard errors clustered at the firm level are reported in parentheses.")
