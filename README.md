# tesis-xgboost-churn

Prototipo de investigación de la tesis *Detección temprana de deserción de afiliados en la plataforma de membresías multinivel de InClub World S.A.C. mediante un modelo predictivo basado en XGBoost* (Seminario de Investigación I y II, UCSS, Ingeniería de Sistemas). Autor: Alexander Urquizo Rodriguez.

Este repositorio contiene un prototipo académico, no un sistema comercial. No incluye datos reales de producción de InClub World S.A.C. ni credenciales de ningún tipo.

## Arquitectura

El proyecto se diseña como un microservicio independiente que se integra por API REST con el backoffice real de InClub World, sin modificarlo ni depender de él para ejecutarse:

- **Sistema existente de InClub World (fuera de este repositorio):** backoffice Java/Spring WebFlux, el job nocturno que calcula el estado de morosidad de cada afiliado, y la base de datos de producción. Este repositorio no se conecta a ellos directamente; solo consume variables ya calculadas, expuestas vía API cuando exista autorización institucional para ello.
- **Microservicio propuesto (este repositorio):**
  - API en FastAPI, que expone el endpoint de consulta del puntaje de riesgo de un afiliado.
  - Núcleo de predicción basado en XGBoost (modelo principal) y un pipeline de entrenamiento offline.
  - Base de datos de resultados en PostgreSQL, separada de los datos crudos, donde se registran las ejecuciones del modelo y los puntajes de riesgo (nunca se sobrescribe el dato original con el resultado).

## Métodos, modelos y algoritmos que son parte de la solución

- **XGBoost** (Chen & Guestrin, 2016): modelo predictivo principal, seleccionado preliminarmente en el Capítulo III de la tesis (matriz de decisión ponderada, Tabla 2) frente a los dos candidatos siguientes.
- **Random Forest** y **Árbol de Decisión**: modelos de comparación, usados en el Capítulo III para confirmar empíricamente la selección de XGBoost sobre el mismo conjunto de datos.
- **SMOTE** (Chawla et al., 2002): técnica de remuestreo para corregir el desbalance de clases entre afiliados que desertan y los que no.
- **Métricas de evaluación:** Recall (métrica principal de la tesis), F1-Score y AUC-ROC.

La formalización axiomática de XGBoost (ecuación → pseudocódigo → código) se documenta por separado en `docs/formalizacion_xgboost.md`.

## Variables

- **Individuales** (confirmadas): días desde el último pago, frecuencia y monto de pago, antigüedad, frecuencia de acceso.
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

Etapa de diseño y aprovisionamiento del entorno (Semana 5 de Seminario de Investigación II). El código de la API y del núcleo del modelo se agregará en los siguientes commits, conforme avance la implementación descrita en el Capítulo III de la tesis.
