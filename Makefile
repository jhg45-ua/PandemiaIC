# Compiler & Standards

# GCC -> Linux
# Clang -> MacOS

CC 			:= gcc
CFLAGS 		:= -Wall -Wextra -Werror -std=c11
# Optimization flags, such as -OX or -march=native
OPTFLAGS 	:= -O0

# Flags for autovectorization, such as -ftree-vectorize or -fopt-info-vec
# VECFLAGS := -fopt-info-vec-optimized -fopt-info-vec-missed -fopt-info-vec-all

# Projects dirs
SRC_DIR 	:= src
INC_DIR 	:= include
BUILD_DIR 	:= build
BIN_DIR 	:= bin

# Exec Name
TARGET 	:= $(BIN_DIR)/sim

# Source & Object files
SRCS 		:= $(wildcard $(SRC_DIR)/*.c)
OBJS 		:= $(patsubst $(SRC_DIR)/%.c, $(BUILD_DIR)/%.o,$(SRCS))

# Headers
INCLUDES 	:= -I $(INC_DIR)

# Sim parameters
CONFIG_FILE := config/policies.conf
N_HAB		:= 100000 # 100,000 Inhabitants
DAYS		:= 150 # 150 Days

.PHONY: all run clean help vectorization

all: $(TARGET)

$(TARGET): $(OBJS) | $(BIN_DIR)
	$(CC) $(CFLAGS) $(OPTFLAGS) $(OBJS) -o $@ -lm
	@echo "Build complete: $(TARGET)"

# Rule to compile source files into object files (.c -> .o)
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(OPTFLAGS) $(INCLUDES) -c $< -o $@

# Create output dirs if they don't exist
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

# Run the simulation with the specified parameters
run: $(TARGET)
	@echo "Running simulation with $(N_HAB) inhabitants for $(DAYS) days..."
	@./$(TARGET) $(CONFIG_FILE) $(N_HAB) $(DAYS)

# Rule to compile with vectorization flags
# vectorization: clean
# 	$(MAKE) CFLAGS="$(CFLAGS) $(VECFLAGS)" OPTFLAGS="$(OPTFLAGS)" all

# Rule to clean up build artifacts
clean:
	@echo "Cleaning up build artifacts..."
	rm -rf $(BUILD_DIR) $(BIN_DIR)

help:
	@echo "Available commands:"
	@echo "  make              	- Compile the project with base options (-O0)"
	@echo "  make run          	- Execute the simulation with the specified parameters"
# 	@echo "  make vectorization	- Compile with -O3 -mavx2 and SIMD analyzer report"
	@echo "  make clean       	- Remove build artifacts and binaries"