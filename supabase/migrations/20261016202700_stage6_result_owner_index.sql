-- Cover both columns of the result ownership foreign key.
create index analysis_results_scan_owner_idx on public.analysis_results(scan_id, user_id);
