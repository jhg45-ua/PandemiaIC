#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#include "policy.h"
#include "simulator.h"
#include "healthcare.h"
#include "economy.h"
#include "society.h"

#define MAX_POLICIES 8

// Load policy configurations from a file
int load_policy_config(const char *filename, PolicyConfig *policies, int max_policies) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Error opening policy configuration file");
        return -1;
    }

    char line[256];
    int count = 0;
    
    while (fgets(line, sizeof(line), file) && count < max_policies) {
        if (line[0] == '#' || strlen(line) < 5) { // Skip comments and empty lines
            continue;
        }
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

    // Adaptation to 2D square grid dimensions
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
    printf("  EPIDEMIOLOGICAL SIMULATOR PANDEMICSIM (P2 - Sequential)\n");
    printf("=================================================================\n");
    printf("Simulated population : %d inhabitants (%dx%d cells)\n", total_population, height, width);
    printf("Simulation days      : %d days\n", days);
    printf("Loaded scenarios     : %d policies\n", num_policies);
    printf("=================================================================\n\n");

    srand(42); // Fixed seed to ensure reproducible measurements

    // Inter-scenario loop (Global Functional Parallelism)
    for (int p = 0; p < num_policies; p++) {
        PolicyConfig cfg = policies[p];
        PolicyMetrics metrics = {0.0, 0, 0, 0, 0.0f};

        // Initialize grid
        Grid *grid = create_grid(height, width);
        init_population(grid, 10); // Initialize with 10 infected individuals

        for (int t = 0; t < days; t++) {
            // 1. Get current counts
            int num_S = 0, num_I = 0, num_R = 0, num_D = 0;
            get_counts(grid, &num_S, &num_I, &num_R, &num_D);

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

            // 2. Analytical modules (Functional Parallelism)
            float excess_mortality_factor = evaluate_healthcare_impact(num_I, total_population, &metrics);
            evaluate_economic_impact(num_I, total_population, &cfg, &metrics);
            float compliance = evaluate_social_impact(&cfg, &metrics);

            // Adjust effective transmission by citizen compliance
            float effective_beta = current_beta / compliance;

            // 3. Cell updates (Data Parallelism)
            update_grid(grid, effective_beta, excess_mortality_factor);
            swap_buffer(grid);
        }

        // Record final balance
        int final_S = 0, final_I = 0, final_R = 0, final_D = 0;
        get_counts(grid, &final_S, &final_I, &final_R, &final_D);
        metrics.total_deaths = final_D;
        metrics.total_recoveries = final_R;

        printf("--- Scenario: %-16s ---\n", cfg.name);
        printf("  Total Economic Cost   : %.2f M€\n", metrics.total_economic_cost / 1000000.0);
        printf("  Total Deaths          : %d people\n", metrics.total_deaths);
        printf("  Total Recoveries      : %d people\n", metrics.total_recoveries);
        printf("  ICU Collapse Days     : %d days\n", metrics.icu_overcrowding_days);
        printf("  Final Social Fatigue  : %.2f\n\n", metrics.accumulated_social_fatigue);

        destroy_grid(grid);
    }

    return EXIT_SUCCESS;
}