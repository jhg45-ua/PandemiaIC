#ifndef ECONOMY_H
#define ECONOMY_H

#include "policy.h"

// Evaluates costs associated with sick leave, business closures, and tax subsidies
void evaluate_economic_impact(int num_I, int total_population, const PolicyConfig *policy, ReplicaMetrics *metrics);

#endif // ECONOMY_H