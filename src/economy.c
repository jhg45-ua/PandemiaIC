#include "economy.h"

void evaluate_economic_impact(int num_I, int total_population, const PolicyConfig *policy, PolicyMetrics *metrics) {
    // 1. Productivity loss due to sick leave (120 €/day per active case)
    double sick_leave_cost = (double)num_I * 120.0;

    // 2. Commercial impact (daily nominal GDP base = 100 €/person/day)
    double daily_GDP_base = (double)total_population * 100.0;
    double cost_of_restrictions = daily_GDP_base * (double)policy->trade_restriction;

    // 3. Government subsidy spending
    double subsidy_cost = policy->daily_subsidy_expense;

    // Add losses to the scenario’s total cost
    metrics->total_economic_cost += (sick_leave_cost + cost_of_restrictions + subsidy_cost);
}