# tesis-xgboost-churn

Prototipo de investigación de la tesis *Detección temprana de deserción de afiliados en la plataforma de membresías multinivel de InClub World S.A.C. mediante un modelo predictivo basado en XGBoost* (Seminario de Investigación I y II, UCSS, Ingeniería de Sistemas). Autor: Alexander Urquizo Rodriguez.

Este repositorio contiene un prototipo académico, no un sistema comercial. La autorización institucional y el dataset histórico autorizado siguen pendientes; las pruebas unitarias no usan datos reales ni credenciales.

## Arquitectura

El proyecto se diseña como un microservicio independiente que se integra por API REST con el backoffice real de InClub World, sin modificarlo ni depender de él para ejecutarse:

- **Sistema existente de InClub World (fuera de este repositorio):** backoffice Java/Spring WebFlux, el job nocturno que calcula el estado de morosidad de cada afiliado, y la base de datos de producción. Este repositorio no se conecta a ellos directamente; solo consume variables ya calculadas, expuestas vía API cuando exista autorización institucional para ello.
- **Microservicio propuesto (este repositorio):**
  - API en FastAPI, que expone el endpoint de consulta del puntaje de riesgo de un afiliado.
  - Núcleo de predicción basado en XGBoost (modelo principal) y un pipeline de entrenamiento offline.
  - Base de datos de resultados en PostgreSQL, separada de los datos crudos, donde se registran las ejecuciones del modelo y los puntajes de riesgo (nunca se sobrescribe el dato original con el resultado).

## Endpoint provisional de HU-02

El prototipo expone `GET /api/v1/risk` para consultar, sin escribir datos, el último
score disponible por afiliado. Acepta `limit` (entero 1..100, por defecto 50),
`offset` (entero >=0, por defecto 0) y `order` (`asc` o `desc`, por defecto `desc`).
Ordena por `risk_score` y usa `scored_at` descendente para desempatar. La respuesta
es `{ "items": [...], "limit": 50, "offset": 0, "total": 0 }`.

Este es un contrato técnico provisional para pruebas del prototipo. No representa una
HU validada organizacionalmente: el actor, la necesidad, los umbrales de negocio y la
aceptación institucional siguen pendientes. El endpoint no implementa escritura,
autenticación, SHAP ni decisiones productivas.

Ejemplo:

```bash
curl "http://localhost:8000/api/v1/risk?limit=10&offset=0&order=desc"
```

## Métodos, modelos y algoritmos que son parte de la solución

- **XGBoost**, **Random Forest** y **Árbol de Decisión**: candidatos de la comparación prevista en el Capítulo III. La selección final queda pendiente de ejecutar el mismo protocolo sobre datos autorizados; este repositorio todavía no contiene resultados experimentales que declaren un ganador.
- **SMOTE** (Chawla et al., 2002): técnica considerada para el tratamiento del desbalance; todavía no está implementada ni validada en este repositorio.
- **Métricas de evaluación:** Recall, F1-Score y AUC-ROC como métricas previstas; la métrica primaria y el protocolo final siguen pendientes de validación.

La formalización axiomática de XGBoost (ecuación → pseudocódigo → código) se documenta por separado en `docs/formalizacion_xgboost.md`.

## Variables

- **Individuales implementadas en el núcleo actual:** días desde el último pago, frecuencia y monto de pago, antigüedad y actividad de billetera. `frecuencia_acceso` permanece pendiente y no está implementada como feature confirmada.
- **De red de referidos** (exploratorias, sujetas a disponibilidad de datos y autorización institucional): número de referidos activos/inactivos, porcentaje de referidos que desertaron recientemente, posición/profundidad en la red, ingresos por comisión de red vs. consumo propio.

## Estructura del repositorio

```
tesis-xgboost-churn/
├── README.md
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docs/          # formalización del algoritmo, diagramas
├── app/           # código de la API y el núcleo del modelo (etapas siguientes)
└── notebooks/     # exploración y entrenamiento offline (etapas siguientes)
```

## Cómo reconstruir el entorno

Con Docker (recomendado):

```bash
git clone https://github.com/alexander3d2/tesis-xgboost-churn.git
cd tesis-xgboost-churn
docker build -t tesis-xgboost-churn .
```

Sin Docker, usando un entorno virtual de Python 3.12:

```bash
git clone https://github.com/alexander3d2/tesis-xgboost-churn.git
cd tesis-xgboost-churn
pip install -r requirements.txt
```

## Estado del proyecto

Estado actual: primera prueba técnica del núcleo y del constructor de ejemplos. La etiqueta usa provisionalmente más de 180 días desde el vencimiento y el horizonte configurado es de 30 días; no son política oficial de InClub World. El tratamiento de reactivaciones, la autorización, el dataset real, el split, los pesos, las métricas y los resultados siguen pendientes.
