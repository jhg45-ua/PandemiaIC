#ifndef SOCIETY_H
#define SOCIETY_H

#include "policy.h"

// Updates accumulated social fatigue and returns the citizen compliance factor
float evaluate_social_impact(const PolicyConfig *policy, PolicyMetrics *metrics);

#endif // SOCIETY_H