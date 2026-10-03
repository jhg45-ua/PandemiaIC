#ifndef POLICY_H
#define POLICY_H

// Epidemiologic states
#define SUSCEPTIBLE 0
#define INFECTED 1
#define RECOVERED 2
#define DEAD 3

// Standard medical parameters for the virus
#define RECOVERY_DAYS 10
#define BASE_DEATH_RATE 0.02f   // 2% mortality on normal conditions

// Policy/scenario parameters
typedef struct {
    char name[32];
    float beta;                     // Base transmission rate per contact
    float trade_restriction;        // Proportion of the economy at a halt (0.0 to 1.0)
    double daily_subsidy_expense;   // Daily tax assistance/subsidies
    float dynamic_ICU_threshold;    // ICU occupancy threshold (-1.0f if not applicable)
} PolicyConfig;

// Accumulated metrics for the scenario
typedef struct {
    double total_economic_cost;
    int icu_overcrowding_days;
    int total_deaths;
    int total_recoveries;
    float accumulated_social_fatigue;

    // Execution time & profiling metrics (in seconds)
    double time_update_grid;
    double time_get_counts;
    double time_analytics;
    double time_total;
} PolicyMetrics;

#endif // POLICY_H