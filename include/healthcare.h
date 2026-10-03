#ifndef HEALTHCARE_H
#define HEALTHCARE_H

#include "policy.h"
#include "simulator.h"

// Evaluates UCI occupancy, clinical costs and escess mortality rate due to system collapse
float evaluate_healthcare_system(const Grid *grid, const PolicyConfig *policy, PolicyMetrics *metrics);

#endif // HEALTHCARE_H