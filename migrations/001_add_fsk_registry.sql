-- =========================================================================
-- Migration 001: add fsk_registry (directory used by the Register screen)
--
-- SAFE TO RUN ON AN EXISTING DATABASE:
--   * only CREATE TABLE IF NOT EXISTS - no DROP, no ALTER, no data changes
--   * does not touch users / indCoun_sessions / grpCoun_sessions
--
--   USE mocoss;
--   SOURCE /path/to/migrations/001_add_fsk_registry.sql;
-- =========================================================================

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS fsk_registry (
    id INT AUTO_INCREMENT PRIMARY KEY,
    identifier VARCHAR(50) NOT NULL UNIQUE,      -- matric / staff ID
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL,                   -- supervisor | field supervisor | counselor
    user_id INT NULL UNIQUE,                     -- filled in once the person registers
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_fsk_registry_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    INDEX idx_fsk_registry_identifier (identifier)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Example rows for testing (uncomment and edit):
-- INSERT INTO fsk_registry (identifier, full_name, email, role) VALUES
--   ('D2026101234', 'Test Counselor', 'test.counselor@mocoss.my', 'counselor');
