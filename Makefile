# Compiler & Standards

# GCC -> Linux
# Clang -> MacOS

CC			:= gcc
MPICC		:= mpicc
CFLAGS		:= -Wall -Wextra -Werror -std=c11
# Optimization flags, such as -OX or -march=native
OPTFLAGS	:= -O0

# Flags for autovectorization, such as -ftree-vectorize or -fopt-info-vec
VECFLAGS := -fopt-info-vec-all=build/vec_report.txt

# Project dirs
SRC_DIR		:= src
INC_DIR		:= include
BUILD_DIR	:= build
ASM_DIR		:= $(BUILD_DIR)/asm
BIN_DIR		:= bin

# Exec name
TARGET		:= $(BIN_DIR)/sim
TARGET_MPI	:= $(BIN_DIR)/sim_mpi

# Source & Object files
SRCS		:= $(wildcard $(SRC_DIR)/*.c)
OBJS		:= $(patsubst $(SRC_DIR)/%.c, $(BUILD_DIR)/%.o, $(SRCS))

# Headers
INCLUDES	:= -I $(INC_DIR)

# Sim parameters
CONFIG_FILE	:= config/policies.conf
N_HAB		:= 100000 # 100,000 Inhabitants
DAYS		:= 150    # 150 Days
N_SIM		:= 80     # 80 Monte Carlo Replicas per policy

.PHONY: all asm run run-provincia run-comunidad clean help vectorization

all: $(TARGET)

all_mpi: $(TARGET_MPI)

$(TARGET): $(OBJS) | $(BIN_DIR)
	$(CC) $(CFLAGS) $(OPTFLAGS) $(OBJS) -o $@ -lm
	@echo "Build complete: $(TARGET)"

$(TARGET_MPI): $(OBJS) | $(BIN_DIR)
	$(MPICC) $(CFLAGS) $(OPTFLAGS) $(OBJS) -o $@ -lm
	@echo "Build complete: $(TARGET_MPI)"

# Rule to compile source files into object files (.c -> .o).
# Each compilation also generates an annotated assembly listing (.s) in build/asm/
# so the compiler-generated code can be inspected for vectorization, inlining, etc.
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c | $(BUILD_DIR) $(ASM_DIR)
	$(MPICC) $(CFLAGS) $(OPTFLAGS) $(INCLUDES) -c $< -o $@
	$(MPICC) $(CFLAGS) $(OPTFLAGS) $(INCLUDES) -S -fverbose-asm $< -o $(ASM_DIR)/$(*F).s

# Create output dirs if they don't exist
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(ASM_DIR):
	mkdir -p $(ASM_DIR)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

# Run the default city-scale simulation
run: $(TARGET)
	@./scripts/run_ciudad.sh

run-provincia: $(TARGET)
	@./scripts/run_provincia.sh

run-comunidad: $(TARGET)
	@./scripts/run_comunidad.sh

run-mpi: $(TARGET_MPI)
	@mpirun -np 4 ./bin/sim_mpi config/policies.conf $(N_HAB) $(DAYS) 10 $(N_SIM) 29

# Standalone target: regenerate all .s files without touching the .o / binary.
# Supports overriding OPTFLAGS from the CLI, e.g.:
#   make asm OPTFLAGS=-O3
#   make asm OPTFLAGS="-O2 -march=native"
asm: | $(ASM_DIR)
	@echo "Generating annotated assembly [OPTFLAGS=$(OPTFLAGS)] -> $(ASM_DIR)/"
	@for src in $(SRCS); do \
		base=$$(basename $$src .c); \
		$(CC) $(CFLAGS) $(OPTFLAGS) $(INCLUDES) -S -fverbose-asm $$src -o $(ASM_DIR)/$$base.s; \
		echo "  $$src  ->  $(ASM_DIR)/$$base.s"; \
	done
	@echo "Done. Files in $(ASM_DIR)/:"
	@ls -lh $(ASM_DIR)/

# Rule to compile with vectorization flags
vectorization: clean
	$(MAKE) CFLAGS="$(CFLAGS) $(VECFLAGS)" OPTFLAGS="$(OPTFLAGS)" all

# Rule to clean up build artifacts
clean:
	@echo "Cleaning up build artifacts..."
	rm -rf $(BUILD_DIR) $(BIN_DIR)

help:
	@echo "Available commands:"
	@echo "  make                        - Compile the project (-O0) + generate build/asm/*.s"
	@echo "  make asm                    - (Re)generate assembly only, with current OPTFLAGS"
	@echo "  make asm OPTFLAGS=-O3       - Generate assembly at a specific optimization level"
	@echo "  make run                    - Execute Alicante City scale (~350k hab)"
	@echo "  make run-provincia          - Execute Alicante Province scale (~2.0M hab)"
	@echo "  make run-comunidad          - Execute Comunitat Valenciana scale (~5.1M hab)"
	@echo "  make vectorization          - Compile with vectorization flags and reports"
	@echo "  make clean                  - Remove build artifacts and binaries"