# tesis-xgboost-churn

Prototipo académico de investigación para la detección temprana de deserción de afiliados mediante modelos de clasificación, con XGBoost como candidato principal. No es un sistema comercial ni declara resultados sobre datos reales, validación organizacional o superioridad de un modelo.

## Decisión y ruta rápida

El repositorio mantiene una aplicación Python única, con capas separadas y dependencias explícitas. La API y el entrenamiento pueden probarse localmente sin conectarse al backoffice ni a datos institucionales.

### 1. Preparar el entorno

Requiere Python 3.12. Se recomienda un entorno virtual:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Ejecutar las pruebas focalizadas

```bash
python -m pytest tests/training tests/api tests/services tests/repositories
```

### 3. Ejecutar la suite completa

```bash
python -m pytest
```

### 4. Comprobar dependencias

```bash
python -m pip check
```

Estas comprobaciones son locales. La tarea documental A3 no requiere ejecutar pruebas Python ni acceder a red, Datasheet, CSV, bases de datos o credenciales.

## Capas y dirección de dependencias

La dirección prevista es de afuera hacia adentro: API → servicios/repositorios → núcleo y entrenamiento. El núcleo no depende de FastAPI ni de SQL; los repositorios encapsulan acceso a almacenamiento y los servicios coordinan casos de uso pequeños.

- `app/api/`: routers, controladores y dependencias de FastAPI. `risk_controller.py` conserva el contrato provisional.
- `app/services/`: servicios de aplicación; `RiskScoreService` delega el listado de scores al repositorio.
- `app/repositories/`: acceso a resultados y fuentes persistidas, incluido `RiskScoreRepository` y repositorios de afiliados, referidos, vencimientos y actividad de wallet.
- `app/schemas/`: modelos Pydantic de las respuestas de riesgo.
- `app/core/`: features, etiquetas, horizonte y modelo; contiene la lógica científica que no debe conocer la infraestructura.
- `app/training/`: construcción de datasets, evaluación, comparación, explicabilidad y experimento sintético. `ports.py` define Protocols para las fuentes del constructor; `csv_adapters.py` ofrece una fachada compatible para los adaptadores CSV concretos.

La inyección de dependencias conecta API con repositorios y servicios. Los puertos de `app/training/ports.py` permiten sustituir fuentes sin acoplar `dataset_builder.py` a un formato concreto; los adaptadores CSV implementan esas interfaces para pruebas y exploración local.

## Fronteras de datos

- **Fuentes:** las interfaces de entrenamiento reciben datos de afiliados, actividad de wallet, referidos y vencimientos. Los repositorios de aplicación aíslan las conexiones de lectura.
- **Transformación:** `app/core/` y `app/training/` convierten esas fuentes en features, etiquetas y evaluaciones. Los notebooks sirven para exploración y construcción offline, no para ejecutar la API.
- **Resultados:** `app/repositories/risk_repository.py` lee scores de `score_riesgo`; `app/schemas/risk_score.py` define su forma de salida. La migración inicial está en `alembic/versions/` y se gestiona con Alembic.
- **Separación:** los resultados del modelo no sobrescriben las fuentes. Las fixtures y experimentos sintéticos deben mantenerse distinguibles de cualquier dataset institucional.

## API provisional

El router de riesgo se monta bajo `/api/v1`.

- `GET /api/v1/risk`: lista el último score por afiliado con `limit` (1..100, por defecto 50), `offset` (>=0, por defecto 0) y `order` (`asc`/`desc`, por defecto `desc`). Responde `{ "items": [...], "limit": 50, "offset": 0, "total": 0 }`.
- `GET /api/v1/risk/{affiliate_id}`: consulta el último score de un afiliado y devuelve 404 si no existe.

Es un contrato técnico provisional. No implementa autenticación, escritura de scores, SHAP ni decisiones productivas, y no representa una historia de usuario validada institucionalmente.

## Experimentos sintéticos y límites

Los tests de `tests/training/` y `app/training/synthetic_experiment.py` verifican construcción, cortes, evaluación y comparación con datos sintéticos o fixtures controladas. Sus métricas solo sirven para comprobar el comportamiento del código; no son resultados de la tesis, no prueban desempeño en afiliados reales y no permiten declarar un modelo superior. SMOTE y el protocolo final de evaluación siguen pendientes de validación.

## Qué queda bloqueado

Hasta contar con autorización institucional, definición validada de variables y dataset histórico real, no se deben afirmar resultados, umbrales de negocio, selección final del modelo ni integración con el backoffice. También quedan fuera de este prototipo la autenticación, la persistencia operativa de scores, las reglas productivas y la validación organizacional. Los archivos locales de `Datasheet/` no deben interpretarse como autorización ni utilizarse para producir conclusiones.

## Estructura actual

```text
tesis-xgboost-churn/
├── app/
│   ├── api/v1/              # endpoints y dependencias FastAPI
│   ├── core/                # features, etiquetas, horizonte y modelo
│   ├── repositories/        # acceso aislado a fuentes y resultados
│   ├── schemas/             # contratos Pydantic
│   ├── services/            # servicios de aplicación
│   └── training/            # puertos, adaptadores y pipeline offline
├── alembic/                 # configuración y migraciones de base de datos
├── notebooks/               # exploración y construcción offline
├── tests/                   # pruebas por API, core, repositorios, servicios y training
├── Datasheet/               # archivos locales; no equivalen a datos autorizados
├── odd/tasks/               # tareas de arquitectura y trabajo del repositorio
├── requirements.txt
├── Dockerfile
└── README.md
```

La formalización de XGBoost y los capítulos de tesis viven en sus rutas documentales respectivas cuando están presentes; no forman parte del flujo de ejecución de la aplicación.

## Estado

El proyecto sigue siendo un prototipo de investigación. La etiqueta provisional usa más de 180 días desde el vencimiento y el horizonte configurado es de 30 días; no son políticas oficiales. El tratamiento de reactivaciones, el split, los pesos, las métricas finales y los resultados sobre datos autorizados permanecen pendientes.
