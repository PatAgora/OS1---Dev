-- 013_teams_calendar_event.sql
-- Req 8 follow-up — Microsoft Graph Teams calendar integration.
-- When OS1 schedules an interview it calls Microsoft Graph to create a
-- real calendar event in the staff user's Outlook calendar with a Teams
-- meeting auto-attached. The returned event ID and Teams join URL are
-- stored on the application so we can update / cancel the meeting on
-- reschedule and surface the join link in the email + UI.

ALTER TABLE applications ADD COLUMN IF NOT EXISTS interview_graph_event_id VARCHAR(128);
ALTER TABLE applications ADD COLUMN IF NOT EXISTS interview_teams_join_url VARCHAR(500);
