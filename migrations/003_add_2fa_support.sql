-- Migration: Add 2FA/MFA Support
-- Date: 2026-01-16
-- Description: Add Two-Factor Authentication columns to users table

-- Add 2FA columns to users table
ALTER TABLE users 
  ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(32),
  ADD COLUMN IF NOT EXISTS totp_enabled BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS backup_codes TEXT;

-- Add password history table for password reuse prevention
CREATE TABLE IF NOT EXISTS password_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create index on password_history
CREATE INDEX IF NOT EXISTS idx_password_history_user_id ON password_history(user_id);
CREATE INDEX IF NOT EXISTS idx_password_history_created_at ON password_history(created_at);

-- Add session security columns
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS session_token VARCHAR(255),
  ADD COLUMN IF NOT EXISTS last_ip VARCHAR(45),
  ADD COLUMN IF NOT EXISTS last_user_agent TEXT;

-- Create indexes for security queries
CREATE INDEX IF NOT EXISTS idx_users_totp_enabled ON users(totp_enabled);
CREATE INDEX IF NOT EXISTS idx_users_session_token ON users(session_token);
