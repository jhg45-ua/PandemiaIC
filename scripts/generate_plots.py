#!/usr/bin/env python3
"""
Script de generación de gráficas científicas homogenizadas para la Memoria de Práctica 2
Ingeniería de los Computadores - Curso 2026-27 (Universidad de Alicante)
Genera 23 figuras de alta resolución (300 DPI) con estilo coherente y pie de fuente de datos en todas.
"""

import os
import re
import numpy as np
import matplotlib.pyplot as plt

# Directorio de salida
OUTPUT_DIR = "results/plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configuración estética general homogenizada
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.labelsize': 11.5,
    'axes.titlesize': 12.5,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 9.5,
    'figure.titlesize': 13.5,
    'axes.edgecolor': '#bdc3c7',
    'axes.linewidth': 0.8,
    'grid.color': '#ecf0f1',
    'grid.linestyle': '--',
    'grid.alpha': 0.8
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
# 2. HELPER UNIFICADO: PIE DE NOTA CON FUENTES
# ==============================================================================
def _add_footnote(fig, sources, notes=''):
    """Añade un pie de nota homogeneizado indicando el origen de los datos."""
    src_str = '  ·  '.join(sources)
    lines = [f'Fuente de datos: {src_str}']
    if notes:
        lines.append(f'Nota: {notes}')
    text = '\n'.join(lines)
    fig.text(
        0.01, -0.01, text,
        ha='left', va='top', fontsize=7.5, color='#555555', style='italic',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#f8f9fa', edgecolor='#dee2e6', alpha=0.92)
    )

# ==============================================================================
# FIG 1: FLAGS DE COMPILACIÓN
# ==============================================================================
def plot_fig1_flags_speedup():
    flags = ['-O0\n(base)', '-O1', '-O2', '-Os', '-O3', '-Ofast']
    files = ['results/flags/base.txt', 'results/flags/01.txt', 'results/flags/02.txt',
             'results/flags/Os.txt', 'results/flags/03.txt', 'results/flags/0fast.txt']
    
    times = [parse_benchmark_file(f)['wall_s'] for f in files]
    t_base = times[0]
    speedups = [t_base / t for t in times]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.8))
    x = np.arange(len(flags))

    colors = ['#7f8c8d', '#3498db', '#2980b9', '#e67e22', '#27ae60', '#16a085']
    bars = ax1.bar(x, times, width=0.55, color=colors, edgecolor='black', linewidth=0.7)
    ax1.set_ylabel('Tiempo Total de Ejecución (s)', fontweight='bold', color='#2c3e50')
    ax1.set_xlabel('Nivel de Optimización GCC', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(flags, fontweight='bold')
    ax1.set_ylim(0, max(times) * 1.18)
    ax1.set_title('A: Tiempo Total (Menor es mejor)', fontweight='bold')

    for bar in bars:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., h + 5, f"{h:.1f} s",
                 ha='center', va='bottom', fontsize=9.5, fontweight='bold', color='#2c3e50')

    ax2.plot(x, speedups, color='#c0392b', marker='o', linewidth=2.4, markersize=8, zorder=3)
    ax2.set_ylabel('Speedup (respecto a -O0)', fontweight='bold', color='#c0392b')
    ax2.set_xlabel('Nivel de Optimización GCC', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(flags, fontweight='bold')
    ax2.set_ylim(0.0, max(speedups) * 1.35)
    ax2.set_title('B: Ganancia en Velocidad (Mayor es mejor)', fontweight='bold')

    for i, s in enumerate(speedups):
        ax2.annotate(f"{s:.2f}x", (x[i], s), textcoords="offset points", xytext=(0, -22),
                     ha='center', va='top', fontsize=9.5, fontweight='bold', color='#c0392b',
                     bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor='#c0392b', alpha=0.95))

    plt.suptitle('Impacto de los Niveles de Optimización GCC (Caso Ciudad, 200 días)', fontweight='bold', fontsize=13, y=1.01)
    plt.tight_layout()
    _add_footnote(fig, files)
    outfile = os.path.join(OUTPUT_DIR, 'fig01_flags_speedup.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 2: THROUGHPUT DEL KERNEL (MCUPS)
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

    fig, ax1 = plt.subplots(figsize=(9.0, 4.8))
    bars1 = ax1.bar(x - width/2, mcups, width, label='Rendimiento Kernel (MCUPS)', color='#2980b9', edgecolor='black', linewidth=0.7)
    ax1.set_ylabel('Rendimiento del Kernel (MCUPS)', fontweight='bold', color='#2980b9')
    ax1.set_xlabel('Nivel de Optimización GCC', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(flags, fontweight='bold')
    ax1.set_ylim(0, max(mcups) * 1.25)

    for bar in bars1:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., h + 10, f"{h:.1f}", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#2980b9')

    ax2 = ax1.twinx()
    bars2 = ax2.bar(x + width/2, sims, width, label='Simulaciones / segundo', color='#e67e22', edgecolor='black', linewidth=0.7)
    ax2.set_ylabel('Productividad (Simulaciones Monte Carlo / s)', fontweight='bold', color='#e67e22')
    ax2.set_ylim(0, max(sims) * 1.30)
    ax2.grid(False)

    for bar in bars2:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., h + 0.15, f"{h:.2f}", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#d35400')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True)

    plt.title('Rendimiento del Kernel (MCUPS) y Productividad Global por Nivel de Optimización', fontweight='bold', pad=14)
    plt.tight_layout()
    _add_footnote(fig, files)
    outfile = os.path.join(OUTPUT_DIR, 'fig02_flags_throughput_mcups.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
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
    
    t_update, t_counts, t_analytics = [], [], []
    for f in files:
        data = parse_benchmark_file(f)
        t_update.append(data['update_grid_s'])
        t_counts.append(data['get_counts_s'])
        t_analytics.append(data['analytics_s'])

    x = np.arange(len(configs))
    width = 0.55

    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    ax.bar(x, t_update, width, label='Update Grid (Actualización)', color='#3498db', edgecolor='black', linewidth=0.7)
    ax.bar(x, t_counts, width, bottom=t_update, label='Get Counts (Recuento)', color='#e74c3c', edgecolor='black', linewidth=0.7)
    bottom_analytics = np.array(t_update) + np.array(t_counts)
    ax.bar(x, t_analytics, width, bottom=bottom_analytics, label='Analytics (Impacto)', color='#2ecc71', edgecolor='black', linewidth=0.7)

    totals = bottom_analytics + np.array(t_analytics)
    for i, t in enumerate(totals):
        pct_u = (t_update[i] / t) * 100
        pct_c = (t_counts[i] / t) * 100
        ax.text(x[i], t + 4, f"{t:.1f} s", ha='center', va='bottom', fontsize=9, fontweight='bold')
        if t_update[i] > 20:
            ax.text(x[i], t_update[i]/2, f"{pct_u:.0f}%", ha='center', va='center', color='white', fontweight='bold', fontsize=8.5)
        if t_counts[i] > 10:
            ax.text(x[i], t_update[i] + t_counts[i]/2, f"{pct_c:.0f}%", ha='center', va='center', color='white', fontweight='bold', fontsize=8.5)

    ax.set_ylabel('Tiempo Acumulado de Ejecución (s)', fontweight='bold')
    ax.set_xlabel('Configuración de Compilación', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(configs, fontsize=9.5, fontweight='bold')
    ax.set_ylim(0, max(totals) * 1.15)
    ax.legend(loc='upper right', frameon=True)

    plt.title('Desglose Temporal por Fases del Programa y Demostración de la Ley de Amdahl', fontweight='bold', pad=14)
    plt.tight_layout()
    _add_footnote(fig, files)
    outfile = os.path.join(OUTPUT_DIR, 'fig03_profiling_phases_stacked.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 4: COMPARATIVA DE FLAGS AVANZADOS
# ==============================================================================
def plot_fig4_advanced_opts():
    experiments = [
        ('-O3 Referencia', 'results/march/03.txt'),
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
    files = [e[1] for e in experiments]
    times = [parse_benchmark_file(f)['wall_s'] for f in files]
    
    colors = ['#27ae60' if 'flto' in n or 'max_opt' in n else '#e74c3c' if 'PGO' in n else '#34495e' if 'Referencia' in n else '#3498db' for n in names]

    fig, ax = plt.subplots(figsize=(10.0, 5.6))
    y = np.arange(len(names))
    bars = ax.barh(y, times, height=0.62, color=colors, edgecolor='black', linewidth=0.7)

    ax.set_xlabel('Tiempo Total de Ejecución (s) - [Menor es mejor]', fontweight='bold')
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9.5, fontweight='bold')
    ax.invert_yaxis()
    ax.set_xlim(0, 115)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 1.2, bar.get_y() + bar.get_height()/2., f"{w:.2f} s", ha='left', va='center', fontsize=9.5, fontweight='bold', color='#2c3e50')

    ax.axvline(times[0], color='#e67e22', linestyle='--', linewidth=1.5, label=f'Referencia -O3 ({times[0]:.1f} s)', zorder=2)
    ax.legend(loc='upper right', frameon=True, fontsize=10)

    plt.title('Comparativa de Opciones Avanzadas de Compilación en GCC 13.2 (Intel Core i5-12400)', fontweight='bold', pad=14)
    plt.tight_layout()
    _add_footnote(fig, files)
    outfile = os.path.join(OUTPUT_DIR, 'fig04_advanced_opts_ablation.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 5: IMPACTO DE LTO (-flto)
# ==============================================================================
def plot_fig5_lto_impact():
    cases = ['-O3 Referencia', '-O3 + march=native', '-O3 + native + funroll', '-O3 + native + flto (LTO)', 'max_opt (-Ofast + lto)']
    files = ['results/march/03.txt', 'results/march/03+native.txt', 'results/unroll/unroll.txt', 'results/lto/lto.txt', 'results/max_opt/max_opt.txt']

    t_counts, t_update = [], []
    for f in files:
        d = parse_benchmark_file(f)
        t_counts.append(d['get_counts_s'])
        t_update.append(d['update_grid_s'])

    x = np.arange(len(cases))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 5.0))

    bars_c = ax1.bar(x, t_counts, width=0.55, color=['#e74c3c', '#e74c3c', '#e74c3c', '#27ae60', '#27ae60'], edgecolor='black', linewidth=0.8)
    ax1.set_ylabel('Tiempo en get_counts() (s)', fontweight='bold', color='#c0392b')
    ax1.set_xticks(x)
    ax1.set_xticklabels(cases, rotation=25, ha='right', fontsize=9, fontweight='bold')
    ax1.set_title('A: Tiempo en get_counts() (Recuento)', fontweight='bold')
    ax1.set_ylim(0, 26)

    for bar in bars_c:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., h + 0.5, f"{h:.2f} s", ha='center', va='bottom', fontsize=9, fontweight='bold')
        
    ax1.annotate('Aceleración de 13.8x\n(inlining entre archivos .c)', xy=(3, 2.5), xytext=(3.3, 16.5),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                 fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#d4efdf', edgecolor='#27ae60'))

    bars_u = ax2.bar(x, t_update, width=0.55, color=['#3498db', '#3498db', '#3498db', '#2980b9', '#2980b9'], edgecolor='black', linewidth=0.8)
    ax2.set_ylabel('Tiempo en update_grid() (s)', fontweight='bold', color='#2980b9')
    ax2.set_xticks(x)
    ax2.set_xticklabels(cases, rotation=25, ha='right', fontsize=9, fontweight='bold')
    ax2.set_title('B: Tiempo en update_grid() (Llamadas a rand/pow)', fontweight='bold')
    ax2.set_ylim(0, 52)

    for bar in bars_u:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., h + 0.8, f"{h:.1f} s", ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.suptitle('Efecto de LTO (-flto): Inlining entre Módulos en Recuento vs Actualización de Celdas', fontweight='bold', fontsize=12.5, y=1.02)
    plt.tight_layout()
    _add_footnote(fig, files)
    outfile = os.path.join(OUTPUT_DIR, 'fig05_lto_impact_reduction_vs_stencil.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 6: ESCALABILIDAD Y JERARQUÍA DE MEMORIA
# ==============================================================================
def plot_fig6_scalability_memory():
    scales = ['Ciudad\n(Alicante)', 'Provincia\n(Alicante)', 'Comunitat\nValenciana']
    files = ['results/size/ciudad.txt', 'results/size/provincia.txt', 'results/size/comunidad.txt']
    pops = [349281, 1999396, 5098564]
    
    times, mcups = [], []
    for f in files:
        d = parse_benchmark_file(f)
        times.append(d['wall_s'])
        mcups.append(d['mcups'])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 5.0))
    x = np.arange(len(scales))

    bars = ax1.bar(x, times, width=0.52, color='#34495e', edgecolor='black', linewidth=0.8)
    ax1.set_ylabel('Tiempo Total de Ejecución (s)', fontweight='bold', color='#2c3e50')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"{scales[i]}\n({pops[i]:,} celdas)" for i in range(3)], fontsize=9.5, fontweight='bold')
    ax1.set_ylim(0, max(times) * 1.22)
    ax1.set_title('A: Tiempo Total vs Tamaño del Problema', fontweight='bold')

    for bar in bars:
        h = bar.get_height()
        txt = f"{h:.1f} s\n({h/60:.1f} min)" if h >= 60 else f"{h:.1f} s"
        ax1.text(bar.get_x() + bar.get_width()/2., h + 20, txt, ha='center', va='bottom', fontsize=9, fontweight='bold', color='#2c3e50')

    ax2.plot(x, mcups, color='#27ae60', marker='s', markersize=9, linewidth=2.4, zorder=3)
    ax2.set_ylabel('Rendimiento del Kernel (MCUPS)', fontweight='bold', color='#27ae60')
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"{scales[i]}\n({pops[i]:,} celdas)" for i in range(3)], fontsize=9.5, fontweight='bold')
    ax2.set_xlim(-0.4, 2.4)
    ax2.set_ylim(430, 510)
    ax2.set_title('B: Rendimiento del Kernel y Límite de Caché L3', fontweight='bold')

    for i, m in enumerate(mcups):
        ax2.annotate(f"{m:.1f} MCUPS", (x[i], m), textcoords="offset points", xytext=(0, 12),
                     ha='center', fontsize=9.5, fontweight='bold', color='#27ae60',
                     bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor='#27ae60', alpha=0.9))

    ax2.annotate('Comunidad supera Caché L3 (18 MB):\n1 buffer = 20.4 MB\n→ Caída en MCUPS por accesos a RAM',
                 xy=(2, mcups[2]), xytext=(0.75, 442),
                 arrowprops=dict(facecolor='#c0392b', shrink=0.08, width=1.2, headwidth=6),
                 fontsize=8.5, fontweight='bold', color='#c0392b',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='#fadbd8', edgecolor='#c0392b'))

    plt.suptitle('Escalabilidad del Censo y Comportamiento Frente a la Jerarquía de Caché', fontweight='bold', fontsize=13, y=1.01)
    plt.tight_layout()
    _add_footnote(fig, files)
    outfile = os.path.join(OUTPUT_DIR, 'fig06_scalability_problem_size_memory.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 7: COMPROMISO COSTE VS MORTALIDAD
# ==============================================================================
def plot_fig7_pareto_frontier():
    src = 'results/flags/03.txt'
    data = parse_benchmark_file(src)['policies']
    policies = ['LaissezFaire', 'RemoteWork', 'DynamicSignals', 'Lockdown']
    colors = {'LaissezFaire': '#e74c3c', 'RemoteWork': '#f39c12', 'DynamicSignals': '#3498db', 'Lockdown': '#8e44ad'}

    fig, ax = plt.subplots(figsize=(9.2, 5.4))
    for p in policies:
        d = data[p]
        ax.errorbar(d['cost_mean'], d['deaths_mean'], xerr=d['cost_std'], yerr=d['deaths_std'],
                    fmt='o', markersize=9, color=colors[p], ecolor=colors[p], elinewidth=1.6, capsize=4,
                    label=f"{p} (media ± σ)", zorder=4)

    positions = {'LaissezFaire': (25, 20), 'RemoteWork': (20, 25), 'DynamicSignals': (-130, -10), 'Lockdown': (25, -20)}
    for p in policies:
        d = data[p]
        ax.annotate(f"{p}\nCoste: {d['cost_mean']:.0f} M€\nMuertes: {d['deaths_mean']:.0f}",
                    (d['cost_mean'], d['deaths_mean']), textcoords="offset points", xytext=positions[p],
                    ha='left', va='bottom' if positions[p][1]>0 else 'center', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=colors[p], alpha=0.95),
                    arrowprops=dict(arrowstyle='->', color=colors[p], lw=1.2))

    px = [data['LaissezFaire']['cost_mean'], data['RemoteWork']['cost_mean'], data['Lockdown']['cost_mean']]
    py = [data['LaissezFaire']['deaths_mean'], data['RemoteWork']['deaths_mean'], data['Lockdown']['deaths_mean']]
    ax.plot(px, py, color='#2c3e50', linestyle=':', linewidth=1.8, label='Curva de Compromiso (Coste vs Vidas)', zorder=2)

    ax.set_xlabel('Coste Económico Total (Millones de Euros - M€)', fontweight='bold')
    ax.set_ylabel('Mortalidad Acumulada (Número de Fallecidos)', fontweight='bold')
    ax.set_xlim(300, 6800)
    ax.set_ylim(5400, 8600)
    ax.legend(loc='upper right', frameon=True)

    plt.title('Compromiso entre Coste Económico y Vidas Humanas por Política (Alicante, 80 Réplicas)', fontweight='bold', pad=14)
    plt.tight_layout()
    _add_footnote(fig, [src])
    outfile = os.path.join(OUTPUT_DIR, 'fig07_pareto_epidemiological_tradeoff.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 8: IMPACTO SANITARIO (COLAPSO UCI) Y ADHERENCIA SOCIAL
# ==============================================================================
def plot_fig8_icu_fatigue():
    src = 'results/flags/03.txt'
    data = parse_benchmark_file(src)['policies']
    policies = ['LaissezFaire', 'RemoteWork', 'DynamicSignals', 'Lockdown']

    icu_days = [data[p]['icu_mean'] for p in policies]
    icu_err = [data[p]['icu_std'] for p in policies]
    fatigue = [data[p]['fatigue'] for p in policies]

    x = np.arange(len(policies))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(8.8, 5.0))
    ax1.bar(x - width/2, icu_days, width, yerr=icu_err, capsize=4, color='#c0392b', edgecolor='black', linewidth=0.8, label='Días Colapso UCI (media ± σ)')
    ax1.set_ylabel('Días de Colapso Hospitalario de UCI', fontweight='bold', color='#c0392b')
    ax1.set_xticks(x)
    ax1.set_xticklabels(policies, fontweight='bold')
    ax1.set_ylim(0, 58)

    ax1.text(x[0] - width/2, icu_days[0] + icu_err[0] + 2.0, f"{icu_days[0]:.1f} d", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#c0392b')
    ax1.text(x[1] - width/2 - 0.12, 4.5, f"{icu_days[1]:.1f} d", ha='right', va='bottom', fontsize=9, fontweight='bold', color='#c0392b')
    ax1.text(x[2] - width/2, 1.5, f"{icu_days[2]:.1f} d", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#c0392b')
    ax1.text(x[3] - width/2, 1.5, f"{icu_days[3]:.1f} d", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#c0392b')

    ax2 = ax1.twinx()
    bars2 = ax2.bar(x + width/2, fatigue, width, color='#8e44ad', edgecolor='black', linewidth=0.8, label='Fatiga Social de la Población')
    ax2.set_ylabel('Índice de Fatiga Social', fontweight='bold', color='#8e44ad')
    ax2.set_ylim(0, 1.6)
    ax2.grid(False)

    for bar in bars2:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., h + 0.04, f"{h:.2f}", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#8e44ad')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center', frameon=True, ncol=2)

    plt.title('Evaluación de Políticas: Saturación de Cuidados Intensivos vs Fatiga Social', fontweight='bold', pad=14)
    plt.tight_layout()
    _add_footnote(fig, [src])
    outfile = os.path.join(OUTPUT_DIR, 'fig08_icu_collapse_and_fatigue.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 9: TIEMPO DE CPU POR POLÍTICA
# ==============================================================================
def plot_fig9_compute_time_per_policy():
    src = 'results/flags/03.txt'
    data = parse_benchmark_file(src)['policies']
    policies = ['LaissezFaire', 'DynamicSignals', 'RemoteWork', 'Lockdown']
    times = [data[p]['compute_time_s'] for p in policies]

    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    bars = ax.bar(policies, times, width=0.52, color=['#27ae60', '#3498db', '#f39c12', '#e74c3c'], edgecolor='black', linewidth=0.8)

    ax.set_ylabel('Tiempo de Cómputo CPU (s) - [80 Réplicas]', fontweight='bold')
    ax.set_xlabel('Política Sanitaria Evaluada', fontweight='bold')
    ax.set_ylim(0, 24)

    base_time = times[0]
    for i, bar in enumerate(bars):
        h = bar.get_height()
        diff = ((h - base_time) / base_time) * 100
        diff_txt = f"(+{diff:.1f}%)" if diff > 0 else "(Ref)"
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.5, f"{h:.2f} s\n{diff_txt}", ha='center', va='bottom', fontsize=9.5, fontweight='bold')

    ax.annotate('En Lockdown la epidemia se alarga:\nMás celdas activas en la malla durante los 200 días\n→ +59.8% de operaciones de contagio ejecutadas',
                xy=(3, times[3]), xytext=(0.6, 19.5),
                arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                fontsize=8.5, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#fcf3cf', edgecolor='#f39c12'))

    plt.title('Variabilidad del Tiempo de Cómputo según la Dinámica de la Simulación', fontweight='bold', pad=14)
    plt.tight_layout()
    _add_footnote(fig, [src])
    outfile = os.path.join(OUTPUT_DIR, 'fig09_compute_time_per_policy.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 10: ESCALABILIDAD MULTIESCALA DE POLÍTICAS
# ==============================================================================
def plot_fig10_multiscale_policy_impact():
    scales = ['ciudad', 'provincia', 'comunidad']
    labels = ['Ciudad (~350k)', 'Provincia (~2.0M)', 'Comunidad (~5.1M)']
    policies = ['LaissezFaire', 'RemoteWork', 'DynamicSignals', 'Lockdown']
    files = [f'results/size/{sc}.txt' for sc in scales]
    
    cost_data = {p: [] for p in policies}
    death_data = {p: [] for p in policies}

    for f in files:
        d = parse_benchmark_file(f)['policies']
        for p in policies:
            cost_data[p].append(d[p]['cost_mean'])
            death_data[p].append(d[p]['deaths_mean'])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 5.0))
    x = np.arange(len(scales))
    width = 0.20
    colors = {'LaissezFaire': '#e74c3c', 'RemoteWork': '#f39c12', 'DynamicSignals': '#3498db', 'Lockdown': '#8e44ad'}

    for i, p in enumerate(policies):
        ax1.bar(x + (i - 1.5)*width, cost_data[p], width, label=p, color=colors[p], edgecolor='black', linewidth=0.6)
    ax1.set_ylabel('Coste Económico Total (M€)', fontweight='bold')
    ax1.set_title('A: Impacto Económico por Escala (M€)', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontweight='bold', fontsize=9.5)
    ax1.set_yscale('log')
    ax1.legend(loc='upper left', fontsize=8.5, frameon=True)

    for i, p in enumerate(policies):
        ax2.bar(x + (i - 1.5)*width, death_data[p], width, label=p, color=colors[p], edgecolor='black', linewidth=0.6)
    ax2.set_ylabel('Total Fallecidos (Personas)', fontweight='bold')
    ax2.set_title('B: Mortalidad Acumulada por Escala', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontweight='bold', fontsize=9.5)
    ax2.set_yscale('log')

    plt.suptitle('Consistencia Multiescala de las Políticas: Crecimiento Proporcional al Censo', fontweight='bold', fontsize=12.5, y=1.01)
    plt.tight_layout()
    _add_footnote(fig, files)
    outfile = os.path.join(OUTPUT_DIR, 'fig10_multiscale_policy_impact.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 11: SPEEDUP ESPECÍFICO POR COMPONENTE DE CÓDIGO
# ==============================================================================
def plot_fig11_speedup_by_kernel_component():
    configs = ['-O0', '-O1', '-O2', '-Os', '-O3', '-Ofast', '-flto', 'max_opt']
    files = [
        'results/flags/base.txt', 'results/flags/01.txt', 'results/flags/02.txt',
        'results/flags/Os.txt', 'results/flags/03.txt', 'results/flags/0fast.txt',
        'results/lto/lto.txt', 'results/max_opt/max_opt.txt'
    ]

    base_data = parse_benchmark_file(files[0])
    base_u, base_c, base_t = base_data['update_grid_s'], base_data['get_counts_s'], base_data['wall_s']

    su_list, sc_list, st_list = [], [], []
    for f in files:
        d = parse_benchmark_file(f)
        su_list.append(base_u / d['update_grid_s'])
        sc_list.append(base_c / d['get_counts_s'])
        st_list.append(base_t / d['wall_s'])

    fig, ax = plt.subplots(figsize=(9.4, 5.2))
    x = np.arange(len(configs))

    ax.plot(x, sc_list, marker='s', markersize=8, linewidth=2.4, color='#e74c3c', label='GetCounts (Recuento de Estados)', zorder=4)
    ax.plot(x, su_list, marker='o', markersize=8, linewidth=2.4, color='#3498db', label='UpdateGrid (Actualización de Celdas)', zorder=4)
    ax.plot(x, st_list, marker='^', markersize=8, linewidth=2.0, color='#2c3e50', linestyle='--', label='Speedup Total de la Aplicación', zorder=3)

    ax.annotate(f"{sc_list[-1]:.1f}x\n(LTO inlining)", xy=(x[-1], sc_list[-1]), xytext=(x[-1]-0.9, 16.5),
                arrowprops=dict(facecolor='#e74c3c', shrink=0.08, width=1, headwidth=5),
                fontsize=9, fontweight='bold', color='#c0392b',
                bbox=dict(boxstyle='round,pad=0.25', facecolor='#fadbd8', edgecolor='#e74c3c'))

    ax.annotate(f"{su_list[-1]:.1f}x (Límite)\nBarrera por rand() y powf()", xy=(x[-1], su_list[-1]), xytext=(x[-1]-0.9, 9.5),
                arrowprops=dict(facecolor='#3498db', shrink=0.08, width=1, headwidth=5),
                fontsize=8.5, fontweight='bold', color='#2980b9',
                bbox=dict(boxstyle='round,pad=0.25', facecolor='#ebf5fb', edgecolor='#3498db'))

    ax.set_ylabel('Speedup Relativo (respecto a -O0)', fontweight='bold')
    ax.set_xlabel('Nivel de Optimización y Flags de Enlace', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(configs, fontweight='bold', fontsize=9.5)
    ax.set_ylim(0, 24)
    ax.legend(loc='upper left', frameon=True)

    plt.title('Aceleración por Componente: Vectorización en Recuento vs Límite en Actualización', fontweight='bold', pad=14)
    plt.tight_layout()
    _add_footnote(fig, files)
    outfile = os.path.join(OUTPUT_DIR, 'fig11_speedup_by_kernel_component.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 12: MEMORIA OCUPADA VS LÍMITES DE CACHÉ L1/L2/L3
# ==============================================================================
def plot_fig12_memory_hierarchy_working_set():
    scales = ['Ciudad\n(~350k)', 'Provincia\n(~2.0M)', 'Comunitat\n(~5.1M)']
    files = ['results/size/ciudad.txt', 'results/size/provincia.txt', 'results/size/comunidad.txt']
    b_single = np.array([349281 * 4, 1999396 * 4, 5098564 * 4]) / (1024 * 1024)
    b_active = np.array([349281 * 8, 1999396 * 8, 5098564 * 8]) / (1024 * 1024)
    b_total  = np.array([349281 * 12, 1999396 * 12, 5098564 * 12]) / (1024 * 1024)

    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    x = np.arange(len(scales))
    width = 0.25

    bars1 = ax.bar(x - width, b_single, width, label='1 Buffer (current_grid)', color='#7fb3d5', edgecolor='black', linewidth=0.7)
    bars2 = ax.bar(x, b_active, width, label='2 Buffers Activos (current + next)', color='#2980b9', edgecolor='black', linewidth=0.7)
    bars3 = ax.bar(x + width, b_total, width, label='Memoria Total (3 arrays)', color='#1b4f72', edgecolor='black', linewidth=0.7)

    ax.axhline(0.281, color='#8e44ad', linestyle=':', linewidth=1.5, label='Caché L1d Total (288 KiB)', zorder=1)
    ax.axhline(7.5, color='#e67e22', linestyle='--', linewidth=1.8, label='Caché L2 Total (7.5 MiB)', zorder=1)
    ax.axhline(18.0, color='#c0392b', linestyle='-', linewidth=2.2, label='Caché L3 Compartida (18.0 MiB)', zorder=1)

    for bar in bars1 + bars2 + bars3:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 1.2, f"{h:.1f} MB",
                ha='center', va='bottom', fontsize=8.5, fontweight='bold',
                bbox=dict(boxstyle='square,pad=0.15', facecolor='white', edgecolor='none', alpha=0.95), zorder=5)

    ax.set_ylabel('Tamaño de los Datos en Memoria (Megabytes - MB)', fontweight='bold')
    ax.set_xlabel('Escala Geográfica de la Población', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(scales, fontweight='bold', fontsize=10)
    ax.set_ylim(0, 78)
    ax.legend(loc='upper left', frameon=True, fontsize=9)

    ax.annotate('Comunidad: 1 solo buffer (20.4 MB) > L3 (18 MB)\n→ Tráfico forzado a Memoria Principal (RAM)\n→ Pérdida de rendimiento en MCUPS',
                xy=(2 - width, 12.0), xytext=(0.85, 52),
                arrowprops=dict(facecolor='#c0392b', shrink=0.08, width=1.2, headwidth=6),
                fontsize=8.5, fontweight='bold', color='#c0392b',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#fadbd8', edgecolor='#c0392b'), zorder=6)

    plt.title('Memoria Ocupada vs Capacidad Física de la Jerarquía de Caché (Intel Core i5-12400)', fontweight='bold', pad=14)
    plt.tight_layout()
    _add_footnote(fig, files, notes='Capacidades de caché L1, L2 y L3 correspondientes a la CPU Intel Core i5-12400.')
    outfile = os.path.join(OUTPUT_DIR, 'fig12_memory_hierarchy_working_set.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 13: DESGLOSE DE FASES POR POLÍTICA
# ==============================================================================
def plot_fig13_policy_phase_disparity():
    src = 'results/flags/03.txt'
    d = parse_benchmark_file(src)['policy_phases']
    policies = ['LaissezFaire', 'DynamicSignals', 'RemoteWork', 'Lockdown']

    t_up = [d[p]['update_s'] for p in policies]
    t_co = [d[p]['counts_s'] for p in policies]

    x = np.arange(len(policies))
    width = 0.38

    fig, ax = plt.subplots(figsize=(9.0, 5.0))
    bars_up = ax.bar(x - width/2, t_up, width, label='Update Grid (Actualización de Celdas)', color='#3498db', edgecolor='black', linewidth=0.8)
    bars_co = ax.bar(x + width/2, t_co, width, label='Get Counts (Recuento de Estados)', color='#e74c3c', edgecolor='black', linewidth=0.8)

    for bar in bars_up:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.35, f"{h:.2f} s", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#2980b9')

    for bar in bars_co:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.35, f"{h:.2f} s", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#c0392b',
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor='#e74c3c', alpha=0.9))

    mean_counts = np.mean(t_co)
    ax.axhline(mean_counts, color='#c0392b', linestyle=':', alpha=0.7, label=f'Promedio Get Counts ({mean_counts:.2f} s)', zorder=2)

    ax.set_ylabel('Tiempo de CPU Consumido (s)', fontweight='bold')
    ax.set_xlabel('Política Sanitaria Evaluada', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(policies, fontweight='bold', fontsize=10)
    ax.set_ylim(0, 19)
    ax.legend(loc='upper left', frameon=True)

    ax.annotate('Get Counts es invariante (~3.9 s):\nEl censo siempre recorre N celdas.\nLa variación (+84% en Update Grid)\nproviene al 100% de las celdas activas.',
                xy=(3 - width/2, t_up[3]), xytext=(1.05, 13.5),
                arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                fontsize=8.5, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#fcf3cf', edgecolor='#f39c12'))

    plt.title('Comparativa de Fases: Recuento Invariante vs Variación en Actualización de Celdas', fontweight='bold', pad=14)
    plt.tight_layout()
    _add_footnote(fig, [src])
    outfile = os.path.join(OUTPUT_DIR, 'fig13_policy_phase_disparity.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 14: PROYECCIÓN TEÓRICA DE AMDAHL
# ==============================================================================
def plot_fig14_amdahl_parallel_projection():
    sources = ['results/flags/03.txt', 'results/lto/lto.txt']
    p = np.array([1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 64])

    f_o3 = 0.7321
    f_lto = 0.9661
    f_both = 0.9990

    s_o3 = 1.0 / ((1.0 - f_o3) + f_o3 / p)
    s_lto = 1.0 / ((1.0 - f_lto) + f_lto / p)
    s_both = 1.0 / ((1.0 - f_both) + f_both / p)
    s_linear = p

    fig, ax = plt.subplots(figsize=(9.8, 5.8))

    ax.plot(p, s_linear, color='#7f8c8d', linestyle=':', linewidth=1.8, label='Escalado Lineal Ideal (Réplicas Monte Carlo, f = 1.0)', zorder=2)
    ax.plot(p, s_both, color='#27ae60', marker='^', markersize=6, linewidth=2.2, label='Paralelismo Completo (Update + Counts, f = 0.999)', zorder=3)
    ax.plot(p, s_lto, color='#2980b9', marker='s', markersize=6, linewidth=2.2, label='Paralelismo en UpdateGrid con LTO (f = 0.966)', zorder=3)
    ax.plot(p, s_o3, color='#e74c3c', marker='o', markersize=6, linewidth=2.2, label='Paralelismo en UpdateGrid sin LTO (f = 0.732)', zorder=3)

    ax.axvline(6, color='#2c3e50', linestyle='--', linewidth=1.4, alpha=0.6, zorder=1)
    ax.text(6, 27.5, '6 Cores Físicos', ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#2c3e50',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#eaeded', edgecolor='#2c3e50', alpha=0.95), zorder=5)

    ax.axvline(12, color='#2c3e50', linestyle='--', linewidth=1.4, alpha=0.6, zorder=1)
    ax.text(12, 27.5, '12 Threads (SMT)', ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#2c3e50',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#eaeded', edgecolor='#2c3e50', alpha=0.95), zorder=5)

    ax.set_ylabel('Speedup Teórico Máximo (Ley de Amdahl)', fontweight='bold')
    ax.set_xlabel('Número de Procesadores / Threads en Paralelo (p)', fontweight='bold')
    ax.set_xlim(1, 32)
    ax.set_ylim(0, 31)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.14), ncol=2, frameon=True, fontsize=9.0)

    s6_lto = 1.0 / ((1.0 - f_lto) + f_lto / 6.0)
    ax.annotate(f"Speedup con 6 Cores = {s6_lto:.2f}x\n(Eficiencia: 85.5%)\nCon 12 Threads = 8.73x",
                xy=(6, s6_lto), xytext=(2.2, 12.5),
                arrowprops=dict(facecolor='#2980b9', shrink=0.08, width=1.2, headwidth=6),
                fontsize=9, fontweight='bold', color='#2980b9',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#ebf5fb', edgecolor='#2980b9'), zorder=6)

    plt.title('Proyección Teórica de la Ganancia Paralela (Ley de Amdahl) en Intel Core i5-12400', fontweight='bold', pad=14)
    plt.tight_layout()
    _add_footnote(fig, sources, notes='Fracciones de código paralelizable f estimadas a partir de la temporización de fases.')
    outfile = os.path.join(OUTPUT_DIR, 'fig14_amdahl_parallel_projection.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 15: DISPERSIÓN DE RESULTADOS EN MONTE CARLO
# ==============================================================================
def plot_fig15_monte_carlo_dispersion_ranges():
    src = 'results/flags/03.txt'
    d = parse_benchmark_file(src)['policies']
    policies = ['LaissezFaire', 'RemoteWork', 'DynamicSignals', 'Lockdown']

    means = [d[p]['deaths_mean'] for p in policies]
    stds  = [d[p]['deaths_std'] for p in policies]
    mins  = [d[p]['deaths_min'] for p in policies]
    maxs  = [d[p]['deaths_max'] for p in policies]

    x = np.arange(len(policies))
    colors = ['#e74c3c', '#f39c12', '#3498db', '#8e44ad']

    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    for i in range(len(policies)):
        ax.plot([x[i], x[i]], [mins[i], maxs[i]], color=colors[i], linewidth=2.5, alpha=0.5, zorder=2)
        ax.plot([x[i]-0.15, x[i]+0.15], [mins[i], mins[i]], color=colors[i], linewidth=2.0, alpha=0.7)
        ax.plot([x[i]-0.15, x[i]+0.15], [maxs[i], maxs[i]], color=colors[i], linewidth=2.0, alpha=0.7)

        ax.errorbar(x[i], means[i], yerr=stds[i], fmt='o', markersize=8, color=colors[i],
                    ecolor='black', elinewidth=2.2, capsize=5, capthick=1.5, zorder=4)

        r_amp = maxs[i] - mins[i]
        ax.text(x[i], maxs[i] + 160, f"Rango: [{mins[i]} - {maxs[i]}]\nΔ = {r_amp} | σ = ±{stds[i]:.0f}",
                ha='center', va='bottom', fontsize=8.5, fontweight='bold', color=colors[i],
                bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor=colors[i], alpha=0.9))

    ax.set_ylabel('Mortalidad Acumulada (Fallecidos)', fontweight='bold')
    ax.set_xlabel('Política Sanitaria Evaluada', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(policies, fontweight='bold', fontsize=10)
    ax.set_ylim(4800, 9700)

    ax.plot([], [], color='black', marker='o', label='Media muestral ± 1 Desviación estándar (σ)')
    ax.plot([], [], color='gray', linewidth=2.5, label='Rango experimental completo [Mínimo - Máximo]')
    ax.legend(loc='lower left', frameon=True, fontsize=9)

    plt.title('Variabilidad de las 80 Réplicas: El Semáforo Reactivo Amortigua la Dispersión', fontweight='bold', pad=14)
    plt.tight_layout()
    _add_footnote(fig, [src])
    outfile = os.path.join(OUTPUT_DIR, 'fig15_monte_carlo_dispersion_ranges.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 16: MODELO ROOFLINE REOPTIMIZADO
# ==============================================================================
def plot_fig16_roofline_model():
    src = 'results/flags/03.txt'
    BW_GB_s = 38.0
    PEAK_GFLOPS = 96.0

    ai_counts = 2.0 / (9 * 4)   # ~0.0556 FLOP/B
    ai_update = 12.0 / 40.0     # 0.3000 FLOP/B

    mcups_O3 = 519.07
    gflops_counts = mcups_O3 * 0.268 * 2 / 1e3   # ~0.278 GFLOPS
    gflops_update = mcups_O3 * 0.732 * 12 / 1e3  # ~4.558 GFLOPS

    ai_range = np.logspace(-3, 2, 500)
    memory_roof = BW_GB_s * ai_range
    compute_roof = np.full_like(ai_range, PEAK_GFLOPS)
    roofline = np.minimum(memory_roof, compute_roof)

    fig, ax = plt.subplots(figsize=(10.0, 5.6), dpi=300)
    ridge_ai = PEAK_GFLOPS / BW_GB_s  # 2.526 FLOP/B

    # Sombreado de regiones de cuello de botella
    ax.axvspan(1e-3, ridge_ai, alpha=0.04, color='#2980b9', zorder=0)
    ax.axvspan(ridge_ai, 1e2, alpha=0.04, color='#c0392b', zorder=0)

    # Curvas teóricas de la arquitectura
    ax.loglog(ai_range, memory_roof, color='#2980b9', linewidth=1.4, linestyle='--', label=f'Techo Memoria ({BW_GB_s:.0f} GB/s)', zorder=2)
    ax.loglog(ai_range, compute_roof, color='#c0392b', linewidth=1.4, linestyle='--', label=f'Techo Cómputo ({PEAK_GFLOPS:.0f} GFLOPS)', zorder=2)
    ax.loglog(ai_range, roofline, color='#2c3e50', linewidth=2.8, label='Roofline Alcanzable', zorder=3)

    # Línea divisoria de Ridge Point
    ax.axvline(ridge_ai, color='#8e44ad', linewidth=1.3, linestyle=':', zorder=3)
    ax.text(ridge_ai * 1.15, 0.003, f'Ridge Point\n{ridge_ai:.2f} FLOP/B', fontsize=8.5, fontweight='bold', color='#8e44ad',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#f4ecf7', edgecolor='#8e44ad', alpha=0.92), zorder=5)

    # Puntos medidos experimentalmente
    ax.scatter(ai_counts, gflops_counts, s=170, color='#27ae60', edgecolors='black', linewidths=1.3, zorder=6, label='get_counts()')
    ax.scatter(ai_update, gflops_update, s=170, color='#e67e22', edgecolors='black', linewidths=1.3, zorder=6, label='update_grid()')

    # Anotaciones con diseño limpio y flechas suaves
    ax.annotate('Recuento de Estados\n(0.056 FLOP/B, 0.28 GFLOPS)',
                xy=(ai_counts, gflops_counts), xytext=(ai_counts * 2.3, gflops_counts * 0.15),
                fontsize=8.5, fontweight='bold', color='#1e8449',
                arrowprops=dict(arrowstyle='->', color='#27ae60', lw=1.3, connectionstyle='arc3,rad=-0.1'),
                bbox=dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor='#27ae60', alpha=0.95), zorder=7)

    ax.annotate('Actualización de Celdas\n(0.300 FLOP/B, 4.56 GFLOPS)',
                xy=(ai_update, gflops_update), xytext=(ai_update * 2.5, gflops_update * 0.25),
                fontsize=8.5, fontweight='bold', color='#d35400',
                arrowprops=dict(arrowstyle='->', color='#e67e22', lw=1.3, connectionstyle='arc3,rad=0.1'),
                bbox=dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor='#e67e22', alpha=0.95), zorder=7)

    # Etiquetas del fondo
    ax.text(0.002, 35, 'ZONA MEMORY-BOUND\n(Limitado por Ancho de Banda)', fontsize=8.5, fontweight='bold', color='#2980b9', alpha=0.6)
    ax.text(5.0, 12, 'ZONA COMPUTE-BOUND\n(Limitado por CPU/ALU)', fontsize=8.5, fontweight='bold', color='#c0392b', alpha=0.6)

    ax.set_xlabel('Intensidad Aritmética (FLOP/Byte)', fontweight='bold', fontsize=11)
    ax.set_ylabel('Rendimiento Alcanzado (GFLOPS)', fontweight='bold', fontsize=11)
    ax.set_title('Modelo Roofline: Ambos Kernels son Memory-Bound (Intel Core i5-12400)', fontweight='bold', pad=14, fontsize=12)

    ax.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#cccccc', framealpha=0.95, fontsize=8.5, ncol=2)
    ax.set_xlim(1e-3, 1e2)
    ax.set_ylim(1e-3, 250)
    ax.grid(True, which="both", ls="--", lw=0.4, alpha=0.5)

    plt.tight_layout()
    _add_footnote(fig, [src], notes='Ancho de banda DDR4 (38 GB/s) y rendimiento teórico calculados para Intel Core i5-12400.')
    outfile = os.path.join(OUTPUT_DIR, 'fig16_roofline_model.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 17: VECTORIZACIÓN POR KERNEL
# ==============================================================================
def plot_fig17_vectorization_analysis():
    src = 'results/simd/vec_report.txt'
    kernels = ['update_grid\n(Actualización)', 'get_counts\n(Recuento)']
    pct_vec   = [0.0,  15.0]
    pct_scalar= [100.0, 85.0]

    x = np.arange(len(kernels))
    width = 0.55

    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    ax.bar(x, pct_scalar, width, label='Escalar (sin SIMD)', color=['#e74c3c', '#e67e22'], edgecolor='black', linewidth=0.8, alpha=0.88)
    ax.bar(x, pct_vec, width, bottom=pct_scalar, label='Vectorizado (SIMD/SLP)', color=['#27ae60', '#27ae60'], edgecolor='black', linewidth=0.8, alpha=0.88)

    causas = ['Fallo: rand() + powf()\nclobber memory (ASM volátil)\n→ 0% SIMD', 'SLP parcial: swap de punteros\nBucle principal: escalar\n→ ~15% cobertura SIMD']
    for i, causa in enumerate(causas):
        ax.text(x[i], 50, causa, ha='center', va='center', fontsize=9.5, fontweight='bold', color='white', bbox=dict(boxstyle='round,pad=0.4', facecolor='#2c3e50', alpha=0.85))

    ax.text(x[1], pct_scalar[1] + pct_vec[1]/2, '15%', ha='center', va='center', fontsize=10, fontweight='bold', color='white')

    ax.annotate('Potencial si se elimina rand()+powf():\n→ hasta ~80% vectorizable', xy=(0, 100), xytext=(0.35, 85),
                fontsize=8.5, color='#27ae60', fontweight='bold', arrowprops=dict(arrowstyle='->', color='#27ae60', lw=1.5),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#27ae60', alpha=0.9))

    ax.set_ylim(0, 115)
    ax.set_ylabel('Cobertura del Bucle (%)', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(kernels, fontweight='bold', fontsize=10.5)
    ax.set_title('Análisis de Vectorización SIMD por Kernel (Según informe GCC -fopt-info-vec-all)', fontweight='bold', pad=12)
    ax.legend(loc='upper right', fontsize=9.5, frameon=True)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_yticklabels(['0%', '20%', '40%', '60%', '80%', '100%'])

    plt.tight_layout()
    _add_footnote(fig, [src, 'src/simulador.c'])
    outfile = os.path.join(OUTPUT_DIR, 'fig17_vectorization_analysis.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 18: SPEEDUP DE LTO POR POLÍTICA
# ==============================================================================
def plot_fig18_lto_speedup_per_policy():
    files = ['results/flags/03.txt', 'results/lto/lto.txt']
    d_o3  = parse_benchmark_file(files[0])
    d_lto = parse_benchmark_file(files[1])

    policies = ['LaissezFaire', 'Lockdown', 'RemoteWork', 'DynamicSignals']
    colors   = ['#e74c3c', '#8e44ad', '#3498db', '#f39c12']

    t_o3  = [d_o3['policy_phases'][p]['total_s']  for p in policies]
    t_lto = [d_lto['policy_phases'][p]['total_s'] for p in policies]
    sp_total = [a/b for a, b in zip(t_o3, t_lto)]

    gc_o3  = [d_o3['policy_phases'][p]['counts_s']  for p in policies]
    gc_lto = [d_lto['policy_phases'][p]['counts_s'] for p in policies]
    sp_gc  = [a/b for a, b in zip(gc_o3, gc_lto)]

    x = np.arange(len(policies))
    width = 0.38

    fig, ax = plt.subplots(figsize=(9.8, 5.2))
    ax.bar(x - width/2, sp_total, width, label='Speedup Total de Política', color=colors, edgecolor='black', linewidth=0.8, alpha=0.88)
    ax.bar(x + width/2, sp_gc, width, label='Speedup solo en Recuento de Estados', color=colors, edgecolor='black', linewidth=0.8, alpha=0.5, hatch='//')

    ax.axhline(1.0, color='black', linewidth=1.0, linestyle='--', alpha=0.5)

    for i, (st, sg) in enumerate(zip(sp_total, sp_gc)):
        ax.text(x[i] - width/2, st + 0.04, f'{st:.2f}×', ha='center', va='bottom', fontsize=9.5, fontweight='bold', color=colors[i],
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=colors[i], alpha=0.9))
        ax.text(x[i] + width/2, sg + 0.04, f'{sg:.2f}×', ha='center', va='bottom', fontsize=9.5, fontweight='bold', color=colors[i],
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=colors[i], alpha=0.9))

    ax.set_ylabel('Speedup (LTO vs -O3)', fontweight='bold')
    ax.set_xlabel('Política Sanitaria', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(policies, fontweight='bold')
    ax.set_ylim(0, max(sp_gc) * 1.30)
    ax.set_title('Impacto de LTO (-O3+native+flto) por Política: Aceleración Inter-Módulo', fontweight='bold', pad=12)
    ax.legend(loc='upper right', fontsize=9.5, frameon=True)

    plt.tight_layout()
    _add_footnote(fig, files)
    outfile = os.path.join(OUTPUT_DIR, 'fig18_lto_speedup_per_policy.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 19: LOCALIDAD ESPACIAL Y CACHÉ
# ==============================================================================
def plot_fig19_spatial_locality_cache():
    files = ['results/flags/03.txt', 'results/size/ciudad.txt', 'results/size/provincia.txt', 'results/size/comunidad.txt']
    configs = [('Ciudad\n591×591', 591*591, 475.09), ('Provincia\n1414×1414', 1414*1414, 484.62), ('Comunidad\n2258×2258', 2258*2258, 464.81)]
    labels = [c[0] for c in configs]
    cells  = [c[1] for c in configs]
    mcups  = [c[2] for c in configs]

    bytes_per_cell = 1 + 4 + 4
    wss_mb = [(n * bytes_per_cell * 3) / 1e6 for n in cells]

    L1_mb, L2_mb, L3_mb = 0.288, 1.25, 18.0
    x = np.arange(len(labels))
    color_bars = ['#3498db', '#f39c12', '#e74c3c']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 5.0))

    ax1.bar(x, wss_mb, color=color_bars, edgecolor='black', linewidth=0.8, alpha=0.85, width=0.55)
    ax1.axhline(L1_mb, color='#27ae60', linewidth=2.0, linestyle='--', label=f'L1d = {L1_mb*1024:.0f} KiB', zorder=3)
    ax1.axhline(L2_mb, color='#e67e22', linewidth=2.0, linestyle='--', label=f'L2 = {L2_mb*1024:.0f} MiB', zorder=3)
    ax1.axhline(L3_mb, color='#c0392b', linewidth=2.0, linestyle='--', label=f'L3 = {L3_mb:.0f} MiB', zorder=3)

    for i, (w, m) in enumerate(zip(wss_mb, mcups)):
        ax1.text(x[i], w + 0.6, f'{w:.1f} MB', ha='center', va='bottom', fontsize=10, fontweight='bold', color=color_bars[i],
                 bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor=color_bars[i], alpha=0.9))

    ax1.set_ylabel('Tamaño del Conjunto de Trabajo (MB)', fontweight='bold')
    ax1.set_xlabel('Configuración de Simulación', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontweight='bold')
    ax1.set_ylim(0, max(wss_mb) * 1.25)
    ax1.set_title('A: Working Set Size vs. Jerarquía de Caché', fontweight='bold')
    ax1.legend(loc='upper left', fontsize=9, frameon=True)

    ax2.bar(x, mcups, color=color_bars, edgecolor='black', linewidth=0.8, alpha=0.85, width=0.55)
    ax2.axhline(np.mean(mcups), color='#8e44ad', linewidth=2.0, linestyle='--', label=f'Media: {np.mean(mcups):.1f} MCUPS')
    for i, m in enumerate(mcups):
        ax2.text(x[i], m + 2, f'{m:.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold', color=color_bars[i],
                 bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor=color_bars[i], alpha=0.9))

    ax2.set_ylabel('Throughput (MCUPS)', fontweight='bold')
    ax2.set_xlabel('Configuración de Simulación', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontweight='bold')
    ax2.set_ylim(440, max(mcups) * 1.12)
    ax2.set_title('B: Throughput Medido (Mallas > L3)', fontweight='bold')
    ax2.legend(loc='upper right', fontsize=9.5, frameon=True)

    plt.suptitle('Localidad Espacial y Jerarquía de Caché (Intel Core i5-12400)', fontweight='bold', fontsize=13, y=1.01)
    plt.tight_layout()
    _add_footnote(fig, files)
    outfile = os.path.join(OUTPUT_DIR, 'fig19_spatial_locality_cache.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 20: EFICIENCIA ENERGÉTICA
# ==============================================================================
def plot_fig20_energy_efficiency():
    configs = [
        ('-O0\n(base)', 249.00), ('-O1', 115.58), ('-O2', 110.58),
        ('-O3', 58.96), ('-O3\n+native', 63.84), ('-O3\n+LTO', 42.89), ('Max\nOpt', 42.78)
    ]
    files = ['results/flags/base.txt', 'results/flags/01.txt', 'results/flags/02.txt',
             'results/flags/03.txt', 'results/march/03+native.txt', 'results/lto/lto.txt', 'results/max_opt/max_opt.txt']
    
    TDP_W = 65.0
    labels = [c[0] for c in configs]
    times  = np.array([c[1] for c in configs])
    energy = times * TDP_W
    rel    = energy / energy[0]

    colors = ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#27ae60', '#1abc9c', '#16a085']

    fig, ax = plt.subplots(figsize=(10.0, 5.2))
    ax.bar(np.arange(len(labels)), rel, color=colors, edgecolor='black', linewidth=0.8, width=0.6, alpha=0.88)
    ax.axhline(1.0, color='black', linewidth=1.0, linestyle='--', alpha=0.5, label='Referencia -O0 (100%)')

    for i, (r, t) in enumerate(zip(rel, times)):
        ax.text(i, r + 0.015, f'{r*100:.1f}%\n({t*TDP_W:.0f} J)', ha='center', va='bottom', fontsize=8.5, fontweight='bold', color=colors[i],
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=colors[i], alpha=0.9))

    ax.set_ylabel('Energía Relativa (respecto a -O0)', fontweight='bold')
    ax.set_xlabel('Configuración de Compilación', fontweight='bold')
    ax.set_xticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, fontweight='bold')
    ax.set_ylim(0, 1.35)
    ax.set_yticks([0, 0.25, 0.50, 0.75, 1.0])
    ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'])
    ax.set_title(f'Eficiencia Energética Estimada por Configuración (TDP bajo carga: {TDP_W:.0f} W — i5-12400)', fontweight='bold', pad=12)
    ax.legend(loc='upper right', fontsize=9.5)

    ax.annotate('', xy=(6, rel[6] + 0.02), xytext=(0, rel[0] - 0.02), arrowprops=dict(arrowstyle='<->', color='#2c3e50', lw=1.8))
    ax.text(3.0, 0.65, f'Ahorro: {(1-rel[6])*100:.1f}% de energía\ncon Max Opt vs -O0', ha='center', va='center', fontsize=9.5, fontweight='bold', color='#2c3e50',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#ecf0f1', edgecolor='#2c3e50', alpha=0.9))

    plt.tight_layout()
    _add_footnote(fig, files, notes='Estimación de consumo basado en el TDP de 65W sostenido durante el tiempo de ejecución.')
    outfile = os.path.join(OUTPUT_DIR, 'fig20_energy_efficiency.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 21: INTENSIDAD ARITMÉTICA REOPTIMIZADA
# ==============================================================================
def plot_fig21_arithmetic_intensity():
    src = 'src/simulador.c'
    fases = [
        'get_counts()\n(Recuento de vecinos)',
        'update_grid()\n(Celda SUSCEPTIBLE sin contagio)',
        'update_grid()\n(Celda SUSCEPTIBLE con contagio)',
        'update_grid()\n(Celda RECOVERED inmune)',
        'update_grid()\n(Celda INFECTED - rand + pow)',
    ]
    ai_vals = [2/36, 1/9, 8/40, 1/4, 4/12]  # Values: 0.056, 0.111, 0.200, 0.250, 0.333
    colors  = ['#3498db', '#2ecc71', '#e67e22', '#9b59b6', '#e74c3c']

    fig, ax = plt.subplots(figsize=(10.0, 5.0), dpi=300)
    y = np.arange(len(fases))
    
    # Dibujar barras
    ax.barh(y, ai_vals, color=colors, edgecolor='#2c3e50', linewidth=0.8, height=0.55, alpha=0.9, zorder=3)

    # Etiquetas numéricas limpias a la derecha de cada barra
    for i, v in enumerate(ai_vals):
        ax.text(v + 0.008, i, f'{v:.3f} FLOP/B', ha='left', va='center', fontsize=9.5, fontweight='bold', color='#2c3e50')

    # Zoom sobre el área relevante del programa (0 a 0.48 FLOP/B)
    ax.set_xlim(0, 0.48)

    # Banner informativo a la derecha indicando la distancia con el Ridge Point
    ax.text(0.46, 2.0, 'Ridge Point (i5-12400):\n2.53 FLOP/B ->\n\n[Todas las rutas son\n 100% Memory-Bound]',
            ha='right', va='center', fontsize=9, fontweight='bold', color='#8e44ad',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#f4ecf7', edgecolor='#8e44ad', linewidth=1.2, alpha=0.95), zorder=5)

    # Fondo suave indicando zona Memory-Bound
    ax.axvspan(0, 0.48, color='#ebf5fb', alpha=0.4, zorder=0)

    ax.set_xlabel('Intensidad Aritmética (FLOP/Byte)', fontweight='bold', fontsize=11)
    ax.set_yticks(y)
    ax.set_yticklabels(fases, fontsize=9.5, fontweight='bold', color='#2c3e50')
    ax.set_title('Intensidad Aritmética Estimada por Ruta de Ejecución del Kernel', fontweight='bold', pad=14, fontsize=12)
    ax.grid(True, axis='x', linestyle='--', alpha=0.5, zorder=1)

    plt.tight_layout()
    _add_footnote(fig, [src], notes='Estimación de FLOP/Byte basada en el análisis del código fuente de los bucles principales.')
    outfile = os.path.join(OUTPUT_DIR, 'fig21_arithmetic_intensity.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 22: PROYECCIÓN DE ESCALADO
# ==============================================================================
def plot_fig22_scaling_projection():
    files = ['results/flags/03.txt', 'results/size/ciudad.txt', 'results/size/provincia.txt', 'results/size/comunidad.txt']
    pops   = np.array([349281, 1999396, 5098564])
    times  = np.array([58.96, 385.30, 1002.61])

    slope, intercept = np.polyfit(np.log10(pops), np.log10(times), 1)
    p_range = np.logspace(np.log10(300000), np.log10(50_000_000), 300)
    t_fit   = 10 ** (slope * np.log10(p_range) + intercept)

    N_l3_overflow = (18.0 * 1e6) / (9 * 3)

    fig, ax = plt.subplots(figsize=(10.0, 5.4))
    ax.scatter(pops, times, s=150, zorder=5, color=['#3498db', '#f39c12', '#e74c3c'], edgecolors='black', linewidths=1.2, label='Mediciones reales')
    ax.plot(p_range, t_fit, color='#2c3e50', linewidth=2.2, linestyle='--', label=f'Ajuste potencial (pendiente={slope:.2f})')

    ax.axvline(N_l3_overflow, color='#e74c3c', linewidth=1.8, linestyle=':', label=f'Desbordamiento L3 (~{N_l3_overflow/1e6:.1f} M hab)')
    ax.axvline(47_000_000, color='#8e44ad', linewidth=1.8, linestyle=':', label='Escala nacional (~47 M hab)')

    point_labels = ['Ciudad\n(349K hab)', 'Provincia\n(2.0M hab)', 'Comunidad\n(5.1M hab)']
    pcolors = ['#3498db', '#f39c12', '#e74c3c']
    for i, (p, t, lbl, col) in enumerate(zip(pops, times, point_labels, pcolors)):
        ax.annotate(f'{lbl}\n{t:.0f} s', xy=(p, t), xytext=(p * 1.6, t * 0.65),
                    fontsize=8.5, fontweight='bold', color=col, arrowprops=dict(arrowstyle='->', color=col, lw=1.3),
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=col, alpha=0.9))

    t_national = 10 ** (slope * np.log10(47_000_000) + intercept)
    ax.scatter([47_000_000], [t_national], s=180, marker='*', color='#8e44ad', zorder=6, edgecolors='black', linewidths=1.0, label=f'Proyección España: {t_national:.0f} s')

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Población Simulada (habitantes)', fontweight='bold')
    ax.set_ylabel('Tiempo Total de Ejecución (s)', fontweight='bold')
    ax.set_title('Proyección del Tiempo de Simulación a Escala de Población', fontweight='bold', pad=12)
    ax.legend(loc='upper left', fontsize=8.5, frameon=True)

    from matplotlib.ticker import FuncFormatter
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x/1e6:.0f}M' if x >= 1e6 else f'{x/1e3:.0f}K' if x >= 1e3 else str(int(x))))

    plt.tight_layout()
    _add_footnote(fig, files, notes='Ajuste de regresión potencial log-log extrapolado a escala de población nacional.')
    outfile = os.path.join(OUTPUT_DIR, 'fig22_scaling_projection.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 23: PIPELINE DE COMPILACIÓN COMPLETO
# ==============================================================================
def plot_fig23_full_optimization_pipeline():
    config_files = [
        ('-O0 (base)',               'results/flags/base.txt'),
        ('-O1',                      'results/flags/01.txt'),
        ('-O2',                      'results/flags/02.txt'),
        ('-Os',                      'results/flags/Os.txt'),
        ('-O3',                      'results/flags/03.txt'),
        ('-Ofast',                   'results/flags/0fast.txt'),
        ('-O3+native',               'results/march/03+native.txt'),
        ('-O3+native+FMA',           'results/march/03+native+fma.txt'),
        ('Unroll (-funroll-loops)',  'results/unroll/unroll.txt'),
        ('Ancho Vec. 256b',          'results/vector_width/w256.txt'),
        ('Ancho Vec. 512b',          'results/vector_width/w512.txt'),
        ('Cost Model (unlimited)',   'results/cost_model/cost_unlimited.txt'),
        ('SIMD (-msse4.2)',          'results/simd/vec.txt'),
        ('PGO (-fprofile-use)',      'results/pgo/pgo.txt'),
        ('-O3+native+LTO',           'results/lto/lto.txt'),
        ('Max Opt (LTO+O3+native)',  'results/max_opt/max_opt.txt'),
    ]

    configs, files_used = [], []
    for label, fpath in config_files:
        d = parse_benchmark_file(fpath)
        if d and d['wall_s'] is not None and d['mcups'] is not None:
            configs.append((label, d['wall_s'], d['mcups']))
            files_used.append(fpath)

    configs_sorted = sorted(configs, key=lambda c: c[2])
    labels = [c[0] for c in configs_sorted]
    times  = [c[1] for c in configs_sorted]
    mcups  = [c[2] for c in configs_sorted]

    cmap = plt.get_cmap('RdYlGn')
    norm_mcups = [(m - min(mcups)) / (max(mcups) - min(mcups)) for m in mcups]
    colors = [cmap(v) for v in norm_mcups]

    x = np.arange(len(labels))
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.5, 10.0), sharex=False)

    ax1.barh(x, mcups, color=colors, edgecolor='black', linewidth=0.6, height=0.65, alpha=0.9)
    ax1.set_xlabel('Rendimiento del Kernel (MCUPS)', fontweight='bold')
    ax1.set_title('A: Throughput del Kernel — Mayor es mejor', fontweight='bold')
    for i, m in enumerate(mcups):
        ax1.text(m + 2, i, f'{m:.1f}', va='center', ha='left', fontsize=8.5, fontweight='bold')
    ax1.set_xlim(0, max(mcups) * 1.12)
    ax1.set_yticks(x)
    ax1.set_yticklabels(labels, fontsize=8.8)

    ax2.barh(x, times, color=colors, edgecolor='black', linewidth=0.6, height=0.65, alpha=0.9)
    ax2.set_xlabel('Tiempo Total de Ejecución (s)', fontweight='bold')
    ax2.set_title('B: Tiempo de Ejecución — Menor es mejor', fontweight='bold')
    for i, t in enumerate(times):
        ax2.text(t + 1.5, i, f'{t:.1f} s', va='center', ha='left', fontsize=8.5, fontweight='bold')
    ax2.set_xlim(0, max(times) * 1.12)
    ax2.set_yticks(x)
    ax2.set_yticklabels(labels, fontsize=8.8)

    plt.suptitle('Pipeline Completo de Optimización: Comparativa de Todas las Configuraciones', fontweight='bold', fontsize=12.5, y=1.01)
    plt.tight_layout()
    _add_footnote(fig, files_used)
    outfile = os.path.join(OUTPUT_DIR, 'fig23_full_optimization_pipeline.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == '__main__':
    print("=================================================================")
    print("Regenerando 23 figuras científicas homogenizadas...")
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
    plot_fig11_speedup_by_kernel_component()
    plot_fig12_memory_hierarchy_working_set()
    plot_fig13_policy_phase_disparity()
    plot_fig14_amdahl_parallel_projection()
    plot_fig15_monte_carlo_dispersion_ranges()
    plot_fig16_roofline_model()
    plot_fig17_vectorization_analysis()
    plot_fig18_lto_speedup_per_policy()
    plot_fig19_spatial_locality_cache()
    plot_fig20_energy_efficiency()
    plot_fig21_arithmetic_intensity()
    plot_fig22_scaling_projection()
    plot_fig23_full_optimization_pipeline()
    print("=================================================================")
    print(f"¡Las 23 figuras han sido generadas e integradas en: {OUTPUT_DIR}/ !")
    print("=================================================================")