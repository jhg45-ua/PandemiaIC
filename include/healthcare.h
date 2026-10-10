#ifndef HEALTHCARE_H
#define HEALTHCARE_H

#include "policy.h"

// Evaluates ICU occupancy, clinical costs and excess mortality rate due to system collapse
float evaluate_healthcare_impact(int num_I, int total_population, ReplicaMetrics *metrics);

#endif // HEALTHCARE_H