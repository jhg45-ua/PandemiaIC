#ifndef SIMULATOR_H
#define SIMULATOR_H

#include "policy.h"

// Population/grid structure with double-buffered plane
typedef struct
{
    int height;             // Map rows
    int width;              // Map columns
    int *current_grid;      // Read buffer at time t (size height*width)
    int *next_grid;         // Write buffer at time t+1 (size height*width)
    int *days_infected;     // Number of days each cell has been infected
} Grid;

// Core functions prototypes
Grid* create_grid(int height, int width);
void destroy_grid(Grid *grid);
void init_population(Grid *grid, int initial_infected);
void update_grid(Grid *grid, float effective_beta, float excess_mortality_factor);
void swap_buffer(Grid *grid);
void get_counts(const Grid *grid, int *num_S, int *num_I, int *num_R, int *num_D);


#endif // SIMULATOR_H