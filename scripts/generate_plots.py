#!/usr/bin/env python3
"""
Script de generación de gráficas científicas para la Memoria de Práctica 2
Ingeniería de los Computadores - Curso 2026-27 (Universidad de Alicante)
Genera 15 figuras de alta resolución (300 DPI) con maquetación limpia y sin colisiones.
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
# 2. HELPER: PIE DE NOTA CON FUENTES
# ==============================================================================
def _add_footnote(fig, sources, notes=''):
    """
    Añade un pie de nota en la parte inferior de la figura indicando
    los archivos de resultados de los que provienen los datos.

    Args:
        fig:     objeto matplotlib Figure
        sources: lista de rutas relativas a los archivos fuente
        notes:   texto adicional opcional (datos calculados/estimados)
    """
    src_str = '  ·  '.join(sources)
    lines = [f'Fuente de datos: {src_str}']
    if notes:
        lines.append(f'Nota: {notes}')
    text = '\n'.join(lines)
    fig.text(
        0.01, -0.03, text,
        ha='left', va='top', fontsize=7.5, color='#555555', style='italic',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#f8f9fa', edgecolor='#dee2e6', alpha=0.92)
    )

# ==============================================================================
# FIG 1: FLAGS DE COMPILACIÓN - SUBPLOTS SEPARADOS (TIEMPO Y SPEEDUP)
# (Etiqueta debajo del punto rojo y sin líneas que pisen números)
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

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.8))
    x = np.arange(len(flags))

    # Panel 1: Tiempo de Ejecución
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

    # Panel 2: Speedup (Ganancia en Velocidad) con etiqueta debajo del punto rojo
    ax2.plot(x, speedups, color='#c0392b', marker='o', linewidth=2.4, markersize=8, zorder=3)
    ax2.set_ylabel('Speedup (respecto a -O0)', fontweight='bold', color='#c0392b')
    ax2.set_xlabel('Nivel de Optimización GCC', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(flags, fontweight='bold')
    ax2.set_ylim(0.0, max(speedups) * 1.35)
    ax2.set_title('B: Ganancia en Velocidad (Mayor es mejor)', fontweight='bold')

    # Etiquetas claramente DEBAJO del punto rojo, con fondo blanco limpio
    for i, s in enumerate(speedups):
        ax2.annotate(f"{s:.2f}x", (x[i], s), textcoords="offset points", xytext=(0, -22),
                     ha='center', va='top', fontsize=9.5, fontweight='bold', color='#c0392b',
                     bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor='#c0392b', alpha=0.95))

    plt.suptitle('Impacto de los Niveles de Optimización GCC (Caso Ciudad, 200 días)',
                 fontweight='bold', fontsize=13, y=1.01)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig01_flags_speedup.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 2: THROUGHPUT DEL KERNEL (MCUPS) Y PRODUCTIVIDAD (SIMS/S)
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
    ax1.set_ylabel('Rendimiento del Kernel (MCUPS - Millones Celdas/s)', fontweight='bold', color='#2980b9')
    ax1.set_xlabel('Nivel de Optimización GCC', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(flags, fontweight='bold')
    ax1.set_ylim(0, max(mcups) * 1.25)

    for bar in bars1:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., h + 10, f"{h:.1f}",
                 ha='center', va='bottom', fontsize=9, fontweight='bold', color='#2980b9')

    ax2 = ax1.twinx()
    bars2 = ax2.bar(x + width/2, sims, width, label='Simulaciones / segundo', color='#e67e22', edgecolor='black', linewidth=0.7)
    ax2.set_ylabel('Productividad (Simulaciones Monte Carlo / s)', fontweight='bold', color='#e67e22')
    ax2.set_ylim(0, max(sims) * 1.30)
    ax2.grid(False)

    for bar in bars2:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., h + 0.15, f"{h:.2f}",
                 ha='center', va='bottom', fontsize=9, fontweight='bold', color='#d35400')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True)

    plt.title('Rendimiento del Kernel (MCUPS) y Productividad Global por Nivel de Optimización',
              fontweight='bold', pad=14)
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

    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    p1 = ax.bar(x, t_update, width, label='Update Grid (Actualización de Celdas)', color='#3498db', edgecolor='black', linewidth=0.7)
    p2 = ax.bar(x, t_counts, width, bottom=t_update, label='Get Counts (Recuento de Estados)', color='#e74c3c', edgecolor='black', linewidth=0.7)
    bottom_analytics = np.array(t_update) + np.array(t_counts)
    p3 = ax.bar(x, t_analytics, width, bottom=bottom_analytics, label='Analytics (Impacto Sanitario y Económico)', color='#2ecc71', edgecolor='black', linewidth=0.7)

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

    plt.title('Desglose Temporal por Fases del Programa y Demostración de la Ley de Amdahl',
              fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig03_profiling_phases_stacked.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 4: COMPARATIVA DE FLAGS AVANZADOS (SIN PALABRAS RARAS, LEYENDA SIN PISAR)
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
    times = [parse_benchmark_file(e[1])['wall_s'] for e in experiments]
    
    colors = []
    for n in names:
        if 'flto' in n or 'max_opt' in n:
            colors.append('#27ae60')
        elif 'PGO' in n:
            colors.append('#e74c3c')
        elif 'Referencia' in n:
            colors.append('#34495e')
        else:
            colors.append('#3498db')

    fig, ax = plt.subplots(figsize=(10.0, 5.6))
    y = np.arange(len(names))
    bars = ax.barh(y, times, height=0.62, color=colors, edgecolor='black', linewidth=0.7)

    ax.set_xlabel('Tiempo Total de Ejecución (s) - [Menor es mejor]', fontweight='bold')
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9.5, fontweight='bold')
    ax.invert_yaxis()
    # Margen amplio a la derecha para que ningún número choque con nada
    ax.set_xlim(0, 115)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 1.2, bar.get_y() + bar.get_height()/2., f"{w:.2f} s",
                ha='left', va='center', fontsize=9.5, fontweight='bold', color='#2c3e50',
                bbox=dict(boxstyle='square,pad=0.15', facecolor='white', edgecolor='none', alpha=0.9), zorder=5)

    ax.axvline(times[0], color='#e67e22', linestyle='--', linewidth=1.5, label=f'Referencia -O3 ({times[0]:.1f} s)', zorder=2)
    # Leyenda situada en la esquina superior derecha donde no hay barras
    ax.legend(loc='upper right', frameon=True, fontsize=10)

    plt.title('Comparativa de Opciones Avanzadas de Compilación en GCC 13.2 (Intel Core i5-12400)',
              fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig04_advanced_opts_ablation.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 5: IMPACTO DE LTO (-flto): OPTIMIZACIÓN GLOBAL SIN COLISIONES
# ==============================================================================
def plot_fig5_lto_impact():
    cases = [
        '-O3 Referencia',
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

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 5.0))

    # Panel A: get_counts
    colors_c = ['#e74c3c', '#e74c3c', '#e74c3c', '#27ae60', '#27ae60']
    bars_c = ax1.bar(x, t_counts, width=0.55, color=colors_c, edgecolor='black', linewidth=0.8)
    ax1.set_ylabel('Tiempo en get_counts() (s)', fontweight='bold', color='#c0392b')
    ax1.set_xticks(x)
    ax1.set_xticklabels(cases, rotation=25, ha='right', fontsize=9, fontweight='bold')
    ax1.set_title('A: Tiempo en get_counts() (Recuento)', fontweight='bold')
    ax1.set_ylim(0, 26)

    for bar in bars_c:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., h + 0.5, f"{h:.2f} s",
                 ha='center', va='bottom', fontsize=9, fontweight='bold')
        
    # Anotación en Panel A colocada limpia arriba sin tapar ningún número ni barra
    ax1.annotate('Aceleración de 13.8x\n(inlining entre archivos .c)',
                 xy=(3, 2.5), xytext=(3.3, 16.5),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                 fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#d4efdf', edgecolor='#27ae60'))

    # Panel B: update_grid
    colors_u = ['#3498db', '#3498db', '#3498db', '#2980b9', '#2980b9']
    bars_u = ax2.bar(x, t_update, width=0.55, color=colors_u, edgecolor='black', linewidth=0.8)
    ax2.set_ylabel('Tiempo en update_grid() (s)', fontweight='bold', color='#2980b9')
    ax2.set_xticks(x)
    ax2.set_xticklabels(cases, rotation=25, ha='right', fontsize=9, fontweight='bold')
    ax2.set_title('B: Tiempo en update_grid() (Llamadas a rand/pow)', fontweight='bold')
    ax2.set_ylim(0, 52)

    for bar in bars_u:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., h + 0.8, f"{h:.1f} s",
                 ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.suptitle('Efecto de LTO (-flto): Inlining entre Módulos en Recuento vs Actualización de Celdas',
                 fontweight='bold', fontsize=12.5, y=1.02)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig05_lto_impact_reduction_vs_stencil.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 6: ESCALABILIDAD DEL TAMAÑO DEL PROBLEMA Y JERARQUÍA DE MEMORIA (SUBPLOTS LIMPIOS)
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

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 5.0))
    x = np.arange(len(scales))

    # Panel A: Tiempo de ejecución
    bars = ax1.bar(x, times, width=0.52, color='#34495e', edgecolor='black', linewidth=0.8)
    ax1.set_ylabel('Tiempo Total de Ejecución (s)', fontweight='bold', color='#2c3e50')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"{scales[i]}\n({pops[i]:,} celdas)" for i in range(3)], fontsize=9.5, fontweight='bold')
    ax1.set_ylim(0, max(times) * 1.22)
    ax1.set_title('A: Tiempo Total vs Tamaño del Problema', fontweight='bold')

    for bar in bars:
        h = bar.get_height()
        minutes = h / 60
        txt = f"{h:.1f} s\n({minutes:.1f} min)" if minutes >= 1 else f"{h:.1f} s"
        ax1.text(bar.get_x() + bar.get_width()/2., h + 20, txt,
                 ha='center', va='bottom', fontsize=9, fontweight='bold', color='#2c3e50')

    # Panel B: Rendimiento en MCUPS
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

    # Anotación en Panel B limpia y despejada
    ax2.annotate('Comunidad supera Caché L3 (18 MB):\n1 buffer = 20.4 MB\n→ Caída en MCUPS por accesos a RAM',
                 xy=(2, mcups[2]), xytext=(0.75, 442),
                 arrowprops=dict(facecolor='#c0392b', shrink=0.08, width=1.2, headwidth=6),
                 fontsize=8.5, fontweight='bold', color='#c0392b',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='#fadbd8', edgecolor='#c0392b'))

    plt.suptitle('Escalabilidad del Censo y Comportamiento Frente a la Jerarquía de Caché',
                 fontweight='bold', fontsize=13, y=1.01)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig06_scalability_problem_size_memory.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 7: COMPROMISO COSTE VS MORTALIDAD (SIN PALABRA PARETO, SIN SOLAPAMIENTO)
# ==============================================================================
def plot_fig7_pareto_frontier():
    data = parse_benchmark_file('results/flags/03.txt')['policies']
    policies = ['LaissezFaire', 'RemoteWork', 'DynamicSignals', 'Lockdown']
    colors = {'LaissezFaire': '#e74c3c', 'RemoteWork': '#f39c12', 'DynamicSignals': '#3498db', 'Lockdown': '#8e44ad'}

    fig, ax = plt.subplots(figsize=(9.2, 5.4))

    for p in policies:
        d = data[p]
        ax.errorbar(d['cost_mean'], d['deaths_mean'],
                    xerr=d['cost_std'], yerr=d['deaths_std'],
                    fmt='o', markersize=9, color=colors[p], ecolor=colors[p], elinewidth=1.6, capsize=4,
                    label=f"{p} (media ± σ)", zorder=4)

    # Posicionamiento cuidadoso de cada recuadro para que NO choquen entre sí ni con puntos
    # 1. LaissezFaire (arriba a la izquierda)
    d = data['LaissezFaire']
    ax.annotate(f"LaissezFaire\nCoste: {d['cost_mean']:.0f} M€\nMuertes: {d['deaths_mean']:.0f}",
                (d['cost_mean'], d['deaths_mean']), textcoords="offset points", xytext=(25, 20),
                ha='left', va='bottom', fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=colors['LaissezFaire'], alpha=0.95),
                arrowprops=dict(arrowstyle='->', color=colors['LaissezFaire'], lw=1.2))

    # 2. RemoteWork (centro-arriba)
    d = data['RemoteWork']
    ax.annotate(f"RemoteWork\nCoste: {d['cost_mean']:.0f} M€\nMuertes: {d['deaths_mean']:.0f}",
                (d['cost_mean'], d['deaths_mean']), textcoords="offset points", xytext=(20, 25),
                ha='left', va='bottom', fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=colors['RemoteWork'], alpha=0.95),
                arrowprops=dict(arrowstyle='->', color=colors['RemoteWork'], lw=1.2))

    # 3. DynamicSignals (a la izquierda de su punto para no tocar a Lockdown)
    d = data['DynamicSignals']
    ax.annotate(f"DynamicSignals\nCoste: {d['cost_mean']:.0f} M€\nMuertes: {d['deaths_mean']:.0f}",
                (d['cost_mean'], d['deaths_mean']), textcoords="offset points", xytext=(-130, -10),
                ha='left', va='center', fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=colors['DynamicSignals'], alpha=0.95),
                arrowprops=dict(arrowstyle='->', color=colors['DynamicSignals'], lw=1.2))

    # 4. Lockdown (abajo a la derecha)
    d = data['Lockdown']
    ax.annotate(f"Lockdown\nCoste: {d['cost_mean']:.0f} M€\nMuertes: {d['deaths_mean']:.0f}",
                (d['cost_mean'], d['deaths_mean']), textcoords="offset points", xytext=(25, -20),
                ha='left', va='center', fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=colors['Lockdown'], alpha=0.95),
                arrowprops=dict(arrowstyle='->', color=colors['Lockdown'], lw=1.2))

    # Curva de tendencia de compromiso (sin la palabra Pareto)
    px = [data['LaissezFaire']['cost_mean'], data['RemoteWork']['cost_mean'], data['Lockdown']['cost_mean']]
    py = [data['LaissezFaire']['deaths_mean'], data['RemoteWork']['deaths_mean'], data['Lockdown']['deaths_mean']]
    ax.plot(px, py, color='#2c3e50', linestyle=':', linewidth=1.8, label='Curva de Compromiso (Coste vs Vidas)', zorder=2)

    ax.set_xlabel('Coste Económico Total (Millones de Euros - M€)', fontweight='bold')
    ax.set_ylabel('Mortalidad Acumulada (Número de Fallecidos)', fontweight='bold')
    ax.set_xlim(300, 6800)
    ax.set_ylim(5400, 8600)
    ax.legend(loc='upper right', frameon=True)

    plt.title('Compromiso entre Coste Económico y Vidas Humanas por Política (Alicante, 80 Réplicas)',
              fontweight='bold', pad=14)
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

    fig, ax1 = plt.subplots(figsize=(8.8, 5.0))

    bars1 = ax1.bar(x - width/2, icu_days, width, yerr=icu_err, capsize=4,
                    color='#c0392b', edgecolor='black', linewidth=0.8, label='Días Colapso UCI (media ± σ)')
    ax1.set_ylabel('Días de Colapso Hospitalario de UCI', fontweight='bold', color='#c0392b')
    ax1.set_xticks(x)
    ax1.set_xticklabels(policies, fontweight='bold')
    ax1.set_ylim(0, 58)  # Altura suficiente para que el texto no toque la leyenda

    # Texto de LaissezFaire
    ax1.text(x[0] - width/2, icu_days[0] + icu_err[0] + 2.0, f"{icu_days[0]:.1f} d",
             ha='center', va='bottom', fontsize=9, fontweight='bold', color='#c0392b')
    # Texto de RemoteWork colocado a la izquierda del error bar para no pisarse
    ax1.text(x[1] - width/2 - 0.12, 4.5, f"{icu_days[1]:.1f} d",
             ha='right', va='bottom', fontsize=9, fontweight='bold', color='#c0392b')
    # Texto de DynamicSignals y Lockdown
    ax1.text(x[2] - width/2, 1.5, f"{icu_days[2]:.1f} d", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#c0392b')
    ax1.text(x[3] - width/2, 1.5, f"{icu_days[3]:.1f} d", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#c0392b')

    ax2 = ax1.twinx()
    bars2 = ax2.bar(x + width/2, fatigue, width,
                    color='#8e44ad', edgecolor='black', linewidth=0.8, label='Fatiga Social de la Población')
    ax2.set_ylabel('Índice de Fatiga Social', fontweight='bold', color='#8e44ad')
    ax2.set_ylim(0, 1.6)
    ax2.grid(False)

    for bar in bars2:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., h + 0.04, f"{h:.2f}",
                 ha='center', va='bottom', fontsize=9, fontweight='bold', color='#8e44ad')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center', frameon=True, ncol=2)

    plt.title('Evaluación de Políticas: Saturación de Cuidados Intensivos vs Fatiga Social',
              fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig08_icu_collapse_and_fatigue.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 9: TIEMPO DE CPU POR POLÍTICA (SIN SOLAPAMIENTO DE TEXTO)
# ==============================================================================
def plot_fig9_compute_time_per_policy():
    data = parse_benchmark_file('results/flags/03.txt')['policies']
    policies = ['LaissezFaire', 'DynamicSignals', 'RemoteWork', 'Lockdown']
    times = [data[p]['compute_time_s'] for p in policies]

    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    colors = ['#27ae60', '#3498db', '#f39c12', '#e74c3c']
    bars = ax.bar(policies, times, width=0.52, color=colors, edgecolor='black', linewidth=0.8)

    ax.set_ylabel('Tiempo de Cómputo CPU (s) - [80 Réplicas]', fontweight='bold')
    ax.set_xlabel('Política Sanitaria Evaluada', fontweight='bold')
    ax.set_ylim(0, 24)  # Espacio superior amplio para que la anotación no toque nada

    base_time = times[0]
    for i, bar in enumerate(bars):
        h = bar.get_height()
        diff = ((h - base_time) / base_time) * 100
        diff_txt = f"(+{diff:.1f}%)" if diff > 0 else "(Ref)"
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.5, f"{h:.2f} s\n{diff_txt}",
                ha='center', va='bottom', fontsize=9.5, fontweight='bold')

    # Anotación en la zona superior libre sin solaparse con RemoteWork
    ax.annotate('En Lockdown la epidemia se alarga:\nMás celdas activas en la malla durante los 200 días\n→ +59.8% de operaciones de contagio ejecutadas',
                xy=(3, times[3]), xytext=(0.6, 19.5),
                arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
                fontsize=8.5, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#fcf3cf', edgecolor='#f39c12'))

    plt.title('Variabilidad del Tiempo de Cómputo según la Dinámica de la Simulación',
              fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig09_compute_time_per_policy.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 10: ESCALABILIDAD MULTIESCALA DE POLÍTICAS
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

    plt.suptitle('Consistencia Multiescala de las Políticas: Crecimiento Proporcional al Censo',
                 fontweight='bold', fontsize=12.5, y=1.01)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig10_multiscale_policy_impact.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 11: SPEEDUP ESPECÍFICO POR COMPONENTE DE CÓDIGO (SIN LÍNEAS QUE CORTEN TEXTO)
# ==============================================================================
def plot_fig11_speedup_by_kernel_component():
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

    fig, ax = plt.subplots(figsize=(9.4, 5.2))
    x = np.arange(len(configs))

    ax.plot(x, sc_list, marker='s', markersize=8, linewidth=2.4, color='#e74c3c', label='GetCounts (Recuento de Estados)', zorder=4)
    ax.plot(x, su_list, marker='o', markersize=8, linewidth=2.4, color='#3498db', label='UpdateGrid (Actualización de Celdas)', zorder=4)
    ax.plot(x, st_list, marker='^', markersize=8, linewidth=2.0, color='#2c3e50', linestyle='--', label='Speedup Total de la Aplicación', zorder=3)

    # Anotación GetCounts limpia arriba
    ax.annotate(f"{sc_list[-1]:.1f}x\n(LTO inlining)", xy=(x[-1], sc_list[-1]), xytext=(x[-1]-0.9, 16.5),
                arrowprops=dict(facecolor='#e74c3c', shrink=0.08, width=1, headwidth=5),
                fontsize=9, fontweight='bold', color='#c0392b',
                bbox=dict(boxstyle='round,pad=0.25', facecolor='#fadbd8', edgecolor='#e74c3c'))

    # Anotación UpdateGrid limpia sin ser cortada por la línea roja
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

    plt.title('Aceleración por Componente: Vectorización en Recuento vs Límite en Actualización',
              fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig11_speedup_by_kernel_component.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 12: MEMORIA OCUPADA VS LÍMITES DE CACHÉ L1/L2/L3 (SIN NÚMEROS CORTADOS)
# ==============================================================================
def plot_fig12_memory_hierarchy_working_set():
    scales = ['Ciudad\n(~350k)', 'Provincia\n(~2.0M)', 'Comunitat\n(~5.1M)']
    b_single = np.array([349281 * 4, 1999396 * 4, 5098564 * 4]) / (1024 * 1024)
    b_active = np.array([349281 * 8, 1999396 * 8, 5098564 * 8]) / (1024 * 1024)
    b_total  = np.array([349281 * 12, 1999396 * 12, 5098564 * 12]) / (1024 * 1024)

    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    x = np.arange(len(scales))
    width = 0.25

    bars1 = ax.bar(x - width, b_single, width, label='1 Buffer (current_grid)', color='#7fb3d5', edgecolor='black', linewidth=0.7)
    bars2 = ax.bar(x, b_active, width, label='2 Buffers Activos (current + next)', color='#2980b9', edgecolor='black', linewidth=0.7)
    bars3 = ax.bar(x + width, b_total, width, label='Memoria Total (3 arrays)', color='#1b4f72', edgecolor='black', linewidth=0.7)

    # Líneas de referencia de caché del Intel Core i5-12400
    ax.axhline(0.281, color='#8e44ad', linestyle=':', linewidth=1.5, label='Caché L1d Total (288 KiB)', zorder=1)
    ax.axhline(7.5, color='#e67e22', linestyle='--', linewidth=1.8, label='Caché L2 Total (7.5 MiB)', zorder=1)
    ax.axhline(18.0, color='#c0392b', linestyle='-', linewidth=2.2, label='Caché L3 Compartida (18.0 MiB)', zorder=1)

    # Números colocados con fondo blanco limpio para que ninguna línea los corte
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

    # Anotación en la zona libre superior derecha, apuntando al cuerpo de la barra
    ax.annotate('Comunidad: 1 solo buffer (20.4 MB) > L3 (18 MB)\n→ Tráfico forzado a Memoria Principal (RAM)\n→ Pérdida de rendimiento en MCUPS',
                xy=(2 - width, 12.0), xytext=(0.85, 52),
                arrowprops=dict(facecolor='#c0392b', shrink=0.08, width=1.2, headwidth=6),
                fontsize=8.5, fontweight='bold', color='#c0392b',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#fadbd8', edgecolor='#c0392b'), zorder=6)

    plt.title('Memoria Ocupada vs Capacidad Física de la Jerarquía de Caché (Intel Core i5-12400)',
              fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig12_memory_hierarchy_working_set.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 13: DESGLOSE DE FASES POR POLÍTICA (SIN LÍNEA DOTTED QUE CORTE NÚMEROS)
# ==============================================================================
def plot_fig13_policy_phase_disparity():
    d = parse_benchmark_file('results/flags/03.txt')['policy_phases']
    policies = ['LaissezFaire', 'DynamicSignals', 'RemoteWork', 'Lockdown']

    t_up = [d[p]['update_s'] for p in policies]
    t_co = [d[p]['counts_s'] for p in policies]

    x = np.arange(len(policies))
    width = 0.38

    fig, ax = plt.subplots(figsize=(9.0, 5.0))

    bars_up = ax.bar(x - width/2, t_up, width, label='Update Grid (Actualización de Celdas)', color='#3498db', edgecolor='black', linewidth=0.8)
    bars_co = ax.bar(x + width/2, t_co, width, label='Get Counts (Recuento de Estados)', color='#e74c3c', edgecolor='black', linewidth=0.8)

    # Etiquetas de Update Grid encima
    for bar in bars_up:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.35, f"{h:.2f} s",
                ha='center', va='bottom', fontsize=9, fontweight='bold', color='#2980b9')

    # Etiquetas de Get Counts con caja blanca para que la línea de promedio no las corte
    for bar in bars_co:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.35, f"{h:.2f} s",
                ha='center', va='bottom', fontsize=9, fontweight='bold', color='#c0392b',
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
                fontsize=8.5, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#fcf3cf', edgecolor='#f39c12'))

    plt.title('Comparativa de Fases: Recuento Invariante vs Variación en Actualización de Celdas',
              fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig13_policy_phase_disparity.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 14: PROYECCIÓN TEÓRICA DE AMDAHL (USA THREADS, SIN HEBRAS, RECUADRO LIMPIO)
# ==============================================================================
def plot_fig14_amdahl_parallel_projection():
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

    # Líneas verticales del Intel Core i5-12400 con badges superiores limpios
    ax.axvline(6, color='#2c3e50', linestyle='--', linewidth=1.4, alpha=0.6, zorder=1)
    ax.text(6, 27.5, '6 Cores Físicos', ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#2c3e50',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#eaeded', edgecolor='#2c3e50', alpha=0.95), zorder=5)

    ax.axvline(12, color='#2c3e50', linestyle='--', linewidth=1.4, alpha=0.6, zorder=1)
    ax.text(12, 27.5, '12 Threads (SMT)', ha='center', va='bottom', fontsize=8.5, fontweight='bold', color='#2c3e50',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#eaeded', edgecolor='#2c3e50', alpha=0.95), zorder=5)

    ax.set_ylabel('Speedup Teórico Máximo (Ley de Amdahl)', fontweight='bold')
    # Usa Threads en vez de hebras
    ax.set_xlabel('Número de Procesadores / Threads en Paralelo (p)', fontweight='bold')
    ax.set_xlim(1, 32)
    ax.set_ylim(0, 31)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.14), ncol=2, frameon=True, fontsize=9.0)

    # Anotación limpia en la zona superior libre sin pisar ninguna línea ni texto
    s6_lto = 1.0 / ((1.0 - f_lto) + f_lto / 6.0)
    ax.annotate(f"Speedup con 6 Cores = {s6_lto:.2f}x\n(Eficiencia: 85.5%)\nCon 12 Threads = 8.73x",
                xy=(6, s6_lto), xytext=(2.2, 12.5),
                arrowprops=dict(facecolor='#2980b9', shrink=0.08, width=1.2, headwidth=6),
                fontsize=9, fontweight='bold', color='#2980b9',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#ebf5fb', edgecolor='#2980b9'), zorder=6)

    plt.title('Proyección Teórica de la Ganancia Paralela (Ley de Amdahl) en Intel Core i5-12400',
              fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig14_amdahl_parallel_projection.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 15: DISPERSIÓN DE RESULTADOS EN MONTE CARLO (SIN COLISIÓN CON RANGOS)
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

    fig, ax = plt.subplots(figsize=(9.2, 5.2))

    for i in range(len(policies)):
        # Rango completo (min - max)
        ax.plot([x[i], x[i]], [mins[i], maxs[i]], color=colors[i], linewidth=2.5, alpha=0.5, zorder=2)
        ax.plot([x[i]-0.15, x[i]+0.15], [mins[i], mins[i]], color=colors[i], linewidth=2.0, alpha=0.7)
        ax.plot([x[i]-0.15, x[i]+0.15], [maxs[i], maxs[i]], color=colors[i], linewidth=2.0, alpha=0.7)

        # Intervalo media ± 1 sigma
        ax.errorbar(x[i], means[i], yerr=stds[i], fmt='o', markersize=8, color=colors[i],
                    ecolor='black', elinewidth=2.2, capsize=5, capthick=1.5, zorder=4)

        # Caja de datos situada 140 unidades POR ENCIMA del tope para que NO se toquen
        r_amp = maxs[i] - mins[i]
        ax.text(x[i], maxs[i] + 160, f"Rango: [{mins[i]} - {maxs[i]}]\nΔ = {r_amp} | σ = ±{stds[i]:.0f}",
                ha='center', va='bottom', fontsize=8.5, fontweight='bold', color=colors[i],
                bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor=colors[i], alpha=0.9))

    ax.set_ylabel('Mortalidad Acumulada (Fallecidos)', fontweight='bold')
    ax.set_xlabel('Política Sanitaria Evaluada', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(policies, fontweight='bold', fontsize=10)
    ax.set_ylim(4800, 9700)  # Límite superior holgado

    ax.plot([], [], color='black', marker='o', label='Media muestral ± 1 Desviación estándar (σ)')
    ax.plot([], [], color='gray', linewidth=2.5, label='Rango experimental completo [Mínimo - Máximo]')
    ax.legend(loc='lower left', frameon=True, fontsize=9)

    plt.title('Variabilidad de las 80 Réplicas: El Semáforo Reactivo Amortigua la Dispersión',
              fontweight='bold', pad=14)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig15_monte_carlo_dispersion_ranges.png')
    plt.savefig(outfile, dpi=300)
    plt.close()
    print(f"[OK] Generada: {outfile}")

# ==============================================================================
# FIG 16: MODELO ROOFLINE SIMPLIFICADO — LÍMITES DE MEMORIA Y CÓMPUTO
# ==============================================================================
def plot_fig16_roofline_model():
    """
    Roofline model para los dos kernels principales del simulador.
    Intensidad aritmética estimada a partir de la estructura de código:
      - get_counts: 1 suma de enteros + acceso a 9 celdas vecinas = ~2 FLOPS / 9*4 B = 0.056 FLOP/B
      - update_grid: rand()+powf()+condicionales por celda = ~12 FLOPS / 40 B = 0.30 FLOP/B
    Ancho de banda DDR4 teórico i5-12400: ~38 GB/s. Pico GFLOPS estimado: ~4.8 (SSE doble).
    """
    # --- Parámetros del hardware (Intel Core i5-12400) ---
    BW_GB_s    = 38.0      # GB/s DDR4 dual-channel teórico
    PEAK_GFLOPS = 96.0     # GFLOPS teórico FP32 single-core (frecuencia × SIMD width)

    # Intensidad aritmética estimada (FLOP/Byte)
    ai_counts = 2.0 / (9 * 4)       # get_counts: 2 OPs, 9 lecturas enteras (4 B c/u)
    ai_update = 12.0 / 40.0         # update_grid: ~12 OPs (rand, pow, cmp), ~40 B r/w

    # Rendimiento medido (GFLOPS estimado = MCUPS × FLOP_por_celda / 1e3)
    # -O3: 519.07 MCUPS
    mcups_O3 = 519.07
    # Desglose de tiempo: update=73.2%, counts=26.8%
    # GFLOPS = MCUPS * FLOPs_por_tipo / 1e3
    gflops_counts = mcups_O3 * 0.268 * 2  / 1e3
    gflops_update = mcups_O3 * 0.732 * 12 / 1e3

    # --- Datos para trazar el Roofline ---
    ai_range = np.logspace(-3, 2, 500)
    # Techo de memoria: BW * AI (en GFLOPS)
    memory_roof = BW_GB_s * ai_range
    # Techo de cómputo: línea horizontal
    compute_roof = np.full_like(ai_range, PEAK_GFLOPS)
    # Roofline = mínimo de ambos techos
    roofline = np.minimum(memory_roof, compute_roof)

    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    ax.loglog(ai_range, roofline, color='#2c3e50', linewidth=2.5, label='Roofline (techo alcanzable)', zorder=3)
    ax.loglog(ai_range, memory_roof, color='#3498db', linewidth=1.4, linestyle='--',
              label=f'Techo de Memoria ({BW_GB_s:.0f} GB/s)', zorder=2, alpha=0.8)
    ax.axhline(PEAK_GFLOPS, color='#e74c3c', linewidth=1.4, linestyle='--',
               label=f'Techo de Cómputo ({PEAK_GFLOPS:.0f} GFLOPS)', alpha=0.8)

    # Puntos de los kernels medidos
    ax.scatter(ai_counts, gflops_counts, s=160, zorder=5, color='#27ae60',
               edgecolors='black', linewidths=1.2, label='Recuento de Estados (get_counts)')
    ax.scatter(ai_update, gflops_update, s=160, zorder=5, color='#e67e22',
               edgecolors='black', linewidths=1.2, label='Actualización de Celdas (update_grid)')

    # Etiquetas de cada punto
    ax.annotate('Recuento\nde Estados\n(~memory-bound)',
                xy=(ai_counts, gflops_counts), xytext=(ai_counts * 3, gflops_counts * 0.35),
                fontsize=9, fontweight='bold', color='#27ae60',
                arrowprops=dict(arrowstyle='->', color='#27ae60', lw=1.5),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#27ae60', alpha=0.9))
    ax.annotate('Actualización\nde Celdas\n(~memory-bound)',
                xy=(ai_update, gflops_update), xytext=(ai_update * 4, gflops_update * 2.5),
                fontsize=9, fontweight='bold', color='#e67e22',
                arrowprops=dict(arrowstyle='->', color='#e67e22', lw=1.5),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#e67e22', alpha=0.9))

    # Zona de limitación
    ax.axvspan(1e-3, PEAK_GFLOPS / BW_GB_s, alpha=0.06, color='#3498db', label='Zona Memory-Bound')
    ax.axvspan(PEAK_GFLOPS / BW_GB_s, 1e2, alpha=0.06, color='#e74c3c', label='Zona Compute-Bound')

    ridge_ai = PEAK_GFLOPS / BW_GB_s
    ax.axvline(ridge_ai, color='#8e44ad', linewidth=1.2, linestyle=':', alpha=0.7)
    ax.text(ridge_ai * 1.1, 0.02, f'Ridge point\n({ridge_ai:.2f} FLOP/B)',
            fontsize=8, color='#8e44ad', va='bottom',
            bbox=dict(facecolor='white', edgecolor='#8e44ad', alpha=0.8, pad=0.3))

    ax.set_xlabel('Intensidad Aritmética (FLOP/Byte)', fontweight='bold')
    ax.set_ylabel('Rendimiento Alcanzado (GFLOPS)', fontweight='bold')
    ax.set_title('Modelo Roofline: Ambos Kernels son Memory-Bound\n'
                 '(Intel Core i5-12400 — Estimación a partir de MCUPS medidos)',
                 fontweight='bold', pad=12)
    ax.legend(loc='upper left', fontsize=8.5, frameon=True)
    ax.set_xlim(1e-3, 1e2)
    ax.set_ylim(1e-3, PEAK_GFLOPS * 3)

    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig16_roofline_model.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")


# ==============================================================================
# FIG 17: VECTORIZACIÓN — ANÁLISIS DE BUCLES VECTORIZADOS POR KERNEL
# ==============================================================================
def plot_fig17_vectorization_analysis():
    """
    Muestra el desglose de la vectorización (o falta de ella) en cada kernel,
    derivado del informe -fopt-info-vec-all de GCC.
    """
    kernels = ['update_grid\n(Actualización de Celdas)', 'get_counts\n(Recuento de Estados)']

    # Datos del informe de vectorización de GCC (-fopt-info-vec-all):
    # update_grid: 0% vectorizado (rand+powf clobber memory — barrera ASM volátil)
    # get_counts:  SLP parcial (swap de punteros vectorizado), resto escalar
    pct_vec   = [0.0,  15.0]   # % de iteraciones que se benefician de SIMD
    pct_scalar= [100.0, 85.0]  # % escalar

    x = np.arange(len(kernels))
    width = 0.55
    colors_vec    = ['#27ae60', '#27ae60']
    colors_scalar = ['#e74c3c', '#e67e22']

    fig, ax = plt.subplots(figsize=(9.0, 5.5))
    b1 = ax.bar(x, pct_scalar, width, label='Escalar (sin SIMD)', color=colors_scalar,
                edgecolor='black', linewidth=0.8, alpha=0.88)
    b2 = ax.bar(x, pct_vec, width, bottom=pct_scalar, label='Vectorizado (SIMD/SLP)',
                color=colors_vec, edgecolor='black', linewidth=0.8, alpha=0.88)

    # Anotaciones de causa de fallo
    causas = [
        'Fallo: rand() + powf()\nclobber memory (ASM volátil)\n→ 0% SIMD',
        'SLP parcial: swap de punteros\nBucle principal: escalar\n→ ~15% cobertura SIMD'
    ]
    for i, causa in enumerate(causas):
        ax.text(x[i], 50, causa, ha='center', va='center', fontsize=9.5, fontweight='bold',
                color='white', bbox=dict(boxstyle='round,pad=0.4', facecolor='#2c3e50', alpha=0.85))

    # Etiqueta del segmento vectorizado (solo get_counts tiene algo)
    ax.text(x[1], pct_scalar[1] + pct_vec[1]/2, '15%',
            ha='center', va='center', fontsize=10, fontweight='bold', color='white')

    # Potencial teórico si se eliminara rand/powf
    ax.annotate('Potencial si se elimina rand()+powf():\n→ hasta ~80% vectorizable',
                xy=(0, 100), xytext=(0.35, 85),
                fontsize=8.5, color='#27ae60', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#27ae60', lw=1.5),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#27ae60', alpha=0.9))

    ax.set_ylim(0, 115)
    ax.set_ylabel('Cobertura del Bucle (%)', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(kernels, fontweight='bold', fontsize=11)
    ax.set_title('Análisis de Vectorización SIMD por Kernel\n'
                 '(Según informe GCC -fopt-info-vec-all)',
                 fontweight='bold', pad=12)
    ax.legend(loc='upper right', fontsize=10, frameon=True)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_yticklabels(['0%', '20%', '40%', '60%', '80%', '100%'])

    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig17_vectorization_analysis.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")


# ==============================================================================
# FIG 18: SPEEDUP DE LTO POR POLÍTICA — IMPACTO DIFERENCIAL
# ==============================================================================
def plot_fig18_lto_speedup_per_policy():
    """
    Compara el tiempo de cómputo de cada política entre -O3 y -O3+native+LTO.
    Muestra el speedup diferencial por política y cuánto aceleró get_counts.
    """
    d_o3  = parse_benchmark_file('results/flags/03.txt')
    d_lto = parse_benchmark_file('results/lto/lto.txt')

    policies = ['LaissezFaire', 'Lockdown', 'RemoteWork', 'DynamicSignals']
    labels   = ['LaissezFaire', 'Lockdown', 'RemoteWork', 'DynamicSignals']
    colors   = ['#e74c3c', '#8e44ad', '#3498db', '#f39c12']

    # Tiempos totales por política
    t_o3  = [d_o3['policy_phases'][p]['total_s']  for p in policies]
    t_lto = [d_lto['policy_phases'][p]['total_s'] for p in policies]
    sp_total = [a/b for a, b in zip(t_o3, t_lto)]

    # Tiempos de get_counts (donde LTO tiene mayor efecto)
    gc_o3  = [d_o3['policy_phases'][p]['counts_s']  for p in policies]
    gc_lto = [d_lto['policy_phases'][p]['counts_s'] for p in policies]
    sp_gc  = [a/b for a, b in zip(gc_o3, gc_lto)]

    x = np.arange(len(policies))
    width = 0.38

    fig, ax = plt.subplots(figsize=(10.0, 5.5))
    b1 = ax.bar(x - width/2, sp_total, width, label='Speedup Total de Política',
                color=colors, edgecolor='black', linewidth=0.8, alpha=0.88)
    b2 = ax.bar(x + width/2, sp_gc, width, label='Speedup solo en Recuento de Estados',
                color=colors, edgecolor='black', linewidth=0.8, alpha=0.5, hatch='//')

    ax.axhline(1.0, color='black', linewidth=1.0, linestyle='--', alpha=0.5)
    ax.text(len(policies)-0.5, 1.02, 'Sin mejora (1.0×)', fontsize=8.5, color='#7f8c8d', va='bottom')

    for i, (st, sg) in enumerate(zip(sp_total, sp_gc)):
        ax.text(x[i] - width/2, st + 0.04, f'{st:.2f}×', ha='center', va='bottom',
                fontsize=9.5, fontweight='bold', color=colors[i],
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=colors[i], alpha=0.9))
        ax.text(x[i] + width/2, sg + 0.04, f'{sg:.2f}×', ha='center', va='bottom',
                fontsize=9.5, fontweight='bold', color=colors[i],
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=colors[i], alpha=0.9))

    ax.set_ylabel('Speedup (LTO vs -O3)', fontweight='bold')
    ax.set_xlabel('Política Sanitaria', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontweight='bold')
    ax.set_ylim(0, max(sp_gc) * 1.30)
    ax.set_title('Impacto de LTO (-O3+native+flto) por Política\n'
                 'get_counts se beneficia masivamente: ×10 gracias a la inlining inter-módulo',
                 fontweight='bold', pad=12)
    ax.legend(loc='upper right', fontsize=9.5, frameon=True)

    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig18_lto_speedup_per_policy.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")


# ==============================================================================
# FIG 19: LOCALIDAD ESPACIAL — MCUPS VS TAMAÑO DE MALLA Y CACHÉ
# ==============================================================================
def plot_fig19_spatial_locality_cache():
    """
    Muestra cómo el MCUPS varía con el tamaño del problema y dónde cae la
    Working Set Size respecto a la jerarquía de caché del i5-12400.
    """
    # Tamaños de malla (filas x cols) y MCUPS medidos (-O3)
    configs = [
        ('Ciudad\n591×591', 591*591, 475.09),
        ('Provincia\n1414×1414', 1414*1414, 484.62),
        ('Comunidad\n2258×2258', 2258*2258, 464.81),
    ]
    labels = [c[0] for c in configs]
    cells  = [c[1] for c in configs]
    mcups  = [c[2] for c in configs]

    # Working Set Size = cells × bytes_per_cell (estado=1B, prob=4B, counts=4B) × 3 buffers
    bytes_per_cell = 1 + 4 + 4   # estado (char) + probabilidad (float) + count (int)
    wss_bytes = [n * bytes_per_cell * 3 for n in cells]   # 3 buffers activos
    wss_mb    = [w / 1e6 for w in wss_bytes]

    # Jerarquía de caché i5-12400
    L1_mb = 0.288   # L1d por núcleo (288 KiB)
    L2_mb = 1.25    # L2 por núcleo (1.25 MiB)
    L3_mb = 18.0    # L3 compartida (18 MiB)

    x = np.arange(len(labels))
    color_bars = ['#3498db', '#f39c12', '#e74c3c']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 5.5))

    # Panel A: Working Set Size vs jerarquía de caché
    ax1.bar(x, wss_mb, color=color_bars, edgecolor='black', linewidth=0.8, alpha=0.85, width=0.55)
    ax1.axhline(L1_mb, color='#27ae60', linewidth=2.0, linestyle='--', label=f'L1d = {L1_mb*1024:.0f} KiB', zorder=3)
    ax1.axhline(L2_mb, color='#e67e22', linewidth=2.0, linestyle='--', label=f'L2 = {L2_mb*1024:.0f} MiB', zorder=3)
    ax1.axhline(L3_mb, color='#c0392b', linewidth=2.0, linestyle='--', label=f'L3 = {L3_mb:.0f} MiB', zorder=3)

    for i, (w, m) in enumerate(zip(wss_mb, mcups)):
        ax1.text(x[i], w + 0.6, f'{w:.1f} MB', ha='center', va='bottom',
                 fontsize=10, fontweight='bold', color=color_bars[i],
                 bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor=color_bars[i], alpha=0.9))

    ax1.set_ylabel('Tamaño del Conjunto de Trabajo (MB)', fontweight='bold')
    ax1.set_xlabel('Configuración de Simulación', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontweight='bold')
    ax1.set_ylim(0, max(wss_mb) * 1.25)
    ax1.set_title('A: Working Set Size\nvs. Jerarquía de Caché', fontweight='bold')
    ax1.legend(loc='upper left', fontsize=9, frameon=True)

    # Panel B: MCUPS por configuración
    ax2.bar(x, mcups, color=color_bars, edgecolor='black', linewidth=0.8, alpha=0.85, width=0.55)
    ax2.axhline(np.mean(mcups), color='#8e44ad', linewidth=2.0, linestyle='--',
                label=f'Media: {np.mean(mcups):.1f} MCUPS')
    for i, m in enumerate(mcups):
        ax2.text(x[i], m + 2, f'{m:.1f}', ha='center', va='bottom',
                 fontsize=10, fontweight='bold', color=color_bars[i],
                 bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor=color_bars[i], alpha=0.9))

    ax2.set_ylabel('Throughput (MCUPS)', fontweight='bold')
    ax2.set_xlabel('Configuración de Simulación', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontweight='bold')
    ax2.set_ylim(440, max(mcups) * 1.12)
    ax2.set_title('B: Throughput Medido\n(todas las mallas superan L3)', fontweight='bold')
    ax2.legend(loc='upper right', fontsize=9.5, frameon=True)

    plt.suptitle('Localidad Espacial y Jerarquía de Caché (Intel Core i5-12400)',
                 fontweight='bold', fontsize=13, y=1.01)
    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig19_spatial_locality_cache.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")


# ==============================================================================
# FIG 20: EFICIENCIA ENERGÉTICA RELATIVA POR CONFIGURACIÓN
# ==============================================================================
def plot_fig20_energy_efficiency():
    """
    Estimación de energía relativa = wall_time × potencia_TDP_estimada.
    Se normaliza a -O0 (=1.0). La fuente de potencia es el TDP del i5-12400
    bajo carga sostenida (~65 W). Sirve para mostrar que más velocidad = menos energía.
    """
    configs = [
        ('-O0\n(base)',    249.00),
        ('-O1',           115.58),
        ('-O2',           110.58),
        ('-O3',            58.96),
        ('-O3\n+native',   63.84),
        ('-O3\n+LTO',      42.89),
        ('Max\nOpt',       42.78),
    ]
    TDP_W = 65.0   # Vatios bajo carga real (estimación i5-12400)
    labels = [c[0] for c in configs]
    times  = np.array([c[1] for c in configs])
    energy = times * TDP_W      # Joules estimados
    rel    = energy / energy[0] # relativo a -O0

    colors = ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#27ae60', '#1abc9c', '#16a085']

    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    bars = ax.bar(np.arange(len(labels)), rel, color=colors, edgecolor='black',
                  linewidth=0.8, width=0.6, alpha=0.88)
    ax.axhline(1.0, color='black', linewidth=1.0, linestyle='--', alpha=0.5, label='Referencia -O0 (100%)')

    for i, (r, t) in enumerate(zip(rel, times)):
        j = t * TDP_W
        ax.text(i, r + 0.015, f'{r*100:.1f}%\n({j:.0f} J)', ha='center', va='bottom',
                fontsize=8.5, fontweight='bold', color=colors[i],
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=colors[i], alpha=0.9))

    ax.set_ylabel('Energía Relativa (respecto a -O0)', fontweight='bold')
    ax.set_xlabel('Configuración de Compilación', fontweight='bold')
    ax.set_xticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, fontweight='bold')
    ax.set_ylim(0, 1.35)
    ax.set_yticks([0, 0.25, 0.50, 0.75, 1.0])
    ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'])
    ax.set_title('Eficiencia Energética Estimada por Configuración de Compilación\n'
                 f'(TDP estimado bajo carga: {TDP_W:.0f} W — Intel Core i5-12400)',
                 fontweight='bold', pad=12)
    ax.legend(loc='upper right', fontsize=9.5)

    # Flecha de ahorro
    ax.annotate('', xy=(6, rel[6] + 0.02), xytext=(0, rel[0] - 0.02),
                arrowprops=dict(arrowstyle='<->', color='#2c3e50', lw=1.8))
    ax.text(3.0, 0.65, f'Ahorro: {(1-rel[6])*100:.1f}% de energía\ncon Max Opt vs -O0',
            ha='center', va='center', fontsize=9.5, fontweight='bold', color='#2c3e50',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#ecf0f1', edgecolor='#2c3e50', alpha=0.9))

    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig20_energy_efficiency.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")


# ==============================================================================
# FIG 21: INTENSIDAD ARITMÉTICA POR FASE DEL KERNEL
# ==============================================================================
def plot_fig21_arithmetic_intensity():
    """
    Estimación de la intensidad aritmética (FLOP/Byte) para cada ruta de
    ejecución dentro de los kernels, basada en el análisis del código fuente.
    """
    fases = [
        'get_counts\n(Recuento de vecinos)',
        'update_grid\n— celda SUSCEPTIBLE\n(sin contagio)',
        'update_grid\n— celda SUSCEPTIBLE\n(con contagio)',
        'update_grid\n— celda INFECTED\n(rand + pow)',
        'update_grid\n— celda RECOVERED\n(inmune)',
    ]
    # Estimación: FLOPs por celda / bytes accedidos por celda
    # get_counts: 9 lecturas int (36B) + 1 suma + 1 incremento = 2 FLOPS
    # Susc sin contagio: 1 lectura (9B) + 1 cmp = 1 FLOP / 9B
    # Susc con contagio: powf() + rand() + mul + add ≈ 8 FLOPS / 40B
    # Infected: rand() + decrement + cmp ≈ 4 FLOPS / 12B
    # Recovered: 1 lectura + 1 cmp = 1 FLOP / 4B
    ai_vals = [2/36, 1/9, 8/40, 4/12, 1/4]
    colors  = ['#3498db', '#2ecc71', '#e67e22', '#e74c3c', '#9b59b6']

    ridge_ai = 96.0 / 38.0   # Ridge point del i5-12400

    fig, ax = plt.subplots(figsize=(10.5, 5.5))
    y = np.arange(len(fases))
    bars = ax.barh(y, ai_vals, color=colors, edgecolor='black', linewidth=0.8,
                   height=0.55, alpha=0.88)

    ax.axvline(ridge_ai, color='#c0392b', linewidth=2.0, linestyle='--',
               label=f'Ridge Point (i5-12400): {ridge_ai:.2f} FLOP/B', zorder=4)

    for i, v in enumerate(ai_vals):
        region = 'Memory-Bound' if v < ridge_ai else 'Compute-Bound'
        ax.text(v + 0.003, i, f'{v:.3f} FLOP/B  [{region}]',
                ha='left', va='center', fontsize=9.5, fontweight='bold', color=colors[i],
                bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor=colors[i], alpha=0.9))

    ax.set_xlabel('Intensidad Aritmética (FLOP/Byte)', fontweight='bold')
    ax.set_yticks(y)
    ax.set_yticklabels(fases, fontsize=9.5)
    ax.set_title('Intensidad Aritmética Estimada por Ruta de Ejecución del Kernel\n'
                 '(Todos los caminos caen en la zona Memory-Bound)',
                 fontweight='bold', pad=12)
    ax.legend(loc='lower right', fontsize=9.5, frameon=True)
    ax.set_xlim(0, ridge_ai * 1.35)

    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig21_arithmetic_intensity.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")


# ==============================================================================
# FIG 22: PROYECCIÓN DE ESCALADO — TIEMPO VS POBLACIÓN TEÓRICA
# ==============================================================================
def plot_fig22_scaling_projection():
    """
    Ajusta una recta a los 3 puntos de escala (ciuddd/provincia/comunidad) y
    extrapola hasta escala nacional (~47M de habitantes).
    Marca cuándo el Working Set supera la L3 (18 MB).
    """
    # Datos medidos (-O3, ciudad / provincia / comunidad)
    pops   = np.array([349281, 1999396, 5098564])
    times  = np.array([58.96, 385.30, 1002.61])   # wall seconds

    # Ajuste lineal en escala log-log
    log_p = np.log10(pops)
    log_t = np.log10(times)
    coeffs = np.polyfit(log_p, log_t, 1)   # slope, intercept
    slope, intercept = coeffs
    print(f"    [fig22] Scaling slope (log-log): {slope:.3f} (ideal lineal = 1.0)")

    p_range = np.logspace(np.log10(300000), np.log10(50_000_000), 300)
    t_fit   = 10 ** (slope * np.log10(p_range) + intercept)

    # Punto en que el Working Set supera la L3 (18 MB)
    # WSS = N * 9 bytes * 3 buffers = 27N bytes → L3_overflow en N = 18e6/27
    L3_MB = 18.0
    bytes_per_cell = 9   # (1 estado + 4 prob + 4 count)
    N_l3_overflow = (L3_MB * 1e6) / (bytes_per_cell * 3)

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    ax.scatter(pops, times, s=150, zorder=5, color=['#3498db', '#f39c12', '#e74c3c'],
               edgecolors='black', linewidths=1.2, label='Mediciones reales')
    ax.plot(p_range, t_fit, color='#2c3e50', linewidth=2.2, linestyle='--',
            label=f'Ajuste potencial (pendiente={slope:.2f})')

    # Marcadores de referencia
    ax.axvline(N_l3_overflow, color='#e74c3c', linewidth=1.8, linestyle=':',
               label=f'Desbordamiento L3 (~{N_l3_overflow/1e6:.1f} M hab)')
    ax.axvline(47_000_000, color='#8e44ad', linewidth=1.8, linestyle=':',
               label='Escala nacional (~47 M hab)')

    # Etiquetas de los puntos medidos
    point_labels = ['Ciudad\n(349K hab)', 'Provincia\n(2.0M hab)', 'Comunidad\n(5.1M hab)']
    offsets = [(1.05, 0.85), (1.05, 0.85), (1.05, 0.85)]
    pcolors = ['#3498db', '#f39c12', '#e74c3c']
    for i, (p, t, lbl, col) in enumerate(zip(pops, times, point_labels, pcolors)):
        ax.annotate(f'{lbl}\n{t:.0f} s', xy=(p, t), xytext=(p * 1.6, t * 0.65),
                    fontsize=8.5, fontweight='bold', color=col,
                    arrowprops=dict(arrowstyle='->', color=col, lw=1.3),
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=col, alpha=0.9))

    # Tiempo proyectado a escala nacional
    t_national = 10 ** (slope * np.log10(47_000_000) + intercept)
    ax.scatter([47_000_000], [t_national], s=180, marker='*', color='#8e44ad',
               zorder=6, edgecolors='black', linewidths=1.0, label=f'Proyección España: {t_national:.0f} s')

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Población Simulada (habitantes)', fontweight='bold')
    ax.set_ylabel('Tiempo Total de Ejecución (s)', fontweight='bold')
    ax.set_title('Proyección del Tiempo de Simulación a Escala de Población\n'
                 f'(Pendiente log-log = {slope:.2f}; escala cuasi-lineal)',
                 fontweight='bold', pad=12)
    ax.legend(loc='upper left', fontsize=8.5, frameon=True)

    # Formatear eje X con nombres de escala
    from matplotlib.ticker import FuncFormatter
    def fmt_pop(x, _):
        if x >= 1e6: return f'{x/1e6:.0f}M'
        if x >= 1e3: return f'{x/1e3:.0f}K'
        return str(int(x))
    ax.xaxis.set_major_formatter(FuncFormatter(fmt_pop))

    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig22_scaling_projection.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")


# ==============================================================================
# FIG 23: PIPELINE DE COMPILACIÓN — COMPARATIVA DE TODAS LAS CONFIGURACIONES
# ==============================================================================
def plot_fig23_full_optimization_pipeline():
    """
    Vista de conjunto: muestra el MCUPS y el tiempo total de TODAS las
    configuraciones probadas, ordenadas por rendimiento creciente.
    TODOS los valores se leen directamente de los archivos de resultados.
    """
    # --- Carga de datos reales desde archivos (sin hardcoding) ---
    config_files = [
        ('-O0 (base)',               'results/flags/base.txt'),
        ('-O1',                      'results/flags/01.txt'),
        ('-O2',                      'results/flags/02.txt'),
        ('-Os',                      'results/flags/Os.txt'),
        ('-O3',                      'results/flags/03.txt'),
        ('-Ofast',                   'results/flags/0fast.txt'),
        ('-O3+native',               'results/march/03+native.txt'),
        ('-O3+native+FMA',           'results/march/03+native+fma.txt'),
        ('Unroll\n(-funroll-loops)', 'results/unroll/unroll.txt'),
        ('Ancho Vec. 256b',          'results/vector_width/w256.txt'),
        ('Ancho Vec. 512b',          'results/vector_width/w512.txt'),
        ('Cost Model\n(unlimited)',  'results/cost_model/cost_unlimited.txt'),
        ('SIMD (-msse4.2)',          'results/simd/vec.txt'),
        ('PGO (-fprofile-use)',      'results/pgo/pgo.txt'),
        ('-O3+native+LTO',           'results/lto/lto.txt'),
        ('Max Opt\n(LTO+O3+native)', 'results/max_opt/max_opt.txt'),
    ]

    configs = []
    for label, fpath in config_files:
        d = parse_benchmark_file(fpath)
        if d and d['wall_s'] is not None and d['mcups'] is not None:
            configs.append((label, d['wall_s'], d['mcups']))
        else:
            print(f"    [fig23] AVISO: no se pudo leer '{fpath}' — omitido")

    # Ordenar por MCUPS creciente
    configs_sorted = sorted(configs, key=lambda c: c[2])
    labels = [c[0] for c in configs_sorted]
    times  = [c[1] for c in configs_sorted]
    mcups  = [c[2] for c in configs_sorted]

    cmap = plt.get_cmap('RdYlGn')
    norm_mcups = [(m - min(mcups)) / (max(mcups) - min(mcups)) for m in mcups]
    colors = [cmap(v) for v in norm_mcups]

    x = np.arange(len(labels))
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13.0, 11.5), sharex=False)

    # Panel A: MCUPS
    ax1.barh(x, mcups, color=colors, edgecolor='black', linewidth=0.6, height=0.65, alpha=0.9)
    ax1.set_xlabel('Rendimiento del Kernel (MCUPS)', fontweight='bold')
    ax1.set_title('A: Throughput del Kernel — Mayor es mejor', fontweight='bold')
    for i, m in enumerate(mcups):
        ax1.text(m + 2, i, f'{m:.1f}', va='center', ha='left', fontsize=8.5, fontweight='bold')
    ax1.set_xlim(0, max(mcups) * 1.12)
    ax1.set_yticks(x)
    ax1.set_yticklabels(labels, fontsize=8.8)

    # Panel B: Tiempo de ejecución
    ax2.barh(x, times, color=colors, edgecolor='black', linewidth=0.6, height=0.65, alpha=0.9)
    ax2.set_xlabel('Tiempo Total de Ejecución (s)', fontweight='bold')
    ax2.set_title('B: Tiempo de Ejecución — Menor es mejor', fontweight='bold')
    for i, t in enumerate(times):
        ax2.text(t + 1.5, i, f'{t:.1f} s', va='center', ha='left', fontsize=8.5, fontweight='bold')
    ax2.set_xlim(0, max(times) * 1.12)
    ax2.set_yticks(x)
    ax2.set_yticklabels(labels, fontsize=8.8)

    plt.suptitle('Pipeline Completo de Optimización: Comparativa de Todas las Configuraciones\n'
                 '(Ciudad 591×591, 320 simulaciones Monte Carlo — Intel Core i5-12400)',
                 fontweight='bold', fontsize=12.5, y=1.01)

    footnote = (
        'Datos leídos directamente de: results/flags/{base,01,02,Os,03,0fast}.txt  ·  results/march/{03,03+native,03+native+fma}.txt\n'
        'results/unroll/unroll.txt  ·  results/vector_width/{w256,w512}.txt  ·  results/cost_model/cost_unlimited.txt\n'
        'results/simd/vec.txt  ·  results/pgo/pgo.txt  ·  results/lto/lto.txt  ·  results/max_opt/max_opt.txt\n'
        'Campos extraídos: "Total Wall-Clock Time" y "Kernel Throughput (MCUPS)" de cada archivo de resultados.'
    )
    fig.text(0.01, -0.02, footnote, ha='left', va='top', fontsize=7.5, color='#555555', style='italic',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#f8f9fa', edgecolor='#dee2e6', alpha=0.9))

    plt.tight_layout()
    outfile = os.path.join(OUTPUT_DIR, 'fig23_full_optimization_pipeline.png')
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generada: {outfile}")


# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == '__main__':
    print("=================================================================")
    print("Regenerando 23 figuras científicas con maquetación impecable...")
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
    # --- Nuevas figuras de arquitectura ---
    plot_fig16_roofline_model()
    plot_fig17_vectorization_analysis()
    plot_fig18_lto_speedup_per_policy()
    plot_fig19_spatial_locality_cache()
    plot_fig20_energy_efficiency()
    plot_fig21_arithmetic_intensity()
    plot_fig22_scaling_projection()
    plot_fig23_full_optimization_pipeline()
    print("=================================================================")
    print(f"¡Todas las figuras generadas exitosamente en: {OUTPUT_DIR}/ !")
    print("=================================================================")
