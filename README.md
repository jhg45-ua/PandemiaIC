# PandemicSim

Simulador epidemiológico y socioeconómico de alto rendimiento escrito en C11.
El proyecto modela la evolución de una epidemia sobre una malla bidimensional y
permite comparar distintas políticas de intervención mediante réplicas Monte
Carlo.

## Características

- Modelo epidemiológico SIRD: susceptibles, infectados, recuperados y
  fallecidos.
- Autómata celular con vecindario de Moore de ocho vecinos y doble búfer.
- Políticas configurables de intervención, como `LaissezFaire`, `Lockdown`,
  `RemoteWork` y `DynamicSignals`.
- Evaluación del impacto sanitario, económico y social de cada política.
- Réplicas Monte Carlo reproducibles mediante una semilla configurable.
- Medición del tiempo de ejecución, del *throughput* y del rendimiento del
  kernel en MCUPS.
- Escenarios de simulación sintéticos y territoriales: ciudad, provincia,
  comunidad autónoma y España.

La descripción completa del modelo y de las fórmulas utilizadas está en
[`docs/modelo.md`](docs/modelo.md).

## Requisitos

- GCC en Linux o Clang en macOS.
- `make`.
- Una shell compatible con Bash para ejecutar los scripts de escenarios.

El código utiliza funciones POSIX para la medición temporal. El `Makefile`
selecciona GCC por defecto; en macOS se puede compilar con Clang cambiando la
variable `CC`.

## Compilación

Desde la raíz del repositorio:

```bash
make
```

El binario se genera en `bin/sim`. La compilación también genera código
ensamblador anotado en `build/asm/`.

Para consultar todos los objetivos disponibles:

```bash
make help
```

## Ejecución

### Escenarios preconfigurados

```bash
# Alicante capital
make run

# Provincia de Alicante
make run-provincia

# Comunitat Valenciana
make run-comunidad
```

Los scripts de escenario establecen el fichero de políticas, la población,
los focos iniciales y el número de réplicas. En `make run` se puede indicar
opcionalmente la duración:

```bash
./scripts/run_ciudad.sh 100
```

### Ejecución directa

El ejecutable acepta los siguientes parámetros posicionales:

```text
./bin/sim [config_file] [population] [days] [initial_infected] [n_sim] [seed]
```

Si no se especifican, se utilizan estos valores:

| Parámetro | Valor predeterminado |
| --- | ---: |
| `config_file` | `config/policies.conf` |
| `population` | `100000` |
| `days` | `150` |
| `initial_infected` | `10` |
| `n_sim` | `20` |
| `seed` | `29` |

Ejemplo:

```bash
./bin/sim config/policies.conf 100000 150 10 20 29
```

La población solicitada se adapta a una malla cuadrada; por ello, el número
real de celdas puede ser ligeramente inferior al valor indicado.

## Configuración

Los ficheros de [`config/`](config/) contienen una política por línea con este
formato:

```text
nombre beta trade_restriction daily_subsidy_expense dynamic_ICU_threshold
```

Los escenarios disponibles son:

- [`policies.conf`](config/policies.conf): escenario sintético.
- [`policies_ciudad.conf`](config/policies_ciudad.conf): Alicante capital.
- [`policies_provincia.conf`](config/policies_provincia.conf): provincia de
  Alicante.
- [`policies_comunidad.conf`](config/policies_comunidad.conf): Comunitat
  Valenciana.
- [`policies_espana.conf`](config/policies_espana.conf): escenario nacional.

## Estructura del repositorio

```text
.
├── config/      # Políticas y parámetros de los escenarios
├── docs/        # Documentación detallada del modelo
├── include/     # Cabeceras públicas del simulador
├── scripts/     # Lanzadores y batería de benchmarks
├── src/         # Implementación en C
└── results/     # Resultados y gráficas de experimentos
```

## Optimización y benchmarks

El proyecto incluye objetivos para inspeccionar el ensamblador y los informes
de autovectorización:

```bash
make asm OPTFLAGS=-O3
make vectorization
```

La batería completa de experimentos de compilación se encuentra en
[`scripts/run_benchmarks.sh`](scripts/run_benchmarks.sh). Sus resultados se
guardan en [`results/`](results/).

## Limpieza

```bash
make clean
```

Este comando elimina el binario y los artefactos generados en `bin/` y
`build/`.

## Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta
[`LICENSE`](LICENSE).
