#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <unistd.h>

#include <mpi.h> // MPI header for parallel processing

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
        stats->total_time_comm        += replicas[r].time_comm;
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
    // Initialize MPI environment
    int rank, numprocs;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &numprocs);

    char hostname[MPI_MAX_PROCESSOR_NAME];
    int name_len;
    MPI_Get_processor_name(hostname, &name_len);
    printf("[Rank %d de %d] Ejecutando en la máquina: %s (PID: %d)\n", 
        rank, numprocs, hostname, getpid());


    // CLI Parameters or defaults
    const char *conf_file = (argc > 1) ? argv[1] : "config/policies.conf";
    int n_hab = (argc > 2) ? atoi(argv[2]) : 100000;
    int days  = (argc > 3) ? atoi(argv[3]) : 150;
    int initial_infected = (argc > 4) ? atoi(argv[4]) : 10;
    int n_sim = (argc > 5) ? atoi(argv[5]) : 20; // Number of Monte Carlo replicas
    int seed = (argc > 6) ? atoi(argv[6]) : 29; // Default seed for reproducibility
    const char *strategy = (argc > 7) ? argv[7] : "macro"; // Parallel strategy: "macro" or "micro"
    int is_micro = (strcmp(strategy, "micro") == 0);

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

    if (rank == 0) {
        printf("=================================================================\n");
        printf("  EPIDEMIOLOGICAL SIMULATOR PANDEMICSIM - MONTE CARLO (MPI)\n");
        printf("=================================================================\n");
        printf("Parallel Strategy    : %s (%s)\n", 
               is_micro ? "MICRO" : "MACRO",
               is_micro ? "2D Domain Decomposition (Halo Exchange)" : "Task Farm (Replica Distribution)");
        printf("MPI Processes        : %d processes\n", numprocs);
        printf("Simulated population : %d inhabitants (%dx%d cells)\n", total_population, height, width);
        printf("Simulation days      : %d days\n", days);
        printf("Initial infected     : %d cases\n", initial_infected);
        printf("Loaded policies      : %d policies\n", num_policies);
        printf("Replicas per policy  : %d Monte Carlo runs\n", n_sim);
        printf("Base seed            : %d\n", seed);
        printf("=================================================================\n\n");
    }

    PolicyStats all_stats[MAX_POLICIES];
    double total_sim_start = MPI_Wtime();

    // 1. Inter-policy loop
    for (int policy = 0; policy < num_policies; policy++) {
        PolicyConfig cfg_base = policies[policy];
        ReplicaMetrics *replicas = calloc(n_sim, sizeof(ReplicaMetrics));

        if (!is_micro) {
            // =========================================================================
            // ESTRATEGIA MACRO: Paralelismo de Tareas (Reparto de Réplicas Monte Carlo)
            // =========================================================================
            int base_chunk = n_sim / numprocs;
            int rem = n_sim % numprocs;
            int local_count = base_chunk + (rank < rem ? 1 : 0);
            int r_start = rank * base_chunk + (rank < rem ? rank : rem);
            int r_end = r_start + local_count;

            for (int r = r_start; r < r_end; r++) {
                srand(seed + policy * 1000 + r);

                PolicyConfig cfg = cfg_base;
                ReplicaMetrics metrics = {0};

                double t_replica_start = MPI_Wtime();

                Grid *grid = create_grid(height, width);
                init_population(grid, initial_infected);

                for (int t = 0; t < days; t++) {
                    // 1. Get current counts
                    double t0 = MPI_Wtime();
                    int num_S = 0, num_I = 0, num_R = 0, num_D = 0;
                    get_counts(grid, &num_S, &num_I, &num_R, &num_D);
                    double t1 = MPI_Wtime();
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
                    t0 = MPI_Wtime();
                    float excess_mortality_factor = evaluate_healthcare_impact(num_I, total_population, (ReplicaMetrics*)&metrics);
                    evaluate_economic_impact(num_I, total_population, &cfg, (ReplicaMetrics*)&metrics);
                    float compliance = evaluate_social_impact(&cfg, (ReplicaMetrics*)&metrics);
                    t1 = MPI_Wtime();
                    metrics.time_analytics += (t1 - t0);

                    float effective_beta = current_beta / compliance;

                    // 3. Cell updates
                    t0 = MPI_Wtime();
                    update_grid(grid, effective_beta, excess_mortality_factor);
                    swap_buffer(grid);
                    t1 = MPI_Wtime();
                    metrics.time_update_grid += (t1 - t0);
                }

                int final_S = 0, final_I = 0, final_R = 0, final_D = 0;
                get_counts(grid, &final_S, &final_I, &final_R, &final_D);

                metrics.total_deaths = final_D;
                metrics.total_recoveries = final_R;
                metrics.time_total = MPI_Wtime() - t_replica_start;

                replicas[r] = metrics;
                destroy_grid(grid);
            }

            // Comunicación: Recopilación de réplicas en rank 0
            double t_comm_start = MPI_Wtime();
            if (rank != 0) {
                if (local_count > 0) {
                    MPI_Send(&replicas[r_start], local_count * sizeof(ReplicaMetrics), MPI_BYTE, 0, 0, MPI_COMM_WORLD);
                }
            } else {
                for (int p = 1; p < numprocs; p++) {
                    int p_count = base_chunk + (p < rem ? 1 : 0);
                    int p_start = p * base_chunk + (p < rem ? p : rem);
                    if (p_count > 0) {
                        MPI_Recv(&replicas[p_start], p_count * sizeof(ReplicaMetrics), MPI_BYTE, p, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                    }
                }
            }
            double t_comm_end = MPI_Wtime();
            double policy_comm = t_comm_end - t_comm_start;

            if (rank == 0) {
                compute_policy_stats(replicas, n_sim, &all_stats[policy]);
                all_stats[policy].total_time_comm = policy_comm;

                printf("=== Policy: %-16s ===\n", cfg_base.name);
                printf("  Economic Cost (M€) : %.2f ± %.2f M€\n", all_stats[policy].mean_cost / 1e6, all_stats[policy].std_cost / 1e6);
                printf("  Total Deaths       : %.1f ± %.1f people [Range: %d - %d]\n",
                    all_stats[policy].mean_deaths, all_stats[policy].std_deaths,
                    all_stats[policy].min_deaths, all_stats[policy].max_deaths);
                printf("  ICU Collapse Days  : %.1f ± %.1f days\n", all_stats[policy].mean_icu_days, all_stats[policy].std_icu_days);
                printf("  Mean Social Fatigue: %.2f\n", all_stats[policy].mean_fatigue);
                printf("  Total Compute Time : %.4f s (%d runs)\n\n", all_stats[policy].total_time, n_sim);
            }

        } else {
            // =========================================================================
            // ESTRATEGIA MICRO: Paralelismo de Datos (Descomposición 2D con Halo Exchange)
            // =========================================================================
            int base_h = height / numprocs;
            int rem_h = height % numprocs;
            int local_height = base_h + (rank < rem_h ? 1 : 0);
            int row_start = rank * base_h + (rank < rem_h ? rank : rem_h);
            int row_end = row_start + local_height;

            int prev_rank = (rank > 0) ? rank - 1 : MPI_PROC_NULL;
            int next_rank = (rank < numprocs - 1) ? rank + 1 : MPI_PROC_NULL;

            for (int r = 0; r < n_sim; r++) {
                PolicyConfig cfg = cfg_base;
                ReplicaMetrics metrics = {0};
                double t_replica_start = MPI_Wtime();

                // Malla local con filas fantasma (0 = halo superior, local_height+1 = halo inferior)
                Grid *grid = create_grid(local_height + 2, width);

                // Inicialización idéntica y determinista
                srand(seed + policy * 1000 + r);
                for (int k = 0; k < initial_infected; k++) {
                    int g_idx = rand() % total_population;
                    int gi = g_idx / width;
                    int gj = g_idx % width;
                    if (gi >= row_start && gi < row_end) {
                        int li = gi - row_start + 1;
                        grid->current_grid[li * width + gj] = INFECTED;
                        grid->days_infected[li * width + gj] = 1;
                    }
                }

                for (int t = 0; t < days; t++) {
                    // 1. Intercambio de bordes / halos perimetrales (Comunicación punto a punto)
                    double tc0 = MPI_Wtime();
                    MPI_Sendrecv(&grid->current_grid[1 * width], width, MPI_INT, prev_rank, 0,
                                 &grid->current_grid[0 * width], width, MPI_INT, prev_rank, 1,
                                 MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                    MPI_Sendrecv(&grid->current_grid[local_height * width], width, MPI_INT, next_rank, 1,
                                 &grid->current_grid[(local_height + 1) * width], width, MPI_INT, next_rank, 0,
                                 MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                    double tc1 = MPI_Wtime();
                    metrics.time_comm += (tc1 - tc0);

                    // 2. Recuento local + Reducción global Allreduce
                    double t0 = MPI_Wtime();
                    int local_counts[4] = {0, 0, 0, 0};
                    for (int i = 1; i <= local_height; i++) {
                        for (int j = 0; j < width; j++) {
                            int st = grid->current_grid[i * width + j];
                            if (st >= 0 && st < 4) local_counts[st]++;
                        }
                    }
                    double t1 = MPI_Wtime();
                    metrics.time_get_counts += (t1 - t0);

                    tc0 = MPI_Wtime();
                    int global_counts[4] = {0, 0, 0, 0};
                    MPI_Allreduce(local_counts, global_counts, 4, MPI_INT, MPI_SUM, MPI_COMM_WORLD);
                    tc1 = MPI_Wtime();
                    metrics.time_comm += (tc1 - tc0);

                    int num_I = global_counts[1];

                    // 3. Módulos analíticos (Cómputo local coherente)
                    t0 = MPI_Wtime();
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

                    float excess_mortality_factor = evaluate_healthcare_impact(num_I, total_population, &metrics);
                    evaluate_economic_impact(num_I, total_population, &cfg, &metrics);
                    float compliance = evaluate_social_impact(&cfg, &metrics);
                    float effective_beta = current_beta / compliance;
                    t1 = MPI_Wtime();
                    metrics.time_analytics += (t1 - t0);

                    // 4. Actualización del dominio propio
                    t0 = MPI_Wtime();
                    for (int i = 1; i <= local_height; i++) {
                        for (int j = 0; j < width; j++) {
                            int idx = i * width + j;
                            int state = grid->current_grid[idx];

                            if (state == SUSCEPTIBLE) {
                                int infected_residents = 0;
                                for (int di = -1; di <= 1; di++) {
                                    for (int dj = -1; dj <= 1; dj++) {
                                        if (di == 0 && dj == 0) continue;
                                        int ni = i + di;
                                        int nj = j + dj;
                                        if (ni == 0 && prev_rank == MPI_PROC_NULL) continue;
                                        if (ni == local_height + 1 && next_rank == MPI_PROC_NULL) continue;
                                        if (nj >= 0 && nj < width) {
                                            if (grid->current_grid[ni * width + nj] == INFECTED)
                                                infected_residents++;
                                        }
                                    }
                                }
                                if (infected_residents > 0) {
                                    float p_contagion = 1.0f - powf(1.0f - effective_beta, (float)infected_residents);
                                    float r_val = (float)rand() / (float)RAND_MAX;
                                    if (r_val < p_contagion) {
                                        grid->next_grid[idx] = INFECTED;
                                        grid->days_infected[idx] = 1;
                                    } else {
                                        grid->next_grid[idx] = SUSCEPTIBLE;
                                    }
                                } else {
                                    grid->next_grid[idx] = SUSCEPTIBLE;
                                }
                            } else if (state == INFECTED) {
                                grid->days_infected[idx]++;
                                if (grid->days_infected[idx] >= RECOVERY_DAYS) {
                                    float p_death = BASE_DEATH_RATE * excess_mortality_factor;
                                    float r_val = (float)rand() / (float)RAND_MAX;
                                    if (r_val < p_death) {
                                        grid->next_grid[idx] = DEAD;
                                    } else {
                                        grid->next_grid[idx] = RECOVERED;
                                    }
                                } else {
                                    grid->next_grid[idx] = INFECTED;
                                }
                            } else {
                                grid->next_grid[idx] = state;
                            }
                        }
                    }
                    swap_buffer(grid);
                    t1 = MPI_Wtime();
                    metrics.time_update_grid += (t1 - t0);
                }

                int local_final[4] = {0, 0, 0, 0};
                for (int i = 1; i <= local_height; i++) {
                    for (int j = 0; j < width; j++) {
                        int st = grid->current_grid[i * width + j];
                        if (st >= 0 && st < 4) local_final[st]++;
                    }
                }
                int global_final[4] = {0, 0, 0, 0};
                MPI_Allreduce(local_final, global_final, 4, MPI_INT, MPI_SUM, MPI_COMM_WORLD);

                metrics.total_deaths = global_final[3];
                metrics.total_recoveries = global_final[2];
                metrics.time_total = MPI_Wtime() - t_replica_start;

                replicas[r] = metrics;
                destroy_grid(grid);
            }

            if (rank == 0) {
                compute_policy_stats(replicas, n_sim, &all_stats[policy]);

                printf("=== Policy: %-16s ===\n", cfg_base.name);
                printf("  Economic Cost (M€) : %.2f ± %.2f M€\n", all_stats[policy].mean_cost / 1e6, all_stats[policy].std_cost / 1e6);
                printf("  Total Deaths       : %.1f ± %.1f people [Range: %d - %d]\n",
                    all_stats[policy].mean_deaths, all_stats[policy].std_deaths,
                    all_stats[policy].min_deaths, all_stats[policy].max_deaths);
                printf("  ICU Collapse Days  : %.1f ± %.1f days\n", all_stats[policy].mean_icu_days, all_stats[policy].std_icu_days);
                printf("  Mean Social Fatigue: %.2f\n", all_stats[policy].mean_fatigue);
                printf("  Total Compute Time : %.4f s (%d runs)\n\n", all_stats[policy].total_time, n_sim);
            }
        }

        free(replicas);
    }

    double t_barrier_start = MPI_Wtime();
    MPI_Barrier(MPI_COMM_WORLD);
    double total_sim_end = MPI_Wtime();
    double barrier_time = total_sim_end - t_barrier_start;
    double total_wall_time = total_sim_end - total_sim_start;

    // Aggregate total times across all policies for profiling and performance metrics
    double sum_update_grid = 0.0;
    double sum_get_counts  = 0.0;
    double sum_analytics   = 0.0;
    double sum_comm        = barrier_time;

    for (int p = 0; p < num_policies; p++) {
        sum_update_grid += all_stats[p].total_time_update_grid;
        sum_get_counts  += all_stats[p].total_time_get_counts;
        sum_analytics   += all_stats[p].total_time_analytics;
        sum_comm        += all_stats[p].total_time_comm;
    }

    double sum_total_compute = sum_update_grid + sum_get_counts + sum_analytics;
    double sum_total_phases = sum_total_compute + sum_comm;

    // Throughput Calculations (Macro and Micro/MCUPS)
    int total_simulations = num_policies * n_sim;
    unsigned long long total_cell_updates = (unsigned long long)total_simulations * days * total_population;

    double throughput_sims_per_sec = (double)total_simulations / total_wall_time;
    double mcups = (sum_update_grid > 0.0) ? 
                   ((double)total_cell_updates / (sum_update_grid * 1e6)) : 0.0;

    // Profiling Report Breakdown
    if (rank == 0) {
        printf("========================================================================================================================\n");
        printf("                                          PROFILING & EXECUTION TIME BREAKDOWN                                          \n");
        printf("========================================================================================================================\n");
        printf("%-16s | %10s | %19s | %18s | %15s | %18s\n", 
            "Policy", "Total (s)", "Update Grid (s)", "Get Counts (s)", "Analytics (s)", "Comm & Sync (s)");
        printf("-----------------+------------+---------------------+--------------------+-----------------+--------------------\n");
        
        for (int p = 0; p < num_policies; p++) {
            double t_tot = all_stats[p].total_time;
            printf("%-16s | %8.4f s | %8.4f s (%5.2f%%) | %7.4f s (%5.2f%%) | %7.4f s (%5.2f%%) | %7.4f s (%5.2f%%)\n",
                policies[p].name,
                t_tot,
                all_stats[p].total_time_update_grid,
                t_tot > 0 ? (all_stats[p].total_time_update_grid / t_tot) * 100.0 : 0.0,
                all_stats[p].total_time_get_counts,
                t_tot > 0 ? (all_stats[p].total_time_get_counts / t_tot) * 100.0 : 0.0,
                all_stats[p].total_time_analytics,
                t_tot > 0 ? (all_stats[p].total_time_analytics / t_tot) * 100.0 : 0.0,
                all_stats[p].total_time_comm,
                t_tot > 0 ? (all_stats[p].total_time_comm / t_tot) * 100.0 : 0.0);
        }
        printf("-----------------+------------+---------------------+--------------------+-----------------+--------------------\n");
        printf("%-16s | %8.4f s | %8.4f s (%5.2f%%) | %7.4f s (%5.2f%%) | %7.4f s (%5.2f%%) | %7.4f s (%5.2f%%)\n",
            "TOTAL PHASES",
            sum_total_phases,
            sum_update_grid, sum_total_phases > 0 ? (sum_update_grid / sum_total_phases) * 100.0 : 0.0,
            sum_get_counts,  sum_total_phases > 0 ? (sum_get_counts / sum_total_phases) * 100.0 : 0.0,
            sum_analytics,   sum_total_phases > 0 ? (sum_analytics / sum_total_phases) * 100.0 : 0.0,
            sum_comm,        sum_total_phases > 0 ? (sum_comm / sum_total_phases) * 100.0 : 0.0);
        printf("Total Wall-Clock Time: %.4f s\n", total_wall_time);
        printf("========================================================================================================================\n");
        printf("                                    COMPUTATION VS COMMUNICATION RATIO (TAREA 3)                                        \n");
        printf("========================================================================================================================\n");
        printf("Total Computation Time   : %.4f s (%.2f%% of phased time)\n", sum_total_compute, sum_total_phases > 0 ? (sum_total_compute / sum_total_phases) * 100.0 : 0.0);
        printf("Total Comm & Sync Time   : %.4f s (%.2f%% of phased time)\n", sum_comm, sum_total_phases > 0 ? (sum_comm / sum_total_phases) * 100.0 : 0.0);
        printf("Computation / Comm Ratio : %.2f : 1\n", sum_comm > 0.0 ? (sum_total_compute / sum_comm) : 999.99);
        printf("========================================================================================================================\n");
        printf("                                      SYSTEM THROUGHPUT & PERFORMANCE METRICS                                           \n");
        printf("========================================================================================================================\n");
        printf("Total Replicas Executed  : %d simulations (%d policies x %d runs)\n", total_simulations, num_policies, n_sim);
        printf("Total Cell Updates       : %llu cell-day transitions\n", total_cell_updates);
        printf("Macro Throughput         : %.2f simulations / sec\n", throughput_sims_per_sec);
        printf("Kernel Throughput (MCUPS): %.2f Million Cell Updates / sec (MCUPS)\n", mcups);
        printf("========================================================================================================================\n");
    }


    // Finalize MPI environment
    MPI_Finalize();

    return EXIT_SUCCESS;
}