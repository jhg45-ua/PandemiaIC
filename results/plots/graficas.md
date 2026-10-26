# 📊 Origen de Datos y Trazabilidad de Gráficas para la Memoria
**Asignatura:** Ingeniería de los Computadores (Curso 2026-27)  
**Ubicación de imágenes:** `results/plots/`  
**Script generador:** `scripts/generate_plots.py`

---

## 📑 Índice de Trazabilidad por Figura

### Fig 01: `fig01_flags_speedup.png`
* **Sección recomendada:** Sección 7 (Opciones de Compilación)
* **Archivos fuente en `results/`:**
  * `results/flags/base.txt` (-O0)
  * `results/flags/01.txt` (-O1)
  * `results/flags/02.txt` (-O2)
  * `results/flags/Os.txt` (-Os)
  * `results/flags/03.txt` (-O3)
  * `results/flags/0fast.txt` (-Ofast)
* **Campos extraídos:** `Total Wall-Clock Time` (segundos).
* **Fórmulas aplicadas:** $Speedup = \frac{T_{-O0}}{T_{\text{opt}}}$.

---

### Fig 02: `fig02_flags_throughput_mcups.png`
* **Sección recomendada:** Sección 7 (Métricas de Rendimiento)
* **Archivos fuente en `results/`:**
  * `results/flags/{base, 01, 02, Os, 03, 0fast}.txt`
* **Campos extraídos:** `Kernel Throughput (MCUPS)` y `Macro Throughput` (sims/s).

---

### Fig 03: `fig03_profiling_phases_stacked.png`
* **Sección recomendada:** Sección 6 / 7 (Desglose de Profiling y Ley de Amdahl)
* **Archivos fuente en `results/`:**
  * `results/flags/{base, 01, 02, Os, 03, 0fast}.txt`
  * `results/lto/lto.txt`
  * `results/max_opt/max_opt.txt`
* **Campos extraídos:** Tabla `TOTAL PHASES`: Tiempos absolutos en segundos de `Update Grid`, `Get Counts` y `Analytics`.

---

### Fig 04: `fig04_advanced_opts_ablation.png`
* **Sección recomendada:** Sección 7 (Estudio de Flags Avanzados GCC)
* **Archivos fuente en `results/`:**
  * `results/march/03.txt`
  * `results/march/03+native.txt`
  * `results/march/03+native+fma.txt`
  * `results/unroll/unroll.txt`
  * `results/vector_width/w256.txt`
  * `results/vector_width/w512.txt`
  * `results/cost_model/cost_unlimited.txt`
  * `results/lto/lto.txt`
  * `results/max_opt/max_opt.txt`
  * `results/pgo/pgo.txt`
* **Campos extraídos:** `Total Wall-Clock Time` (s).

---

### Fig 05: `fig05_lto_impact_reduction_vs_stencil.png`
* **Sección recomendada:** Sección 7 (Análisis de LTO y Autovectorización)
* **Archivos fuente en `results/`:**
  * `results/march/03.txt`
  * `results/march/03+native.txt`
  * `results/unroll/unroll.txt`
  * `results/lto/lto.txt`
  * `results/max_opt/max_opt.txt`
* **Campos extraídos:** Tiempos específicos en segundos de `Get Counts` y `Update Grid`.

---

### Fig 06: `fig06_scalability_problem_size_memory.png`
* **Sección recomendada:** Sección 6 (Escalabilidad del Censo y Memoria)
* **Archivos fuente en `results/`:**
  * `results/size/ciudad.txt` (349k hab)
  * `results/size/provincia.txt` (2.0M hab)
  * `results/size/comunidad.txt` (5.1M hab)
* **Campos extraídos:** `Total Wall-Clock Time` (s) y `Kernel Throughput` (MCUPS).

---

### Fig 07: `fig07_pareto_epidemiological_tradeoff.png`
* **Sección recomendada:** Sección 3 (Caso de Prueba / Evaluación Epidemiológica)
* **Archivos fuente en `results/`:**
  * `results/flags/03.txt` (Bloques Monte Carlo de las 4 políticas)
* **Campos extraídos:** `Economic Cost (M€)` ($\mu \pm \sigma$) y `Total Deaths` ($\mu \pm \sigma$).

---

### Fig 08: `fig08_icu_collapse_and_fatigue.png`
* **Sección recomendada:** Sección 3 (Saturación Sanitaria y Sociedad)
* **Archivos fuente en `results/`:**
  * `results/flags/03.txt`
* **Campos extraídos:** `ICU Collapse Days` ($\mu \pm \sigma$) y `Mean Social Fatigue`.

---

### Fig 09: `fig09_compute_time_per_policy.png`
* **Sección recomendada:** Sección 6 (Carga de Cómputo por Dinámica)
* **Archivos fuente en `results/`:**
  * `results/flags/03.txt`
* **Campos extraídos:** `Total Compute Time` (s) de cada política para las 80 réplicas Monte Carlo.

---

### Fig 10: `fig10_multiscale_policy_impact.png`
* **Sección recomendada:** Sección 6 (Estabilidad Multiescala)
* **Archivos fuente en `results/`:**
  * `results/size/ciudad.txt`
  * `results/size/provincia.txt`
  * `results/size/comunidad.txt`
* **Campos extraídos:** Medias de coste económico y mortalidad por política en cada escala geográfica.

---

### Fig 11: `fig11_speedup_by_kernel_component.png`
* **Sección recomendada:** Sección 7 (Aceleración Diferencial por Función)
* **Archivos fuente en `results/`:**
  * `results/flags/{base, 01, 02, Os, 03, 0fast}.txt`
  * `results/lto/lto.txt`
  * `results/max_opt/max_opt.txt`
* **Cálculo:** Speedups parciales individuales:
  $$S_{\text{UpdateGrid}} = \frac{T_{\text{UpdateGrid, O0}}}{T_{\text{UpdateGrid, opt}}}, \quad S_{\text{GetCounts}} = \frac{T_{\text{GetCounts, O0}}}{T_{\text{GetCounts, opt}}}$$

---

### Fig 12: `fig12_memory_hierarchy_working_set.png`
* **Sección recomendada:** Sección 5 / 6 (Jerarquía de Caché)
* **Archivos fuente en `results/`:** Geometría de malla de `results/size/{ciudad, provincia, comunidad}.txt`.
* **Cálculo de arquitectura:**
  * 1 Buffer entero = $N \times 4\text{ Bytes}$.
  * Working Set activo (3 arrays) = $N \times 12\text{ Bytes}$.
  * Umbrales de hardware Intel Core i5-12400: L1d (288 KiB), L2 (7.5 MiB), L3 (18.0 MiB).

---

### Fig 13: `fig13_policy_phase_disparity.png`
* **Sección recomendada:** Sección 6 (Disparidad Temporal de Fases)
* **Archivos fuente en `results/`:**
  * `results/flags/03.txt` (Sección `POLICY_PHASES`)
* **Campos extraídos:** Tiempos en segundos de `Update Grid` vs `Get Counts` para cada una de las 4 políticas sanitarias.

---

### Fig 14: `fig14_amdahl_parallel_projection.png`
* **Sección recomendada:** Sección 8 / 9 (Proyección Paralela Futura)
* **Archivos fuente en `results/`:** Fracciones secuenciales $f$ medidas en `results/flags/03.txt` ($f = 0.7321$) y `results/lto/lto.txt` ($f = 0.9661$).
* **Fórmula:** Ley de Amdahl:
  $$S(p) = \frac{1}{(1-f) + \frac{f}{p}}$$
  para $p \in [1, 64]$ Threads.

---

### Fig 15: `fig15_monte_carlo_dispersion_ranges.png`
* **Sección recomendada:** Sección 3 / 6 (Estadística Monte Carlo)
* **Archivos fuente en `results/`:**
  * `results/flags/03.txt`
* **Campos extraídos:** Media ($\mu$), Desviación típica ($\sigma$), Rango Mínimo y Máximo de fallecidos en 80 réplicas.

---

### Fig 16: `fig16_roofline_model.png`
* **Sección recomendada:** Sección 7 (Modelo Roofline de Arquitectura)
* **Archivos fuente en `results/`:**
  * `results/flags/03.txt` (Throughput: 519.07 MCUPS).
* **Parámetros de hardware y código:**
  * Ancho de banda de memoria DDR4 i5-12400: 38 GB/s. Pico teórico FP32: 96 GFLOPS.
  * Intensidad aritmética: `get_counts` $\approx 0.056\text{ FLOP/Byte}$, `update_grid` $\approx 0.300\text{ FLOP/Byte}$. Ambos caen en la zona *Memory-Bound*.

---

### Fig 17: `fig17_vectorization_analysis.png`
* **Sección recomendada:** Sección 7 (Evidencias de Autovectorización SIMD)
* **Archivos fuente en `results/`:**
  * Diagnóstico del compilador GCC (`results/vec_report/vec_report.txt` / `-fopt-info-vec-all`).
* **Datos:** % de bucle vectorizado por SIMD/SLP (`update_grid`: 0% por barreras de memoria de `rand()` y `powf()`; `get_counts`: 15% SLP).

---

### Fig 18: `fig18_lto_speedup_per_policy.png`
* **Sección recomendada:** Sección 7 (Impacto Diferencial de LTO)
* **Archivos fuente en `results/`:**
  * `results/flags/03.txt` vs `results/lto/lto.txt`
* **Campos extraídos:** Tiempos por política para calcular el Speedup de la política completa vs el Speedup exclusivo de `get_counts`.

---

### Fig 19: `fig19_spatial_locality_cache.png`
* **Sección recomendada:** Sección 5 / 6 (Localidad Espacial)
* **Archivos fuente en `results/`:**
  * `results/size/ciudad.txt`, `provincia.txt`, `comunidad.txt`
* **Campos extraídos:** MCUPS medidos (475.1, 484.6, 464.8) y Working Set ($N \times 9\text{ Bytes/celda}$) frente a los límites L1d/L2/L3.

---

### Fig 20: `fig20_energy_efficiency.png`
* **Sección recomendada:** Sección 7 (Sostenibilidad y Eficiencia Energética)
* **Archivos fuente en `results/`:**
  * `results/flags/{base, 01, 02, 03}.txt`, `results/march/03+native.txt`, `results/lto/lto.txt`, `results/max_opt/max_opt.txt`.
* **Fórmula:** Energía relativa $E = T_{\text{wall}} \times 65\text{ W}$ (TDP i5-12400), normalizada respecto a `-O0`.

---

### Fig 21: `fig21_arithmetic_intensity.png`
* **Sección recomendada:** Sección 7 (Análisis de Código C)
* **Archivos fuente en `results/`:** Análisis del código fuente `src/simulator.c`.
* **Cálculo:** Intensidad Aritmética ($\text{AI} = \frac{\text{FLOPs}}{\text{Bytes accedidos}}$) por cada rama condicional del autómata frente al *Ridge Point* (2.53 FLOP/B).

---

### Fig 22: `fig22_scaling_projection.png`
* **Sección recomendada:** Sección 6 (Proyección de Escala Nacional)
* **Archivos fuente en `results/`:**
  * `results/size/ciudad.txt`, `provincia.txt`, `comunidad.txt`
* **Método:** Ajuste en escala logarítmica $\log_{10}(T) = b \cdot \log_{10}(N) + c$ (Pendiente $b = 1.06$, cuasi-lineal) para proyectar la ejecución a escala España (~47M hab).

---

### Fig 23: `fig23_full_optimization_pipeline.png`
* **Sección recomendada:** Sección 7 (Pipeline Completo de Optimización)
* **Archivos fuente en `results/` (lectura directa y automatizada de 16 ficheros):**
  1. `results/flags/base.txt` (-O0)
  2. `results/flags/01.txt` (-O1)
  3. `results/flags/02.txt` (-O2)
  4. `results/flags/Os.txt` (-Os)
  5. `results/flags/03.txt` (-O3)
  6. `results/flags/0fast.txt` (-Ofast)
  7. `results/march/03+native.txt`
  8. `results/march/03+native+fma.txt`
  9. `results/unroll/unroll.txt`
  10. `results/vector_width/w256.txt`
  11. `results/vector_width/w512.txt`
  12. `results/cost_model/cost_unlimited.txt`
  13. `results/simd/vec.txt`
  14. `results/pgo/pgo.txt`
  15. `results/lto/lto.txt`
  16. `results/max_opt/max_opt.txt`
* **Campos extraídos:** `Total Wall-Clock Time` y `Kernel Throughput (MCUPS)`, ordenados en orden ascendente por rendimiento.