#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "simulator.h"

// Reserve continuous memory blocks on Heap
Grid* create_grid(int height, int width)
{
    // Allocate memory for the Grid structure
    Grid *grid = (Grid *)malloc(sizeof(Grid));
    // Set the height and width of the grid
    grid->height = height;
    grid->width = width;
    // Calculate the total number of cells in the grid (height * width)
    int total_cells = height * width;

    // Allocate memory for the current grid, next grid, and days infected arrays
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

// Main loop: updates cells (Data parallelism / Stencil)
void update_grid(Grid *grid, float effective_beta, float excess_mortality_factor) 
{
    int height = grid->height;
    int width  = grid->width;

    // [ASM_LABEL] update_grid: outer loop over rows (i)
    __asm__ volatile("# =====================================================================");
    __asm__ volatile("# [update_grid] BEGIN: outer row loop (i = 0..height)");
    __asm__ volatile("# VECTORIZATION TARGET: inner j-loop over current_grid[] (stride-1, row-major)");
    __asm__ volatile("# BARRIER: rand() call and powf() prevent auto-vectorization at -O3");
    __asm__ volatile("# =====================================================================");

    // Iterate over each cell in the grid, first by row (i) then by column (j)
    for (int i = 0; i < height; i++) {
        for (int j = 0; j < width; j++) {
            // Linear index of the cell in the 1D array representation of the 2D grid and its current state
            int idx = i * width + j;
            int state = grid->current_grid[idx];

            if (state == SUSCEPTIBLE) {
                // [ASM_LABEL] SUSCEPTIBLE branch: Moore neighborhood scan
                __asm__ volatile("# --- [SUSCEPTIBLE] Moore neighborhood scan (di=-1..1, dj=-1..1) ---");

                // Count the number of infected residents in the Moore neighborhood (8 adjacent cells)
                int infected_residents = 0;

                // Scan the Moore neighborhood, d* = {-1, 0, 1} for both rows(i) and columns(j)
                // Gets if any of the 8 neighbors are infected, and counts them
                for (int di = -1; di <= 1; di++) {
                    for (int dj = -1; dj <= 1; dj++) {
                        if (di == 0 && dj == 0) continue; // Ignore central cell

                        // Compute neighbor coordinates, the pos of the cell + the offset
                        int ni = i + di;
                        int nj = j + dj;

                        // Check grid limits, and if the neighbor is infected, increment the counter
                        // ni * width + nj is the linear index of the neighbor
                        if (ni >= 0 && ni < height && nj >= 0 && nj < width)
                            if (grid->current_grid[ni * width + nj] == INFECTED) 
                                infected_residents++;
                    }
                }

                // [ASM_LABEL] Stochastic transition: Monte Carlo sampling
                __asm__ volatile("# --- [SUSCEPTIBLE] Stochastic Monte Carlo: powf() + rand() ---");

                // Stochastic transition based on the probability of the complementary event
                if (infected_residents > 0) {
                    float p_contagion = 1.0f - powf(1.0f - effective_beta, (float)infected_residents);
                    float r = (float)rand() / (float)RAND_MAX;

                    // If the random number is less than the contagion probability, the cell becomes infected
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
                // [ASM_LABEL] INFECTED branch: convalescence counter + recovery/death roll
                __asm__ volatile("# --- [INFECTED] Convalescence counter + death/recovery Monte Carlo ---");

                grid->days_infected[idx]++;

                // If the critical recovery period is exceeded
                if (grid->days_infected[idx] >= RECOVERY_DAYS) {
                    float p_death = BASE_DEATH_RATE * excess_mortality_factor;
                    float r = (float)rand() / (float)RAND_MAX;

                    // If the random number is less than the death probability, the cell dies; otherwise, it recovers
                    if (r < p_death) {
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

    __asm__ volatile("# [update_grid] END ===================================================");
}

// Swap the current and next grid buffers for the next iteration
// This is a simple pointer swap, no data is copied
// This makes the next grid become the current grid for the next time step, and vice versa
// The new current becomes a read-only buffer, and the new next becomes a write-only buffer and gets overwritten
void swap_buffer(Grid *grid)
{
    int *temp = grid->current_grid;
    grid->current_grid = grid->next_grid;
    grid->next_grid = temp;
}

// Count the number of cells in each state (S, I, R, D) in the current grid
void get_counts(const Grid *grid, int *num_S, int *num_I, int *num_R, int *num_D)
{
    *num_S = 0;
    *num_I = 0;
    *num_R = 0;
    *num_D = 0;

    // Total number of cells in the grid is the same as the size of the current_grid array, which is height * width
    int total_cells = grid->height * grid->width;

    // [ASM_LABEL] get_counts: reduction loop over current_grid[]
    __asm__ volatile("# =====================================================================");
    __asm__ volatile("# [get_counts] BEGIN: reduction loop (idx = 0..total_cells)");
    __asm__ volatile("# VECTORIZATION TARGET: simple switch/accumulator, no side effects");
    __asm__ volatile("# =====================================================================");

    for (int idx = 0; idx < total_cells; idx++) {
        switch (grid->current_grid[idx]) {
            case SUSCEPTIBLE: (*num_S)++; break;
            case INFECTED:    (*num_I)++; break;
            case RECOVERED:   (*num_R)++; break;
            case DEAD:        (*num_D)++; break;
        }
    }

    __asm__ volatile("# [get_counts] END ====================================================");
}