import pandas as pd
import numpy as np


def roth_ira_contribution(agi):
    """
    source: https://www.irs.gov/retirement-plans/plan-participant-employee/amount-of-roth-ira-contributions-that-you-can-make-for-2024
    Vectorized calculation of Roth IRA contribution based on AGI for a single filer for 2024.

    Parameters:
    agi (float or array-like): Adjusted Gross Income (can be a single value or an array)
    
    Returns:
    float or ndarray: Allowed Roth IRA contribution amount(s)
    """
    # Contribution limits for 2024
    max_contribution = 7000
    phase_out_start = 146000
    phase_out_end = 161000
    # Convert input to numpy array for vectorized operations
    agi = np.asarray(agi)
    # Calculate contribution using vectorized operations
    contribution = np.where(
        agi < phase_out_start,
        max_contribution,
        np.where(
            agi >= phase_out_end,
            0,
            max_contribution * (
                1 - (agi - phase_out_start) /
                (phase_out_end - phase_out_start)
                )
        )
    )
    return (contribution)

def trad_ira_contribution(agi):
    """
    Calculate the traditional IRA contribution based on adjusted gross income (AGI).

    This function determines the allowable traditional IRA contribution by subtracting 
    the Roth IRA contribution from the annual IRA contribution limit (assumed to be $7,000). 
    The absolute value ensures a non-negative result.

    Parameters:
    agi (float): Adjusted gross income (AGI) of the individual.

    Returns:
    float: The allowed contribution to a traditional IRA.
    """
    return np.abs(7000 - roth_ira_contribution(agi))

def calpers_contribution(agi):
    return 0.08 * agi

def calpers_benefit_factor(age, existing_service_credit=1):
    # https://www.calpers.ca.gov/docs/forms-publications/benefit-factors-state-misc-industrial-2-at-62.pdf
    benefit_factor = np.where(
        age >= 67, 0.025, np.where(
            age < 52, 0, (0.01 + (age - 52 + existing_service_credit)*0.001))
    )
    return benefit_factor

def calpers_pct_income(age, start_age):
    percent_of_inc = calpers_benefit_factor(age, start_age) * (age - start_age)
    return np.minimum(1, percent_of_inc)

def calpers_benefit(age, start_age, agi):
    max_inc = agi.combine_first(pd.Series(agi).rolling(3).mean())
    percent_of_inc = calpers_pct_income(age, start_age)
    return percent_of_inc * max_inc

def ira_growth(
    annual_income: pd.Series,
    stock_growth: pd.Series,
    periods: int,
    roth_balance: int = 26000,
    trad_balance: int = 0):
    roth_ira_balances = []
    trad_ira_balances = []
    for i in range(periods):
        roth_balance += roth_ira_contribution(annual_income[i])
        roth_ira_balances.append(roth_balance)
        roth_balance += roth_balance * stock_growth[i]

        trad_balance += trad_ira_contribution(annual_income[i])
        trad_ira_balances.append(trad_balance)
        trad_balance += trad_balance * stock_growth[i]
    return roth_ira_balances, trad_ira_balances