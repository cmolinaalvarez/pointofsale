delete FROM public.countries;
select * FROM public.countries;
TRUNCATE TABLE public.countries RESTART IDENTITY;
SELECT last_value FROM public.countries_id_seq;

delete FROM public.divisions;
select * FROM public.divisions;
TRUNCATE TABLE divisions, countries RESTART IDENTITY CASCADE;
SELECT pg_get_serial_sequence('divisions', 'id');
SELECT last_value FROM public.divisions_id_seq;

delete FROM public.municipalities;
select * FROM public.municipalities;
TRUNCATE TABLE public.municipalities RESTART IDENTITY;
SELECT last_value FROM public.municipalities_id_seq;

delete from public.categories;
TRUNCATE TABLE public.categories RESTART IDENTITY;
select * from public.categories;

TRUNCATE TABLE products, categories, brands, units RESTART IDENTITY CASCADE;
delete from public.products;
select * from public.products;
SELECT last_value FROM public.products_id_seq;

select * from public.orders
select * from public.order_items
delete from public.order_items
delete from public.orders
TRUNCATE TABLE orders, order_items RESTART IDENTITY CASCADE;
SELECT last_value FROM public.orders_id_seq;
SELECT last_value FROM public.order_items_id_seq;

select * from public.entries
select * from public.entry_items
delete from public.entry_items
delete from public.entries
TRUNCATE TABLE entries, entry_items RESTART IDENTITY CASCADE;
SELECT last_value FROM public.entries_id_seq;
SELECT last_value FROM public.entry_items_id_seq;
select * from public.concepts
delete from public.concepts
TRUNCATE TABLE concepts RESTART IDENTITY;
SELECT last_value FROM public.concepts_id_seq;

select * from public.third_parties
delete from public.third_parties
TRUNCATE TABLE third_parties RESTART IDENTITY;
SELECT last_value FROM public.third_parties_id_seq;

select * from public.units
delete from public.units
TRUNCATE TABLE units RESTART IDENTITY;
SELECT last_value FROM public.units_id_seq;

select * from public.brands
delete from public.brands
TRUNCATE TABLE brands RESTART IDENTITY;
SELECT last_value FROM public.brands_id_seq;












