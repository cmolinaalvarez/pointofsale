BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE schemaname = 'public' AND indexname = 'ux_stocks_wh_prod'
  ) THEN
    EXECUTE 'CREATE UNIQUE INDEX ux_stocks_wh_prod ON public.stocks(warehouse_id, product_id)';
  END IF;
END$$;

WITH params AS (
  SELECT
    '22cf0b09-9a4b-4d81-b7ce-7b70c13f16f3'::uuid AS v_user,
    now()::timestamptz AS v_ts
),
pairs AS (
  SELECT w.id AS warehouse_id, p.id AS product_id
  FROM public.warehouses w
  CROSS JOIN public.products p
  WHERE w.active = true AND p.active = true
),
ins AS (
  INSERT INTO public.stocks
    (id, warehouse_id, product_id, quantity, min_stock, max_stock, reserved, active, user_id, created_at, updated_at)
  SELECT
    gen_random_uuid(), pairs.warehouse_id, pairs.product_id,
    0, 0, 0, 0, true,
    (SELECT v_user FROM params),
    (SELECT v_ts FROM params),
    (SELECT v_ts FROM params)
  FROM pairs
  ON CONFLICT (warehouse_id, product_id) DO NOTHING
  RETURNING 1
)
SELECT COUNT(*) AS filas_insertadas FROM ins;

COMMIT;
