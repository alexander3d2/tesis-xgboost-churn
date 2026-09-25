-- Introspección de esquema real (solo metadatos, ninguna de estas queries
-- trae filas ni datos personales de afiliados).
-- Ajusta la lista de esquemas en cada WHERE según lo que necesites revisar.

-- 1) Tablas por esquema
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema IN ('bo_account', 'bo_membership', 'bo_commissions', 'bo_wallet')
ORDER BY table_schema, table_name;

-- 2) Columnas y tipos de cada tabla
SELECT
    table_schema,
    table_name,
    ordinal_position,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema IN ('bo_account', 'bo_membership', 'bo_commissions', 'bo_wallet')
ORDER BY table_schema, table_name, ordinal_position;

-- 3) Llaves primarias declaradas
SELECT
    tc.table_schema,
    tc.table_name,
    kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
   AND tc.table_schema = kcu.table_schema
WHERE tc.constraint_type = 'PRIMARY KEY'
  AND tc.table_schema IN ('bo_account', 'bo_membership', 'bo_commissions', 'bo_wallet')
ORDER BY tc.table_schema, tc.table_name;

-- 4) Relaciones (foreign keys) DECLARADAS a nivel de base de datos.
-- Puede salir vacía o incompleta: en microservicios es normal que las
-- relaciones entre esquemas de servicios distintos se manejen solo a nivel
-- de aplicación (ej. una columna "idsponsor" que apunta conceptualmente a
-- bo_account.user.id, sin una FK real declarada en Postgres).
SELECT
    tc.table_schema  AS esquema_origen,
    tc.table_name    AS tabla_origen,
    kcu.column_name  AS columna_origen,
    ccu.table_schema AS esquema_destino,
    ccu.table_name   AS tabla_destino,
    ccu.column_name  AS columna_destino
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
   AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu
    ON tc.constraint_name = ccu.constraint_name
   AND tc.table_schema = ccu.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_schema, tc.table_name;

-- 5) Si el punto 4 sale vacío: relaciones "por convención de nombre",
-- útil para inferir relaciones no declaradas formalmente (columnas que
-- parecen apuntar a un id de otra tabla, por su nombre).
SELECT table_schema, table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema IN ('bo_account', 'bo_membership', 'bo_commissions', 'bo_wallet')
  AND (
      column_name ILIKE 'id%'
      OR column_name ILIKE '%\_id'
      OR column_name ILIKE '%iduser%'
      OR column_name ILIKE '%idsponsor%'
      OR column_name ILIKE '%idslave%'
  )
ORDER BY table_schema, table_name, column_name;
