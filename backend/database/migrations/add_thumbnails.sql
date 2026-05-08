-- SmartStudy Migration: Add thumbnail support to session_frames
-- Run once to enable session replay thumbnails

ALTER TABLE session_frames ADD COLUMN thumbnail_bytes BLOB;

-- Index for faster session frame queries
CREATE INDEX IF NOT EXISTS idx_frames_focus_state
    ON session_frames(session_id, focus_state);
