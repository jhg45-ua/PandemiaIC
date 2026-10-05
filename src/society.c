#include "society.h"

float evaluate_social_impact(const PolicyConfig *policy, ReplicaMetrics *metrics) {
    // Social fatigue increases based on the degree of trade restriction
    metrics->accumulated_social_fatigue += (policy->trade_restriction * 0.01f);

    // The compliance factor decreases with accumulated fatigue (lower limit of 40%)
    float compliance = 1.0f - metrics->accumulated_social_fatigue;
    if (compliance < 0.40f) {
        compliance = 0.40f;
    }

    return compliance;
}