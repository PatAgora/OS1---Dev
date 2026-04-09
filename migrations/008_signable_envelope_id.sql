-- Migration 008: Add Signable envelope ID column to declaration_records (Req-005)
-- Allows the associate portal declaration form to track the envelope ID returned
-- from Signable when a declaration is sent for e-signature.
--
-- Signable integration is gated by SIGNABLE_LIVE_CALLS env flag — when stubbed,
-- this column receives values like "stub-<uuid>" so the local flow can be
-- exercised end-to-end without making any billable Signable API calls.

ALTER TABLE declaration_records ADD COLUMN signable_envelope_id VARCHAR(64);
