#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

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

// Maximum number of policies to load from the configuration file
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

void compute_policy_stats(const ReplicaMetrics *replicas, int n_sim, PolicyStats *stats) {
    memset(stats, 0, sizeof(PolicyStats));
    stats->min_deaths = 2e9;
    stats->max_deaths = -1;

    double sum_cost = 0.0, sum_deaths = 0.0, sum_icu = 0.0, sum_fatigue = 0.0;

    for (int r = 0; r < n_sim; r++) {
        sum_cost += replicas[r].total_economic_cost;
        sum_deaths += replicas[r].total_deaths;
        sum_icu += replicas[r].icu_overcrowding_days;
        sum_fatigue += replicas[r].accumulated_social_fatigue;

        if (replicas[r].total_deaths > stats->max_deaths) stats->max_deaths = replicas[r].total_deaths;
        if (replicas[r].total_deaths < stats->min_deaths) stats->min_deaths = replicas[r].total_deaths;

        stats->total_time_update_grid += replicas[r].time_update_grid;
        stats->total_time_get_counts  += replicas[r].time_get_counts;
        stats->total_time_analytics   += replicas[r].time_analytics;
        stats->total_time             += replicas[r].time_total;
    }

    stats->mean_cost    = sum_cost / n_sim;
    stats->mean_deaths  = sum_deaths / n_sim;
    stats->mean_icu_days= sum_icu / n_sim;
    stats->mean_fatigue = sum_fatigue / n_sim;

    // Compute Standard Deviation (σ)
    double var_cost = 0.0, var_deaths = 0.0, var_icu = 0.0;
    for (int r = 0; r < n_sim; r++) {
        var_cost   += pow(replicas[r].total_economic_cost - stats->mean_cost, 2);
        var_deaths += pow(replicas[r].total_deaths - stats->mean_deaths, 2);
        var_icu    += pow(replicas[r].icu_overcrowding_days - stats->mean_icu_days, 2);
    }

    stats->std_cost     = sqrt(var_cost / n_sim);
    stats->std_deaths   = sqrt(var_deaths / n_sim);
    stats->std_icu_days = sqrt(var_icu / n_sim);
}

int main(int argc, char *argv[]) {
    // CLI Parameters or defaults
    const char *conf_file = (argc > 1) ? argv[1] : "config/policies.conf";
    int n_hab = (argc > 2) ? atoi(argv[2]) : 100000;
    int days  = (argc > 3) ? atoi(argv[3]) : 150;
    int initial_infected = (argc > 4) ? atoi(argv[4]) : 10;
    int n_sim = (argc > 5) ? atoi(argv[5]) : 20; // Number of Monte Carlo replicas
    int seed = (argc > 6) ? atoi(argv[6]) : 29; // Default seed for reproducibility

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
    printf("  EPIDEMIOLOGICAL SIMULATOR PANDEMICSIM - MONTE CARLO\n");
    printf("=================================================================\n");
    printf("Simulated population : %d inhabitants (%dx%d cells)\n", total_population, height, width);
    printf("Simulation days      : %d days\n", days);
    printf("Initial infected     : %d cases\n", initial_infected);
    printf("Loaded policies      : %d policies\n", num_policies);
    printf("Replicas per policy  : %d Monte Carlo runs\n", n_sim);
    printf("Base seed            : %d\n", seed);
    printf("=================================================================\n\n");

    PolicyStats all_stats[MAX_POLICIES];
    double total_sim_start = get_time_sec();

    // 1. Inter-policy loop
    for (int policy = 0; policy < num_policies; policy++) {
        PolicyConfig cfg_base = policies[policy];
        ReplicaMetrics *replicas = calloc(n_sim, sizeof(ReplicaMetrics));

        // 2. Monte Carlo Replicas loop
        for (int r = 0; r < n_sim; r++) {
            // Unique reproducible seed per replica
            srand(seed + policy * 1000 + r);

            PolicyConfig cfg = cfg_base;
            ReplicaMetrics metrics = {0};

            double t_replica_start = get_time_sec();

            Grid *grid = create_grid(height, width);
            init_population(grid, initial_infected);

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

                if (cfg.dynamic_ICU_threshold > 0.0f) {
                    float icu_occupancy = ((float)num_I * 0.05f) / ((float)total_population * 0.005f);
                    if (icu_occupancy >= cfg.dynamic_ICU_threshold) {
                        current_beta = 0.08f;
                        cfg.trade_restriction = 0.50f;
                    } else {
                        cfg.trade_restriction = base_restriction;
                    }
                }

                // 2. Analytical modules
                t0 = get_time_sec();

                float excess_mortality_factor = evaluate_healthcare_impact(num_I, total_population, (ReplicaMetrics*)&metrics);
                evaluate_economic_impact(num_I, total_population, &cfg, (ReplicaMetrics*)&metrics);
                float compliance = evaluate_social_impact(&cfg, (ReplicaMetrics*)&metrics);

                t1 = get_time_sec();
                metrics.time_analytics += (t1 - t0);

                float effective_beta = current_beta / compliance;

                // 3. Cell updates
                t0 = get_time_sec();

                update_grid(grid, effective_beta, excess_mortality_factor);
                swap_buffer(grid);

                t1 = get_time_sec();
                metrics.time_update_grid += (t1 - t0);
            }

            int final_S = 0, final_I = 0, final_R = 0, final_D = 0;
            get_counts(grid, &final_S, &final_I, &final_R, &final_D);

            metrics.total_deaths = final_D;
            metrics.total_recoveries = final_R;
            metrics.time_total = get_time_sec() - t_replica_start;

            replicas[r] = metrics;
            destroy_grid(grid);
        }

        // Aggregate statistics for policy
        compute_policy_stats(replicas, n_sim, &all_stats[policy]);

        printf("=== Policy: %-16s ===\n", cfg_base.name);
        printf("  Economic Cost (M€) : %.2f ± %.2f M€\n", all_stats[policy].mean_cost / 1e6, all_stats[policy].std_cost / 1e6);
        printf("  Total Deaths       : %.1f ± %.1f people [Range: %d - %d]\n",
               all_stats[policy].mean_deaths, all_stats[policy].std_deaths,
               all_stats[policy].min_deaths, all_stats[policy].max_deaths);
        printf("  ICU Collapse Days  : %.1f ± %.1f days\n", all_stats[policy].mean_icu_days, all_stats[policy].std_icu_days);
        printf("  Mean Social Fatigue: %.2f\n", all_stats[policy].mean_fatigue);
        printf("  Total Compute Time : %.4f s (%d runs)\n\n", all_stats[policy].total_time, n_sim);

        free(replicas);
    }

    double total_sim_end = get_time_sec();
    double total_wall_time = total_sim_end - total_sim_start;

    // Aggregate total times across all policies for profiling and performance metrics
    double sum_update_grid = 0.0;
    double sum_get_counts  = 0.0;
    double sum_analytics   = 0.0;

    for (int p = 0; p < num_policies; p++) {
        sum_update_grid += all_stats[p].total_time_update_grid;
        sum_get_counts  += all_stats[p].total_time_get_counts;
        sum_analytics   += all_stats[p].total_time_analytics;
    }

    double sum_total_phases = sum_update_grid + sum_get_counts + sum_analytics;

    // Throughput Calculations (Macro and Micro/MCUPS)
    int total_simulations = num_policies * n_sim;
    unsigned long long total_cell_updates = (unsigned long long)total_simulations * days * total_population;

    double throughput_sims_per_sec = (double)total_simulations / total_wall_time;
    double mcups = (sum_update_grid > 0.0) ? 
                   ((double)total_cell_updates / (sum_update_grid * 1e6)) : 0.0;

    // Profiling Report Breakdown
    printf("====================================================================================================\n");
    printf("                               PROFILING & EXECUTION TIME BREAKDOWN                                 \n");
    printf("====================================================================================================\n");
    printf("%-16s | %10s | %21s | %20s | %18s\n", 
           "Policy", "Total (s)", "Update Grid (s)", "Get Counts (s)", "Analytics (s)");
    printf("-----------------+------------+-----------------------+----------------------+---------------------\n");
    
    for (int p = 0; p < num_policies; p++) {
        double t_tot = all_stats[p].total_time;
        printf("%-16s | %8.4f s | %8.4f s (%5.3f%%)   | %7.4f s (%5.3f%%) | %7.4f s (%5.3f%%)\n",
               policies[p].name,
               t_tot,
               all_stats[p].total_time_update_grid,
               t_tot > 0 ? (all_stats[p].total_time_update_grid / t_tot) * 100.0 : 0.0,
               all_stats[p].total_time_get_counts,
               t_tot > 0 ? (all_stats[p].total_time_get_counts / t_tot) * 100.0 : 0.0,
               all_stats[p].total_time_analytics,
               t_tot > 0 ? (all_stats[p].total_time_analytics / t_tot) * 100.0 : 0.0);
    }
    printf("-----------------+------------+------------------------+----------------------+---------------------\n");
    printf("%-16s | %8.4f s | %8.4f s (%5.3f%%)   | %7.4f s (%5.3f%%)  | %7.4f s (%5.3f%%)\n",
           "TOTAL PHASES",
           sum_total_phases,
           sum_update_grid,
           sum_total_phases > 0 ? (sum_update_grid / sum_total_phases) * 100.0 : 0.0,
           sum_get_counts,
           sum_total_phases > 0 ? (sum_get_counts / sum_total_phases) * 100.0 : 0.0,
           sum_analytics,
           sum_total_phases > 0 ? (sum_analytics / sum_total_phases) * 100.0 : 0.0);
    printf("Total Wall-Clock Time: %.4f s\n", total_wall_time);
    printf("====================================================================================================\n");
    printf("                               SYSTEM THROUGHPUT & PERFORMANCE METRICS                              \n");
    printf("====================================================================================================\n");
    printf("Total Replicas Executed  : %d simulations (%d policies x %d runs)\n", total_simulations, num_policies, n_sim);
    printf("Total Cell Updates       : %llu cell-day transitions\n", total_cell_updates);
    printf("Macro Throughput         : %.2f simulations / sec\n", throughput_sims_per_sec);
    printf("Kernel Throughput (MCUPS): %.2f Million Cell Updates / sec (MCUPS)\n", mcups);
    printf("====================================================================================================\n");

    return EXIT_SUCCESS;
}