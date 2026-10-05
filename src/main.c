#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define _POSIX_C_SOURCE 200809L

// High-resolution monotonic timer returning seconds
static inline double get_time_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

#include "policy.h"
#include "simulator.h"
#include "healthcare.h"
#include "economy.h"
#include "society.h"

// Maximum number of policies to load from the configuration file, also the maximum number of scenarios to simulate
#define MAX_POLICIES 8

// Load policy configurations from a file
int load_policy_config(const char *filename, PolicyConfig *policies, int max_policies) {
    // Open the file for reading
    FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Error opening policy configuration file");
        return -1;
    }

    // Read each line and parse the policy parameters
    char line[256];
    int count = 0;
    
    while (fgets(line, sizeof(line), file) && count < max_policies) {
        if (line[0] == '#' || strlen(line) < 5) { // Skip comments and empty lines
            continue;
        }

        // Parse the line into the PolicyConfig structure
        // Expected format: name beta trade_restriction daily_subsidy_expense dynamic_ICU_threshold
        sscanf(line, "%31s %f %f %lf %f", 
               policies[count].name, 
               &policies[count].beta, 
               &policies[count].trade_restriction, 
               &policies[count].daily_subsidy_expense, 
               &policies[count].dynamic_ICU_threshold);
        count++;
    }

    fclose(file);
    return count;
}

int main(int argc, char *argv[]) {
    // CLI Parameters or defaults
    const char *conf_file = (argc > 1) ? argv[1] : "config/policies.conf";
    int n_hab = (argc > 2) ? atoi(argv[2]) : 100000;
    int days  = (argc > 3) ? atoi(argv[3]) : 150;
    int initial_infected = (argc > 4) ? atoi(argv[4]) : 10;
    int seed = (argc > 5) ? atoi(argv[5]) : 29; // Default seed for reproducibility

    // Adaptation to 2D square grid dimensions
    // Ensure the grid is square and the total population matches n_hab
    int width = (int)sqrt(n_hab);
    int height = width;
    int total_population = height * width;

    // Load policies from the configuration file
    PolicyConfig policies[MAX_POLICIES];
    int num_policies = load_policy_config(conf_file, policies, MAX_POLICIES);
    if (num_policies <= 0) {
        fprintf(stderr, "Error: No valid policies loaded from %s\n", conf_file);
        return EXIT_FAILURE;
    }

    printf("=================================================================\n");
    printf("  EPIDEMIOLOGICAL SIMULATOR PANDEMICSIM \n");
    printf("=================================================================\n");
    printf("Simulated population : %d inhabitants (%dx%d cells)\n", total_population, height, width);
    printf("Simulation days      : %d days\n", days);
    printf("Initial infected     : %d cases\n", initial_infected);
    printf("Loaded scenarios     : %d policies\n", num_policies);
    printf("Seed                 : %d\n", seed);
    printf("=================================================================\n\n");

    srand(seed); // Fixed seed to ensure reproducible measurements

    PolicyMetrics all_metrics[MAX_POLICIES];
    double total_sim_start = get_time_sec();

    // Inter-scenario loop (Global Functional Parallelism)
    for (int policy = 0; policy < num_policies; policy++) {
        PolicyConfig cfg = policies[policy];
        PolicyMetrics metrics = {0};

        double t_scenario_start = get_time_sec();

        // Initialize grid
        Grid *grid = create_grid(height, width);
        init_population(grid, initial_infected); // Initialize with infected individuals

        for (int t = 0; t < days; t++) {
            // 1. Get current counts
            double t0 = get_time_sec();
            int num_S = 0, num_I = 0, num_R = 0, num_D = 0;
            get_counts(grid, &num_S, &num_I, &num_R, &num_D);
            double t1 = get_time_sec();
            metrics.time_get_counts += (t1 - t0);

            // Dynamic traffic light trigger rule
            float current_beta = cfg.beta;
            float base_restriction = cfg.trade_restriction;

            // If dynamic ICU threshold is set, adjust trade restrictions based on ICU occupancy
            if (cfg.dynamic_ICU_threshold > 0.0f) {
                float icu_occupancy = ((float)num_I * 0.05f) / ((float)total_population * 0.005f);
                if (icu_occupancy >= cfg.dynamic_ICU_threshold) {
                    current_beta = 0.08f;
                    cfg.trade_restriction = 0.50f;
                } else {
                    cfg.trade_restriction = base_restriction;
                }
            }

            // 2. Analytical modules (Functional Parallelism)
            t0 = get_time_sec();

            float excess_mortality_factor = evaluate_healthcare_impact(num_I, total_population, &metrics);
            evaluate_economic_impact(num_I, total_population, &cfg, &metrics);
            float compliance = evaluate_social_impact(&cfg, &metrics);

            t1 = get_time_sec();
            metrics.time_analytics += (t1 - t0);

            // Adjust effective transmission by citizen compliance
            float effective_beta = current_beta / compliance;

            // 3. Cell updates (Data Parallelism)
            t0 = get_time_sec();

            update_grid(grid, effective_beta, excess_mortality_factor);
            swap_buffer(grid);

            t1 = get_time_sec();
            metrics.time_update_grid += (t1 - t0);
        }

        // Record final balance
        double t0 = get_time_sec();

        int final_S = 0, final_I = 0, final_R = 0, final_D = 0;
        get_counts(grid, &final_S, &final_I, &final_R, &final_D);
        
        double t1 = get_time_sec();
        metrics.time_get_counts += (t1 - t0);

        metrics.total_deaths = final_D;
        metrics.total_recoveries = final_R;

        double t_scenario_end = get_time_sec();
        metrics.time_total = t_scenario_end - t_scenario_start;
        all_metrics[policy] = metrics;

        printf("--- Scenario: %-16s ---\n", cfg.name);
        printf("  Execution Time        : %.4f s\n", metrics.time_total);
        printf("  Total Economic Cost   : %.2f M€\n", metrics.total_economic_cost / 1000000.0);
        printf("  Total Deaths          : %d people\n", metrics.total_deaths);
        printf("  Total Recoveries      : %d people\n", metrics.total_recoveries);
        printf("  ICU Collapse Days     : %d days\n", metrics.icu_overcrowding_days);
        printf("  Final Social Fatigue  : %.2f\n\n", metrics.accumulated_social_fatigue);

        destroy_grid(grid);
    }

    double total_sim_end = get_time_sec();
    double total_wall_time = total_sim_end - total_sim_start;

    // Accumulated profiling across all scenarios
    double sum_scenario_time = 0.0;
    double sum_update_grid = 0.0;
    double sum_get_counts = 0.0;
    double sum_analytics = 0.0;

    for (int policy = 0; policy < num_policies; policy++) {
        sum_scenario_time += all_metrics[policy].time_total;
        sum_update_grid   += all_metrics[policy].time_update_grid;
        sum_get_counts    += all_metrics[policy].time_get_counts;
        sum_analytics     += all_metrics[policy].time_analytics;
    }

    printf("====================================================================================================\n");
    printf("                               PROFILING & EXECUTION TIME BREAKDOWN                                 \n");
    printf("====================================================================================================\n");
    printf("%-16s | %10s | %22s | %20s | %18s\n", 
           "Scenario", "Total (s)", "Update Grid (s)", "Get Counts (s)", "Analytics (s)");
    printf("-----------------+------------+------------------------+----------------------+---------------------\n");
    for (int p = 0; p < num_policies; p++) {
        double t_tot = all_metrics[p].time_total;
        printf("%-16s | %8.4f s | %8.4f s (%5.1f%%)   | %7.4f s (%5.1f%%)   | %7.4f s (%5.1f%%)\n",
               policies[p].name,
               t_tot,
               all_metrics[p].time_update_grid,
               t_tot > 0 ? (all_metrics[p].time_update_grid / t_tot) * 100.0 : 0.0,
               all_metrics[p].time_get_counts,
               t_tot > 0 ? (all_metrics[p].time_get_counts / t_tot) * 100.0 : 0.0,
               all_metrics[p].time_analytics,
               t_tot > 0 ? (all_metrics[p].time_analytics / t_tot) * 100.0 : 0.0);
    }
    printf("-----------------+------------+------------------------+----------------------+---------------------\n");
    printf("%-16s | %8.4f s | %8.4f s (%5.1f%%)   | %7.4f s (%5.1f%%)   | %7.4f s (%5.1f%%)\n",
           "SUM SCENARIOS",
           sum_scenario_time,
           sum_update_grid,
           sum_scenario_time > 0 ? (sum_update_grid / sum_scenario_time) * 100.0 : 0.0,
           sum_get_counts,
           sum_scenario_time > 0 ? (sum_get_counts / sum_scenario_time) * 100.0 : 0.0,
           sum_analytics,
           sum_scenario_time > 0 ? (sum_analytics / sum_scenario_time) * 100.0 : 0.0);
    printf("Total Wall-Clock Time: %.4f s\n", total_wall_time);
    printf("====================================================================================================\n");

    return EXIT_SUCCESS;
}