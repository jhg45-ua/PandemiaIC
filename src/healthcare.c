#include <stdio.h>
#include <math.h>
#include "healthcare.h"

float evaluate_health_impact(int num_I, int total_population, PolicyMetrics *metrics) {
    // 5% of active cases require ICU care and 15% require a general hospital bed
    int icu_demand = (int)ceilf(num_I * 0.05f);
    int general_beds = (int)ceilf(num_I * 0.15f);

    // Installed ICU capacity (0.5% of the total population)
    int icu_capacity = (int)(total_population * 0.005f);
    if (icu_capacity < 1) icu_capacity = 1;

    float excess_mortality_factor = 1.0f;

    // If demand exceeds capacity, a collapse is recorded and excess mortality is scaled
    if (icu_demand > icu_capacity) {
        int excess = icu_demand - icu_capacity;
        metrics->icu_overcrowding_days++;
        excess_mortality_factor += ((float)excess / (float)icu_capacity);
    }

    // Daily healthcare cost (€1,200/day per ICU bed and €400/day per general ward bed)
    double daily_cost = (icu_demand * 1200.0) + (general_beds * 400.0);
    metrics->total_economic_cost += daily_cost;

    return excess_mortality_factor;
}