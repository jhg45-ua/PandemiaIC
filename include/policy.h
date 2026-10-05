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
    char name[32];                      // Name of the policy/scenario
    float beta;                         // Base transmission rate per contact
    float trade_restriction;            // Proportion of the economy at a halt (0.0 to 1.0)
    double daily_subsidy_expense;       // Daily tax assistance/subsidies
    float dynamic_ICU_threshold;        // ICU occupancy threshold (-1.0f if not applicable)
} PolicyConfig;

// Accumulated metrics for the scenario
typedef struct {
    double total_economic_cost;         // Total economic cost of the policy
    int icu_overcrowding_days;          // Number of days ICU occupancy exceeded the threshold
    int total_deaths;                   // Total number of deaths
    int total_recoveries;               // Total number of recoveries
    float accumulated_social_fatigue;   // Accumulated social fatigue

    // Execution time & profiling metrics (in seconds)
    double time_update_grid;
    double time_get_counts;
    double time_analytics;
    double time_total;
} ReplicaMetrics;

typedef struct {
    double mean_cost;
    double std_cost;

    double mean_deaths;
    double std_deaths;
    int min_deaths;
    int max_deaths;

    double mean_icu_days;
    double std_icu_days;

    double mean_fatigue;

    // Total profiling times accumulated across all replicas
    double total_time_update_grid;
    double total_time_get_counts;
    double total_time_analytics;
    double total_time;
} PolicyStats;

#endif // POLICY_H