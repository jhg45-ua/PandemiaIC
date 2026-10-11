#!/usr/bin/env python3
"""
Script de generación de gráficas científicas para la Memoria de Práctica 2
Ingeniería de los Computadores - Curso 2026-27 (Universidad de Alicante)
Genera 15 figuras de alta resolución (300 DPI) a partir de los datos en results/
"""

import os
import re
import numpy as np
import matplotlib.pyplot as plt

# Directorio de salida
OUTPUT_DIR = "results/plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configuración estética general
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14,
    'axes.edgecolor': '#cccccc',
    'axes.linewidth': 0.8,
    'grid.color': '#e0e0e0',
    'grid.linestyle': '--',
    'grid.alpha': 0.7
})

# ==============================================================================
# 1. PARSING DE DATOS
# ==============================================================================

def parse_benchmark_file(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    wall_m = re.search(r'Total Wall-Clock Time:\s+([\d\.]+)\s+s', content)
    mcups_m = re.search(r'Kernel Throughput \(MCUPS\):\s+([\d\.]+)', content)
    macro_m = re.search(r'Macro Throughput\s+:\s+([\d\.]+)\s+simulations', content)
    phases_m = re.search(
        r'TOTAL PHASES\s+\|\s+([\d\.]+)\s+s\s+\|\s+([\d\.]+)\s+s\s+\(([\d\.]+)%\)\s+\|\s+([\d\.]+)\s+s\s+\(([\d\.]+)%\)\s+\|\s+([\d\.]+)\s+s\s+\(([\d\.]+)%\)',
        content
    )

    policies = re.findall(
        r'=== Policy:\s+(\w+)\s+===\s+'
        r'Economic Cost \(M€\)\s+:\s+([\d\.]+)\s+±\s+([\d\.]+)\s+M€\s+'
        r'Total Deaths\s+:\s+([\d\.]+)\s+±\s+([\d\.]+)\s+people\s+\[Range:\s+(\d+)\s+-\s+(\d+)\]\s+'
        r'ICU Collapse Days\s+:\s+([\d\.]+)\s+±\s+([\d\.]+)\s+days\s+'
        r'Mean Social Fatigue:\s+([\d\.]+)\s+'
        r'Total Compute Time\s+:\s+([\d\.]+)\s+s',
        content
    )

    phases_pol = re.findall(
        r'(\w+)\s+\|\s+([\d\.]+)\s+s\s+\|\s+([\d\.]+)\s+s\s+\(([\d\.]+)%\)\s+\|\s+([\d\.]+)\s+s\s+\(([\d\.]+)%\)\s+\|\s+([\d\.]+)\s+s\s+\(([\d\.]+)%\)',
        content
    )

    pol_phases_dict = {}
    for row in phases_pol:
        if row[0] not in ['PHASES', 'Policy']:
            pol_phases_dict[row[0]] = {
                'total_s': float(row[1]),
                'update_s': float(row[2]),
                'update_pct': float(row[3]),
                'counts_s': float(row[4]),
                'counts_pct': float(row[5]),
                'analytics_s': float(row[6]),
                'analytics_pct': float(row[7])
            }

    return {
        'wall_s': float(wall_m.group(1)) if wall_m else None,
        'mcups': float(mcups_m.group(1)) if mcups_m else None,
        'macro_sims_s': float(macro_m.group(1)) if macro_m else None,
        'total_phases_s': float(phases_m.group(1)) if phases_m else None,
        'update_grid_s': float(phases_m.group(2)) if phases_m else None,
        'update_grid_pct': float(phases_m.group(3)) if phases_m else None,
        'get_counts_s': float(phases_m.group(4)) if phases_m else None,
        'get_counts_pct': float(phases_m.group(5)) if phases_m else None,
        'analytics_s': float(phases_m.group(6)) if phases_m else None,
        'analytics_pct': float(phases_m.group(7)) if phases_m else None,
        'policies': {
            p[0]: {
                'cost_mean': float(p[1]), 'cost_std': float(p[2]),
                'deaths_mean': float(p[3]), 'deaths_std': float(p[4]),
                'deaths_min': int(p[5]), 'deaths_max': int(p[6]),
                'icu_mean': float(p[7]), 'icu_std': float(p[8]),
                'fatigue': float(p[9]),
                'compute_time_s': float(p[10])
            } for p in policies
        },
        'policy_phases': pol_phases_dict
    }

# ==============================================================================
# FIG 1: FLAGS DE COMPILACIÓN - TIEMPO WALL-CLOCK Y SPEEDUP RESPECTO A -O0
# (Etiqueta debajo del punto rojo)
# ==============================================================================
def plot_fig1_flags_speedup():
    flags = ['-O0\n(base)', '-O1', '-O2', '-Os', '-O3', '-Ofast']
    files = ['results/flags/base.txt', 'results/flags/01.txt', 'results/flags/02.txt',
             'results/flags/Os.txt', 'results/flags/03.txt', 'results/flags/0fast.txt']
    
    times = []
    for f in files:
        data = parse_benchmark_file(f)
        times.append(data['wall_s'])
    
    t_base = times[0]
    speedups = [t_base / t for t in times]

    fig, ax1 = plt.subplots(figsize=(8.5, 4.8))
    x = np.arange(len(flags))
    width = 0.55

    # Barras de tiempo
    colors = ['#7f8c8d', '#3498db', '#2980b9', '#e67e22', '#27ae60', '#16a085']
    bars = ax1.bar(x, times, width, color=colors, alpha=0.88, edgecolor='black', linewidth=0.8, zorder=3)
    ax1.set_ylabel('Tiempo Wall-Clock Total (s)', fontsize=12, fontweight='bold', color='#2c3e50')
    ax1.set_xlabel('Nivel de Optimización GCC', fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(flags, fontsize=10, fontweight='bold')
    ax1.set_ylim(0, max(times) * 1.15)

    # Valores sobre barras
    for bar in bars:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., h + 4, f"{h:.1f} s",
                 ha='center', va='bottom', fontsize=9.5, fontweight='bold', color='#2c3e50')

    # Eje secundario para Speedup
    ax2 = ax1.twinx()
    ax2.plot(x, speedups, color='#c0392b', marker='o', linewidth=2.4, markersize=7, zorder=4, label='Speedup respecto a -O0')
    ax2.set_ylabel('Speedup (Ganancia en Velocidad)', fontsize=12, fontweight='bold', color='#c0392b')
    ax2.set_ylim(-0.3, max(speedups) * 1.25)
    ax2.grid(False)

    # Etiquetas DEBAJO del punto rojo (-22 puntos hacia abajo)
    for i, s in enumerate(speedups):
        ax2.annotate(f"{s:.2f}x", (x[i], s), textcoords="offset points", xytext=(0, -22),
                     ha='center', va='top', fontsize=9.5, fontweight='bold', color='#c0392b',
                     bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#c0392b', alpha=0.9))

    plt.title('Impacto de los Niveles de Optimización GCC en el Tiempo y Speedup (Caso Ciudad, 200 días)',
              fontsize=12, fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig01_flags_speedup.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 2: THROUGHPUT DEL KERNEL (MCUPS) Y MACRO THROUGHPUT (SIMS/S)
# ==============================================================================
def plot_fig2_flags_throughput():
    flags = ['-O0', '-O1', '-O2', '-Os', '-O3', '-Ofast']
    files = ['results/flags/base.txt', 'results/flags/01.txt', 'results/flags/02.txt',
             'results/flags/Os.txt', 'results/flags/03.txt', 'results/flags/0fast.txt']
    
    mcups = []
    sims = []
    for f in files:
        data = parse_benchmark_file(f)
        mcups.append(data['mcups'])
        sims.append(data['macro_sims_s'])

    x = np.arange(len(flags))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(8.5, 4.8))
    bars1 = ax1.bar(x - width/2, mcups, width, label='Throughput Kernel (MCUPS)', color='#2980b9', edgecolor='black', linewidth=0.8)
    ax1.set_ylabel('Throughput del Kernel (MCUPS - Millones Celdas/s)', fontsize=11, fontweight='bold', color='#2980b9')
    ax1.set_xlabel('Nivel de Optimización GCC', fontsize=11, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(flags, fontweight='bold')
    ax1.set_ylim(0, max(mcups) * 1.2)

    for bar in bars1:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., h + 10, f"{h:.1f}",
                 ha='center', va='bottom', fontsize=9, fontweight='bold', color='#2980b9')

    ax2 = ax1.twinx()
    bars2 = ax2.bar(x + width/2, sims, width, label='Macro Throughput (sims/s)', color='#e67e22', edgecolor='black', linewidth=0.8)
    ax2.set_ylabel('Throughput Macro (Simulaciones Monte Carlo / s)', fontsize=11, fontweight='bold', color='#e67e22')
    ax2.set_ylim(0, max(sims) * 1.25)
    ax2.grid(False)

    for bar in bars2:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., h + 0.15, f"{h:.2f}",
                 ha='center', va='bottom', fontsize=9, fontweight='bold', color='#d35400')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True)

    plt.title('Rendimiento del Kernel (MCUPS) y Productividad Global por Nivel de Optimización',
              fontsize=12, fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig02_flags_throughput_mcups.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 3: DESGLOSE APILADO DEL TIEMPO POR FASES (LEY DE AMDAHL)
# ==============================================================================
def plot_fig3_profiling_phases_stacked():
    configs = ['-O0', '-O1', '-O2', '-Os', '-O3', '-Ofast', '-flto\n(-O3+native)', 'max_opt\n(-Ofast+lto)']
    files = ['results/flags/base.txt', 'results/flags/01.txt', 'results/flags/02.txt',
             'results/flags/Os.txt', 'results/flags/03.txt', 'results/flags/0fast.txt',
             'results/lto/lto.txt', 'results/max_opt/max_opt.txt']
    
    t_update = []
    t_counts = []
    t_analytics = []

    for f in files:
        data = parse_benchmark_file(f)
        t_update.append(data['update_grid_s'])
        t_counts.append(data['get_counts_s'])
        t_analytics.append(data['analytics_s'])

    x = np.arange(len(configs))
    width = 0.55

    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    p1 = ax.bar(x, t_update, width, label='Update Grid (Propagación Stencil 2D)', color='#3498db', edgecolor='black', linewidth=0.7)
    p2 = ax.bar(x, t_counts, width, bottom=t_update, label='Get Counts (Reducción Censo SIRD)', color='#e74c3c', edgecolor='black', linewidth=0.7)
    bottom_analytics = np.array(t_update) + np.array(t_counts)
    p3 = ax.bar(x, t_analytics, width, bottom=bottom_analytics, label='Analytics (Módulos Sanitario/Eco/Soc)', color='#2ecc71', edgecolor='black', linewidth=0.7)

    totals = bottom_analytics + np.array(t_analytics)
    for i, t in enumerate(totals):
        pct_u = (t_update[i] / t) * 100
        pct_c = (t_counts[i] / t) * 100
        ax.text(x[i], t + 4, f"{t:.1f} s", ha='center', va='bottom', fontsize=9, fontweight='bold')
        if t > 60:
            ax.text(x[i], t_update[i]/2, f"{pct_u:.0f}%", ha='center', va='center', color='white', fontweight='bold', fontsize=8.5)
            if t_counts[i] > 10:
                ax.text(x[i], t_update[i] + t_counts[i]/2, f"{pct_c:.0f}%", ha='center', va='center', color='white', fontweight='bold', fontsize=8.5)

    ax.set_ylabel('Tiempo Acumulado de Ejecución (s)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Configuración de Compilación', fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(configs, fontsize=9.5, fontweight='bold')
    ax.set_ylim(0, max(totals) * 1.15)
    ax.legend(loc='upper right', frameon=True)

    plt.title('Desglose Temporal por Fases del Kernel y Demostración de la Ley de Amdahl',
              fontsize=12, fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig03_profiling_phases_stacked.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 4: ABLACIÓN DE OPTIMIZACIONES AVANZADAS (LTO, ARCH, UNROLL, PGO)
# ==============================================================================
def plot_fig4_advanced_opts():
    experiments = [
        ('-O3 Baseline', 'results/march/03.txt'),
        ('-O3 + march=native', 'results/march/03+native.txt'),
        ('-O3 + native + mfma', 'results/march/03+native+fma.txt'),
        ('-O3 + native + funroll-loops', 'results/unroll/unroll.txt'),
        ('-O3 + native + vector-width=256', 'results/vector_width/w256.txt'),
        ('-O3 + native + vector-width=512', 'results/vector_width/w512.txt'),
        ('-O3 + native + cost-unlimited', 'results/cost_model/cost_unlimited.txt'),
        ('-O3 + native + flto (LTO)', 'results/lto/lto.txt'),
        ('max_opt (-Ofast+lto+unroll)', 'results/max_opt/max_opt.txt'),
        ('PGO (-fprofile-use)', 'results/pgo/pgo.txt'),
    ]

    names = [e[0] for e in experiments]
    times = [parse_benchmark_file(e[1])['wall_s'] for e in experiments]
    
    colors = []
    for n in names:
        if 'flto' in n or 'max_opt' in n:
            colors.append('#27ae60')
        elif 'PGO' in n:
            colors.append('#e74c3c')
        elif 'Baseline' in n:
            colors.append('#34495e')
        else:
            colors.append('#3498db')

    fig, ax = plt.subplots(figsize=(9.8, 5.5))
    y = np.arange(len(names))
    bars = ax.barh(y, times, height=0.62, color=colors, edgecolor='black', linewidth=0.7)

    ax.set_xlabel('Tiempo Wall-Clock Total (s) - [Menor es mejor]', fontsize=11, fontweight='bold')
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9.5, fontweight='bold')
    ax.invert_yaxis()
    ax.set_xlim(0, max(times) * 1.15)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 1.2, bar.get_y() + bar.get_height()/2., f"{w:.2f} s",
                ha='left', va='center', fontsize=9.5, fontweight='bold', color='#2c3e50')

    ax.axvline(times[0], color='#e67e22', linestyle='--', linewidth=1.5, label=f'Baseline -O3 ({times[0]:.1f} s)')
    ax.legend(loc='lower right', frameon=True)

    plt.title('Ablación de Técnicas Avanzadas de Compilación en GCC 13.2 (Intel Core i5-12400)',
              fontsize=12, fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig04_advanced_opts_ablation.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 5: IMPACTO QUIRÚRGICO DE LTO EN GET_COUNTS (REDUCCIÓN 14x)
# ==============================================================================
def plot_fig5_lto_impact():
    cases = [
        '-O3 Baseline',
        '-O3 + march=native',
        '-O3 + native + funroll',
        '-O3 + native + flto (LTO)',
        'max_opt (-Ofast + lto)'
    ]
    files = [
        'results/march/03.txt',
        'results/march/03+native.txt',
        'results/unroll/unroll.txt',
        'results/lto/lto.txt',
        'results/max_opt/max_opt.txt'
    ]

    t_counts = []
    t_update = []
    for f in files:
        d = parse_benchmark_file(f)
        t_counts.append(d['get_counts_s'])
        t_update.append(d['update_grid_s'])

    x = np.arange(len(cases))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.8))

    colors_c = ['#e74c3c', '#e74c3c', '#e74c3c', '#27ae60', '#27ae60']
    bars_c = ax1.bar(x, t_counts, width=0.55, color=colors_c, edgecolor='black', linewidth=0.8)
    ax1.set_ylabel('Tiempo en get_counts() (s)', fontsize=11, fontweight='bold', color='#c0392b')
    ax1.set_xticks(x)
    ax1.set_xticklabels(cases, rotation=25, ha='right', fontsize=9, fontweight='bold')
    ax1.set_title('A: Tiempo en get_counts() (Reducción)', fontsize=11, fontweight='bold')
    ax1.set_ylim(0, max(t_counts) * 1.2)

    for bar in bars_c:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., h + 0.5, f"{h:.2f} s",
                 ha='center', va='bottom', fontsize=9, fontweight='bold')
        
    ax1.annotate('Aceleración de 13.8x\npor inlining inter-modular',
                 xy=(3, t_counts[3]), xytext=(2.2, 12),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                 fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#d4efdf', edgecolor='#27ae60'))

    colors_u = ['#3498db', '#3498db', '#3498db', '#2980b9', '#2980b9']
    bars_u = ax2.bar(x, t_update, width=0.55, color=colors_u, edgecolor='black', linewidth=0.8)
    ax2.set_ylabel('Tiempo en update_grid() (s)', fontsize=11, fontweight='bold', color='#2980b9')
    ax2.set_xticks(x)
    ax2.set_xticklabels(cases, rotation=25, ha='right', fontsize=9, fontweight='bold')
    ax2.set_title('B: Tiempo en update_grid() (Barrera rand/pow)', fontsize=11, fontweight='bold')
    ax2.set_ylim(0, max(t_update) * 1.15)

    for bar in bars_u:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., h + 0.8, f"{h:.1f} s",
                 ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.suptitle('Efecto Quirúrgico de LTO (-flto): Inlining Intermodular en Reducciones vs Stencil Estocástico',
                 fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig05_lto_impact_reduction_vs_stencil.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 6: ESCALABILIDAD TEMPORAL Y JERARQUÍA DE MEMORIA (CIUDAD, PROVINCIA, COMUNIDAD)
# ==============================================================================
def plot_fig6_scalability_memory():
    scales = ['Ciudad\n(Alicante)', 'Provincia\n(Alicante)', 'Comunitat\nValenciana']
    files = ['results/size/ciudad.txt', 'results/size/provincia.txt', 'results/size/comunidad.txt']
    
    pops = [349281, 1999396, 5098564]
    times = []
    mcups = []

    for f in files:
        d = parse_benchmark_file(f)
        times.append(d['wall_s'])
        mcups.append(d['mcups'])

    fig, ax1 = plt.subplots(figsize=(8.8, 5.0))
    x = np.arange(len(scales))

    color_time = '#2c3e50'
    bars = ax1.bar(x - 0.18, times, width=0.36, color='#34495e', edgecolor='black', linewidth=0.8, label='Tiempo Total (s)')
    ax1.set_ylabel('Tiempo Wall-Clock Total (s)', fontsize=11, fontweight='bold', color=color_time)
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"{scales[i]}\n({pops[i]:,} celdas)" for i in range(3)], fontsize=9.5, fontweight='bold')
    ax1.set_ylim(0, max(times) * 1.15)

    for bar in bars:
        h = bar.get_height()
        minutes = h / 60
        txt = f"{h:.1f} s\n({minutes:.1f} min)" if minutes >= 1 else f"{h:.1f} s"
        ax1.text(bar.get_x() + bar.get_width()/2., h + 15, txt,
                 ha='center', va='bottom', fontsize=8.5, fontweight='bold', color=color_time)

    ax2 = ax1.twinx()
    color_mcups = '#27ae60'
    ax2.plot(x + 0.18, mcups, color=color_mcups, marker='s', markersize=8, linewidth=2.2, label='Throughput Kernel (MCUPS)')
    ax2.set_ylabel('Throughput del Kernel (MCUPS)', fontsize=11, fontweight='bold', color=color_mcups)
    ax2.set_ylim(400, 520)
    ax2.grid(False)

    for i, m in enumerate(mcups):
        ax2.annotate(f"{m:.1f} MCUPS", (x[i] + 0.18, m), textcoords="offset points", xytext=(0, 10),
                     ha='center', fontsize=9.5, fontweight='bold', color=color_mcups,
                     bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=color_mcups, alpha=0.9))

    ax2.annotate('Huella de memoria: 20.4 MB\nSupera Caché L3 (18 MB)\n→ Caída en MCUPS por fallos de capacidad',
                 xy=(2 + 0.18, mcups[2]), xytext=(1.2, 430),
                 arrowprops=dict(facecolor='#c0392b', shrink=0.08, width=1.2, headwidth=6),
                 fontsize=8.5, fontweight='bold', color='#c0392b',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='#fadbd8', edgecolor='#c0392b'))

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True)

    plt.title('Escalabilidad del Censo y Comportamiento Frente a la Jerarquía de Caché L1/L2/L3',
              fontsize=12, fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig06_scalability_problem_size_memory.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 7: FRONTERA DE PARETO (COSTE ECONÓMICO VS FALLECIDOS POR POLÍTICA)
# ==============================================================================
def plot_fig7_pareto_frontier():
    data = parse_benchmark_file('results/flags/03.txt')['policies']
    
    policies = ['LaissezFaire', 'RemoteWork', 'DynamicSignals', 'Lockdown']
    colors = {'LaissezFaire': '#e74c3c', 'RemoteWork': '#f39c12', 'DynamicSignals': '#3498db', 'Lockdown': '#8e44ad'}

    fig, ax = plt.subplots(figsize=(8.8, 5.2))

    for p in policies:
        d = data[p]
        ax.errorbar(d['cost_mean'], d['deaths_mean'],
                    xerr=d['cost_std'], yerr=d['deaths_std'],
                    fmt='o', markersize=9, color=colors[p], ecolor=colors[p], elinewidth=1.6, capsize=4,
                    label=f"{p} (μ ± σ)", zorder=4)
        
        offset_y = 60 if p != 'DynamicSignals' else -90
        offset_x = 30
        ax.annotate(f"{p}\nCoste: {d['cost_mean']:.0f} M€\nMuertes: {d['deaths_mean']:.0f}",
                    (d['cost_mean'], d['deaths_mean']),
                    textcoords="offset points", xytext=(offset_x, offset_y),
                    ha='left', va='center', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=colors[p], alpha=0.9),
                    arrowprops=dict(arrowstyle='->', color=colors[p], lw=1.2))

    pareto_x = [data['LaissezFaire']['cost_mean'], data['RemoteWork']['cost_mean'], data['Lockdown']['cost_mean']]
    pareto_y = [data['LaissezFaire']['deaths_mean'], data['RemoteWork']['deaths_mean'], data['Lockdown']['deaths_mean']]
    ax.plot(pareto_x, pareto_y, color='#2c3e50', linestyle=':', linewidth=1.8, label='Frontera de Eficiencia de Pareto', zorder=2)

    ax.set_xlabel('Coste Económico Total (Millones de Euros - M€)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Mortalidad Acumulada (Número de Fallecidos)', fontsize=11, fontweight='bold')
    ax.set_xlim(300, 6500)
    ax.set_ylim(5500, 8500)
    ax.legend(loc='upper right', frameon=True)

    plt.title('Frontera de Pareto Multi-Objetivo: Impacto Macroeconómico vs Vidas Humanas (Alicante, 80 Réplicas)',
              fontsize=12, fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig07_pareto_epidemiological_tradeoff.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 8: IMPACTO SANITARIO (COLAPSO UCI) Y ADHERENCIA SOCIAL (FATIGA)
# ==============================================================================
def plot_fig8_icu_fatigue():
    data = parse_benchmark_file('results/flags/03.txt')['policies']
    policies = ['LaissezFaire', 'RemoteWork', 'DynamicSignals', 'Lockdown']

    icu_days = [data[p]['icu_mean'] for p in policies]
    icu_err = [data[p]['icu_std'] for p in policies]
    fatigue = [data[p]['fatigue'] for p in policies]

    x = np.arange(len(policies))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(8.5, 4.8))

    bars1 = ax1.bar(x - width/2, icu_days, width, yerr=icu_err, capsize=4,
                    color='#c0392b', edgecolor='black', linewidth=0.8, label='Días Colapso UCI (media ± σ)')
    ax1.set_ylabel('Días de Colapso Hospitalario de UCI', fontsize=11, fontweight='bold', color='#c0392b')
    ax1.set_xticks(x)
    ax1.set_xticklabels(policies, fontsize=10, fontweight='bold')
    ax1.set_ylim(0, 50)

    for bar in bars1:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., h + 3, f"{h:.1f} d",
                 ha='center', va='bottom', fontsize=9, fontweight='bold', color='#c0392b')

    ax2 = ax1.twinx()
    bars2 = ax2.bar(x + width/2, fatigue, width,
                    color='#8e44ad', edgecolor='black', linewidth=0.8, label='Fatiga Social Acumulada')
    ax2.set_ylabel('Índice de Fatiga Social Acumulada', fontsize=11, fontweight='bold', color='#8e44ad')
    ax2.set_ylim(0, 1.5)
    ax2.grid(False)

    for bar in bars2:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., h + 0.05, f"{h:.2f}",
                 ha='center', va='bottom', fontsize=9, fontweight='bold', color='#8e44ad')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True)

    plt.title('Evaluación de Políticas: Saturación de Cuidados Intensivos vs Fatiga Social de la Población',
              fontsize=12, fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig08_icu_collapse_and_fatigue.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 9: TIEMPO DE CPU POR POLÍTICA (DINÁMICA EPIDEMIOLÓGICA Y CARGA COMPUTACIONAL)
# ==============================================================================
def plot_fig9_compute_time_per_policy():
    data = parse_benchmark_file('results/flags/03.txt')['policies']
    policies = ['LaissezFaire', 'DynamicSignals', 'RemoteWork', 'Lockdown']
    times = [data[p]['compute_time_s'] for p in policies]

    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    colors = ['#27ae60', '#3498db', '#f39c12', '#e74c3c']
    bars = ax.bar(policies, times, width=0.52, color=colors, edgecolor='black', linewidth=0.8)

    ax.set_ylabel('Tiempo de Cómputo CPU (s) - [80 Réplicas]', fontsize=11, fontweight='bold')
    ax.set_xlabel('Política Epidemiológica Evaluada', fontsize=11, fontweight='bold')
    ax.set_ylim(0, max(times) * 1.25)

    base_time = times[0]
    for i, bar in enumerate(bars):
        h = bar.get_height()
        diff = ((h - base_time) / base_time) * 100
        diff_txt = f"(+{diff:.1f}%)" if diff > 0 else "(Ref)"
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.5, f"{h:.2f} s\n{diff_txt}",
                ha='center', va='bottom', fontsize=9.5, fontweight='bold')

    ax.annotate('En Lockdown la epidemia se alarga en el tiempo:\nMás celdas activas en la malla durante los 200 días\n→ +59.8% de operaciones estocásticas ejecutadas',
                xy=(3, times[3]), xytext=(1.0, 16.5),
                arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                fontsize=8.5, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#fcf3cf', edgecolor='#f39c12'))

    plt.title('Variabilidad del Tiempo de Ejecución de CPU según la Dinámica del Autómata Celular',
              fontsize=12, fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig09_compute_time_per_policy.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 10: ESCALABILIDAD MULTIESCALA DE POLÍTICAS (CIUDAD, PROVINCIA, COMUNIDAD)
# ==============================================================================
def plot_fig10_multiscale_policy_impact():
    scales = ['ciudad', 'provincia', 'comunidad']
    labels = ['Ciudad (~350k)', 'Provincia (~2.0M)', 'Comunidad (~5.1M)']
    policies = ['LaissezFaire', 'RemoteWork', 'DynamicSignals', 'Lockdown']
    
    cost_data = {p: [] for p in policies}
    death_data = {p: [] for p in policies}

    for sc in scales:
        d = parse_benchmark_file(f'results/size/{sc}.txt')['policies']
        for p in policies:
            cost_data[p].append(d[p]['cost_mean'])
            death_data[p].append(d[p]['deaths_mean'])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.8))
    x = np.arange(len(scales))
    width = 0.20

    colors = {'LaissezFaire': '#e74c3c', 'RemoteWork': '#f39c12', 'DynamicSignals': '#3498db', 'Lockdown': '#8e44ad'}

    for i, p in enumerate(policies):
        ax1.bar(x + (i - 1.5)*width, cost_data[p], width, label=p, color=colors[p], edgecolor='black', linewidth=0.6)
    ax1.set_ylabel('Coste Económico Total (M€)', fontsize=11, fontweight='bold')
    ax1.set_title('A: Impacto Económico por Escala (M€)', fontsize=11, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontweight='bold', fontsize=9.5)
    ax1.set_yscale('log')
    ax1.legend(loc='upper left', fontsize=8.5, frameon=True)

    for i, p in enumerate(policies):
        ax2.bar(x + (i - 1.5)*width, death_data[p], width, label=p, color=colors[p], edgecolor='black', linewidth=0.6)
    ax2.set_ylabel('Total Fallecidos (Personas)', fontsize=11, fontweight='bold')
    ax2.set_title('B: Mortalidad Acumulada por Escala', fontsize=11, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontweight='bold', fontsize=9.5)
    ax2.set_yscale('log')

    plt.suptitle('Consistencia Multiescala de las Políticas: Crecimiento Proporcional al Censo',
                 fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig10_multiscale_policy_impact.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 11: SPEEDUP ESPECÍFICO POR COMPONENTE DE CÓDIGO (UpdateGrid vs GetCounts)
# ==============================================================================
def plot_fig11_speedup_by_component():
    configs = ['-O0', '-O1', '-O2', '-Os', '-O3', '-Ofast', '-flto', 'max_opt']
    files = [
        'results/flags/base.txt', 'results/flags/01.txt', 'results/flags/02.txt',
        'results/flags/Os.txt', 'results/flags/03.txt', 'results/flags/0fast.txt',
        'results/lto/lto.txt', 'results/max_opt/max_opt.txt'
    ]

    su_list = []
    sc_list = []
    st_list = []

    base_data = parse_benchmark_file(files[0])
    base_u = base_data['update_grid_s']
    base_c = base_data['get_counts_s']
    base_t = base_data['wall_s']

    for f in files:
        d = parse_benchmark_file(f)
        su_list.append(base_u / d['update_grid_s'])
        sc_list.append(base_c / d['get_counts_s'])
        st_list.append(base_t / d['wall_s'])

    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    x = np.arange(len(configs))

    ax.plot(x, sc_list, marker='s', markersize=8, linewidth=2.4, color='#e74c3c', label='GetCounts (Reducción Censal)', zorder=4)
    ax.plot(x, su_list, marker='o', markersize=8, linewidth=2.4, color='#3498db', label='UpdateGrid (Stencil 2D)', zorder=4)
    ax.plot(x, st_list, marker='^', markersize=8, linewidth=2.0, color='#2c3e50', linestyle='--', label='Speedup Total Aplicación', zorder=3)

    # Anotaciones de valor en los extremos
    ax.annotate(f"{sc_list[-1]:.1f}x\n(LTO inlining)", xy=(x[-1], sc_list[-1]), xytext=(x[-1]-0.8, sc_list[-1]-3.5),
                arrowprops=dict(facecolor='#e74c3c', shrink=0.08, width=1, headwidth=5),
                fontsize=9, fontweight='bold', color='#c0392b',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#fadbd8', edgecolor='#e74c3c'))

    ax.annotate(f"{su_list[-1]:.1f}x (Asíntota)\nBarrera rand()/powf()", xy=(x[-1], su_list[-1]), xytext=(x[-1]-1.2, su_list[-1]+3.5),
                arrowprops=dict(facecolor='#3498db', shrink=0.08, width=1, headwidth=5),
                fontsize=9, fontweight='bold', color='#2980b9',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#ebf5fb', edgecolor='#3498db'))

    ax.set_ylabel('Speedup Relativo (Respecto a -O0)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Nivel de Optimización y Flags de Enlace', fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(configs, fontweight='bold', fontsize=9.5)
    ax.set_ylim(0, 24)
    ax.legend(loc='upper left', frameon=True)

    plt.title('Disparidad de Aceleración por Componente: Vectorización en Reducción vs Barrera Estocástica',
              fontsize=12, fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig11_speedup_by_kernel_component.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 12: HUELLA DE MEMORIA VS LÍMITES FÍSICOS DE CACHÉ L1/L2/L3 (SECCIÓN 5 Y 6)
# ==============================================================================
def plot_fig12_memory_hierarchy_working_set():
    scales = ['Ciudad\n(~350k)', 'Provincia\n(~2.0M)', 'Comunitat\n(~5.1M)']
    # Celdas por escala: 349281, 1999396, 5098564
    # 1 buffer de grid = N * 4 bytes
    # Working set activo (current + next) = N * 8 bytes
    # Working set total (current + next + days_infected) = N * 12 bytes
    b_single = np.array([349281 * 4, 1999396 * 4, 5098564 * 4]) / (1024 * 1024)
    b_active = np.array([349281 * 8, 1999396 * 8, 5098564 * 8]) / (1024 * 1024)
    b_total  = np.array([349281 * 12, 1999396 * 12, 5098564 * 12]) / (1024 * 1024)

    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    x = np.arange(len(scales))
    width = 0.25

    bars1 = ax.bar(x - width, b_single, width, label='1 Buffer (current_grid)', color='#7fb3d5', edgecolor='black', linewidth=0.7)
    bars2 = ax.bar(x, b_active, width, label='2 Buffers Activos (current + next)', color='#2980b9', edgecolor='black', linewidth=0.7)
    bars3 = ax.bar(x + width, b_total, width, label='Working Set Total (3 arrays)', color='#1b4f72', edgecolor='black', linewidth=0.7)

    # Líneas de referencia de caché del Intel Core i5-12400
    ax.axhline(0.281, color='#8e44ad', linestyle=':', linewidth=1.5, label='Caché L1d Total (288 KiB)')
    ax.axhline(7.5, color='#e67e22', linestyle='--', linewidth=1.8, label='Caché L2 Total (7.5 MiB)')
    ax.axhline(18.0, color='#c0392b', linestyle='-', linewidth=2.2, label='Caché L3 Compartida (18.0 MiB)')

    for bar in bars1 + bars2 + bars3:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 1.0, f"{h:.1f} MB",
                ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    ax.set_ylabel('Tamaño de los Datos en Memoria (Megabytes - MB)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Escala Geográfica de la Población', fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(scales, fontweight='bold', fontsize=10)
    ax.set_ylim(0, 72)
    ax.legend(loc='upper left', frameon=True, fontsize=9)

    ax.annotate('Comunidad: 1 solo buffer (20.4 MB) > L3 (18 MB)\n→ Tráfico forzado a Memoria Principal (RAM)\n→ Pérdida de rendimiento en MCUPS',
                xy=(2 - width, b_single[2]), xytext=(1.05, 52),
                arrowprops=dict(facecolor='#c0392b', shrink=0.08, width=1.2, headwidth=6),
                fontsize=9, fontweight='bold', color='#c0392b',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#fadbd8', edgecolor='#c0392b'))

    plt.title('Huella de Memoria vs Capacidad Física de la Jerarquía de Caché (Intel Core i5-12400)',
              fontsize=12, fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig12_memory_hierarchy_working_set.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 13: DESGLOSE DE FASES POR POLÍTICA (AISLAMIENTO DEL TIEMPO EN UPDATE_GRID)
# ==============================================================================
def plot_fig13_policy_phase_disparity():
    d = parse_benchmark_file('results/flags/03.txt')['policy_phases']
    policies = ['LaissezFaire', 'DynamicSignals', 'RemoteWork', 'Lockdown']

    t_up = [d[p]['update_s'] for p in policies]
    t_co = [d[p]['counts_s'] for p in policies]

    x = np.arange(len(policies))
    width = 0.38

    fig, ax = plt.subplots(figsize=(8.8, 4.8))

    bars_up = ax.bar(x - width/2, t_up, width, label='Update Grid (Propagación Estocástica)', color='#3498db', edgecolor='black', linewidth=0.8)
    bars_co = ax.bar(x + width/2, t_co, width, label='Get Counts (Reducción Censal)', color='#e74c3c', edgecolor='black', linewidth=0.8)

    for bar in bars_up:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.3, f"{h:.2f} s",
                ha='center', va='bottom', fontsize=9, fontweight='bold', color='#2980b9')

    for bar in bars_co:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.3, f"{h:.2f} s",
                ha='center', va='bottom', fontsize=9, fontweight='bold', color='#c0392b')

    # Línea horizontal en Get Counts para mostrar invarianza
    mean_counts = np.mean(t_co)
    ax.axhline(mean_counts, color='#c0392b', linestyle=':', alpha=0.7, label=f'Promedio Get Counts ({mean_counts:.2f} s)')

    ax.set_ylabel('Tiempo de CPU Consumido (s)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Política Epidemiológica', fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(policies, fontweight='bold', fontsize=10)
    ax.set_ylim(0, 18)
    ax.legend(loc='upper left', frameon=True)

    ax.annotate('Get Counts es invariante (~3.9 s):\nEl censo siempre recorre N celdas.\nLa disparidad (+84% en Update Grid)\nproviene al 100% de las celdas activas.',
                xy=(3 - width/2, t_up[3]), xytext=(1.2, 12.5),
                arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                fontsize=8.5, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#fcf3cf', edgecolor='#f39c12'))

    plt.title('Aislamiento de Fases por Política: Invarianza en Reducción vs Sobrecarga en Stencil',
              fontsize=12, fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig13_policy_phase_disparity.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 14: PROYECCIÓN TEÓRICA DE LA LEY DE AMDAHL PARA PARALELIZACIÓN (SECCIONES 8 Y 9)
# ==============================================================================
def plot_fig14_amdahl_parallel_projection():
    # Cores / hilos
    p = np.array([1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 64])

    # Fracciones paralelizables medidas:
    # 1. UpdateGrid sólo en -O3: f = 0.732 (Amdahl max = 3.73x)
    # 2. UpdateGrid en -flto: f = 0.966 (Amdahl max = 29.4x)
    # 3. UpdateGrid + GetCounts (OpenMP data parallel): f = 0.9999 (Amdahl max ~10,000x)
    # 4. Embarrassingly Parallel Monte Carlo replicas: f = 1.0 (Linear speedup S = p)
    f_o3 = 0.7321
    f_lto = 0.9661
    f_both = 0.9990

    s_o3 = 1.0 / ((1.0 - f_o3) + f_o3 / p)
    s_lto = 1.0 / ((1.0 - f_lto) + f_lto / p)
    s_both = 1.0 / ((1.0 - f_both) + f_both / p)
    s_linear = p

    fig, ax = plt.subplots(figsize=(9.2, 5.2))

    ax.plot(p, s_linear, color='#7f8c8d', linestyle=':', linewidth=1.8, label='Escalado Lineal Ideal (Réplicas Monte Carlo, f = 1.0)')
    ax.plot(p, s_both, color='#27ae60', marker='^', markersize=6, linewidth=2.2, label='Paralelismo de Datos Completo (Update+Counts, f = 0.999)')
    ax.plot(p, s_lto, color='#2980b9', marker='s', markersize=6, linewidth=2.2, label='Paralelismo sólo en UpdateGrid con LTO (f = 0.966)')
    ax.plot(p, s_o3, color='#e74c3c', marker='o', markersize=6, linewidth=2.2, label='Paralelismo sólo en UpdateGrid sin LTO (f = 0.732)')

    # Marcar los límites de la CPU de laboratorio: Intel Core i5-12400 (6 Cores, 12 Threads)
    ax.axvline(6, color='#2c3e50', linestyle='--', linewidth=1.5, alpha=0.8)
    ax.text(6 + 0.8, 1.5, '6 Núcleos P (Físicos)', rotation=90, fontsize=8.5, fontweight='bold', color='#2c3e50')

    ax.axvline(12, color='#2c3e50', linestyle='--', linewidth=1.5, alpha=0.8)
    ax.text(12 + 0.8, 1.5, '12 Hilos (SMT)', rotation=90, fontsize=8.5, fontweight='bold', color='#2c3e50')

    ax.set_ylabel('Speedup Teórico Máximo (Ley de Amdahl)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Número de Procesadores / Hebras Paralelas (p)', fontsize=11, fontweight='bold')
    ax.set_xlim(1, 32)
    ax.set_ylim(0, 28)
    ax.legend(loc='upper left', frameon=True, fontsize=9.2)

    # Anotaciones
    s6_lto = 1.0 / ((1.0 - f_lto) + f_lto / 6.0)
    ax.annotate(f"Speedup 6 cores = {s6_lto:.2f}x\n(Eficiencia: 85%)",
                xy=(6, s6_lto), xytext=(8, s6_lto - 2),
                arrowprops=dict(facecolor='#2980b9', shrink=0.08, width=1, headwidth=5),
                fontsize=8.5, fontweight='bold', color='#2980b9',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='#ebf5fb', edgecolor='#2980b9'))

    plt.title('Proyección Teórica de la Ganancia Paralela (Ley de Amdahl) para la Propuesta Arquitectural',
              fontsize=12, fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig14_amdahl_parallel_projection.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 15: DISPERSIÓN ESTOCÁSTICA DE MONTE CARLO Y RANGOS MÍN-MÁX (SECCIÓN 3 Y 6)
# ==============================================================================
def plot_fig15_monte_carlo_dispersion_ranges():
    d = parse_benchmark_file('results/flags/03.txt')['policies']
    policies = ['LaissezFaire', 'RemoteWork', 'DynamicSignals', 'Lockdown']

    means = [d[p]['deaths_mean'] for p in policies]
    stds  = [d[p]['deaths_std'] for p in policies]
    mins  = [d[p]['deaths_min'] for p in policies]
    maxs  = [d[p]['deaths_max'] for p in policies]

    x = np.arange(len(policies))
    colors = ['#e74c3c', '#f39c12', '#3498db', '#8e44ad']

    fig, ax = plt.subplots(figsize=(8.8, 4.8))

    for i in range(len(policies)):
        # Rango completo (min - max)
        ax.plot([x[i], x[i]], [mins[i], maxs[i]], color=colors[i], linewidth=2.5, alpha=0.5, zorder=2)
        ax.plot([x[i]-0.15, x[i]+0.15], [mins[i], mins[i]], color=colors[i], linewidth=2.0, alpha=0.7)
        ax.plot([x[i]-0.15, x[i]+0.15], [maxs[i], maxs[i]], color=colors[i], linewidth=2.0, alpha=0.7)

        # Intervalo ± 1 sigma
        ax.errorbar(x[i], means[i], yerr=stds[i], fmt='o', markersize=8, color=colors[i],
                    ecolor='black', elinewidth=2.2, capsize=5, capthick=1.5, zorder=4)

        # Texto con datos exactos
        r_amp = maxs[i] - mins[i]
        ax.text(x[i], maxs[i] + 70, f"Rango: [{mins[i]} - {maxs[i]}]\nΔ = {r_amp} | σ = ±{stds[i]:.0f}",
                ha='center', va='bottom', fontsize=8.5, fontweight='bold', color=colors[i],
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=colors[i], alpha=0.85))

    ax.set_ylabel('Mortalidad Acumulada (Fallecidos)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Política Sanitaria Evaluada', fontsize=11, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(policies, fontweight='bold', fontsize=10)
    ax.set_ylim(5000, 9200)

    # Leyenda personalizada
    ax.plot([], [], color='black', marker='o', label='Media muestral ± 1 Desviación estándar (σ)')
    ax.plot([], [], color='gray', linewidth=2.5, label='Rango experimental completo [Mínimo - Máximo]')
    ax.legend(loc='lower left', frameon=True, fontsize=9)

    plt.title('Incertidumbre Estocástica en 80 Réplicas: El Semáforo Reactivo Amortigua la Varianza',
              fontsize=12, fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig15_monte_carlo_dispersion_ranges.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == '__main__':
    print("=================================================================")
    print("Iniciando generación de 15 figuras científicas para la Memoria...")
    print("=================================================================")
    plot_fig1_flags_speedup()
    plot_fig2_flags_throughput()
    plot_fig3_profiling_phases_stacked()
    plot_fig4_advanced_opts()
    plot_fig5_lto_impact()
    plot_fig6_scalability_memory()
    plot_fig7_pareto_frontier()
    plot_fig8_icu_fatigue()
    plot_fig9_compute_time_per_policy()
    plot_fig10_multiscale_policy_impact()
    plot_fig11_speedup_by_component()
    plot_fig12_memory_hierarchy_working_set()
    plot_fig13_policy_phase_disparity()
    plot_fig14_amdahl_parallel_projection()
    plot_fig15_monte_carlo_dispersion_ranges()
    print("=================================================================")
    print(f"¡Las 15 gráficas han sido guardadas con éxito en: {OUTPUT_DIR}/ !")
    print("=================================================================")
