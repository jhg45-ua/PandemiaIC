#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "simulator.h"

// Reserve continous memory blocks on Heap
Grid* create_grid(int height, int width)
{
    Grid *grid = (Grid *)malloc(sizeof(Grid));
    grid->height = height;
    grid->width = width;
    int total_cells = height * width;

    grid->current_grid          = (int *)calloc(total_cells, sizeof(int));
    grid->next_grid             = (int *)calloc(total_cells, sizeof(int));
    grid->days_infected         = (int *)calloc(total_cells, sizeof(int));

    return grid;
}

void destroy_grid(Grid *grid)
{
    if (grid)
    {
        free(grid->current_grid);
        free(grid->next_grid);
        free(grid->days_infected);
        free(grid);
    }
}

// Initialize the population with a given number of initially random infected individuals
void init_population(Grid *grid, int initial_infected)
{
    int total = grid->height * grid->width;

    for (int i = 0; i < initial_infected; i++) {
        int idx = rand() % total;

        grid->current_grid[idx] = INFECTED;
        grid->days_infected[idx] = 1;
    }
}

// Main loop: updates cells (Data parelelisim / Stencil)
void update_grid(Grid *grid, float effective_beta, float excess_mortality_factor) 
{
    int heigth = grid->height;
    int width  = grid->width;

    for (int i = 0; i < heigth; i++) {
        for (int j = 0; j < width; j++) {
            int idx = i * width + j;
            int state = grid->current_grid[idx];

            if (state == SUSCEPTIBLE) {
                // Count the number of infected residents in the Moore neighborhood (8 adjacent cells)
                int infected_residents = 0;
                for (int di = -1; di <= 1; di++) {
                    for (int dj = -1; dj <= 1; dj++) {
                        if (di == 0 && dj == 0) continue; // Ignore central cell

                        int ni = i + di;
                        int nj = j + dj;

                        // Check grid limits
                        if (ni >= 0 && ni < heigth && nj >= 0 && nj < width)
                            if (grid->current_grid[ni * width + nj] == INFECTED)
                                infected_residents++;
                    }
                }

                // Stochastic transition based on the probability of the complementary event
                if (infected_residents > 0) {
                    float p_contagion = 1.0f - powf(1.0f - effective_beta, (float)infected_residents);
                    float r = (float)rand() / (float)RAND_MAX;

                    if (r < p_contagion) {
                        grid->next_grid[idx] = INFECTED;
                        grid->days_infected[idx]  = 1;
                    } else {
                        grid->next_grid[idx] = SUSCEPTIBLE;
                    }
                } else {
                    grid->next_grid[idx] = SUSCEPTIBLE;
                }
            } else if (state == INFECTED) {
                grid->days_infected[idx]++;

                // If the critical recovery period is exceeded
                if (grid->days_infected[idx] >= RECOVERY_DAYS) {
                    float p_muerte = BASE_DEATH_RATE * excess_mortality_factor;
                    float r = (float)rand() / (float)RAND_MAX;

                    if (r < p_muerte) {
                        grid->next_grid[idx] = DEAD;
                    } else {
                        grid->next_grid[idx] = RECOVERED;
                    }
                } else {
                    grid->next_grid[idx] = INFECTED; // Stays infected
                }

            } else {
                // Those who have recovered or died remain in their current status
                grid->next_grid[idx] = state;
            }
        }
    }
}

void swap_buffer(Grid *grid)
{
    int *temp = grid->current_grid;
    grid->current_grid = grid->next_grid;
    grid->next_grid = temp;
}

void get_counts(const Grid *grid, int *num_S, int *num_I, int *num_R, int *num_D)
{
    *num_S = 0;
    *num_I = 0;
    *num_R = 0;
    *num_D = 0;

    int total_cells = grid->height * grid->width;

    for (int idx = 0; idx < total_cells; idx++) {
        switch (grid->current_grid[idx]) {
            case SUSCEPTIBLE: (*num_S)++; break;
            case INFECTED:    (*num_I)++; break;
            case RECOVERED:   (*num_R)++; break;
            case DEAD:        (*num_D)++; break;
        }
    }
}