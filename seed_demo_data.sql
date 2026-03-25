-- Demo Seed Data for ATS Application
-- Contains FICTIONAL data for demonstration purposes only
-- Run this AFTER migrations/000_create_users_table.sql and migrations/001_add_security_features.sql

-- Clean existing demo data (if any)
DELETE FROM applications WHERE candidate_id IN (SELECT id FROM candidates WHERE email LIKE '%demo.example.com');
DELETE FROM candidate_tags WHERE candidate_id IN (SELECT id FROM candidates WHERE email LIKE '%demo.example.com');
DELETE FROM candidates WHERE email LIKE '%demo.example.com';
DELETE FROM jobs WHERE company_name LIKE 'Demo%';
DELETE FROM engagements WHERE client_name LIKE 'Demo%';
DELETE FROM users WHERE email LIKE '%demo.example.com';

-- Create demo admin user
-- Password: DemoAdmin2024! (bcrypt hashed)
INSERT INTO users (email, name, pw_hash, created_at) VALUES
('admin@demo.example.com', 'Demo Administrator', 
 '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5oBhFvVZa4j3u', 
 CURRENT_TIMESTAMP);

-- Create demo engagements
INSERT INTO engagements (client_name, start_date, status, notes, created_at) VALUES
('Demo Tech Solutions Ltd', '2024-01-15', 'active', 'Leading technology consultancy firm seeking senior developers', CURRENT_TIMESTAMP),
('Demo Financial Services PLC', '2024-02-01', 'active', 'Investment banking client requiring compliance specialists', CURRENT_TIMESTAMP),
('Demo Healthcare Group', '2024-03-01', 'pending', 'NHS Trust requiring healthcare IT professionals', CURRENT_TIMESTAMP);

-- Create demo jobs
INSERT INTO jobs (title, description, location, salary_min, salary_max, company_name, role_type, status, public_token, created_at) VALUES
('Senior Full Stack Developer', 
 'We are seeking an experienced Full Stack Developer to join our growing team. You will work on cutting-edge web applications using React, Node.js, and PostgreSQL.',
 'London, UK (Hybrid)', 
 70000, 90000,
 'Demo Tech Solutions Ltd',
 'Engineering',
 'open',
 'demo-fullstack-dev-2024',
 CURRENT_TIMESTAMP),

('DevOps Engineer', 
 'Join our infrastructure team to build and maintain cloud-native applications. Experience with AWS, Docker, and Kubernetes required.',
 'Manchester, UK (Remote)',
 65000, 85000,
 'Demo Tech Solutions Ltd',
 'Engineering',
 'open',
 'demo-devops-2024',
 CURRENT_TIMESTAMP),

('Compliance Manager', 
 'Lead our compliance function ensuring adherence to FCA regulations. Strong knowledge of financial services required.',
 'London, UK (On-site)',
 80000, 100000,
 'Demo Financial Services PLC',
 'Compliance',
 'open',
 'demo-compliance-mgr-2024',
 CURRENT_TIMESTAMP),

('Clinical Systems Analyst', 
 'Support the implementation of electronic patient record systems. Healthcare IT experience essential.',
 'Birmingham, UK (Hybrid)',
 50000, 65000,
 'Demo Healthcare Group',
 'Healthcare IT',
 'draft',
 'demo-clinical-analyst-2024',
 CURRENT_TIMESTAMP);

-- Create demo candidates
INSERT INTO candidates (name, email, phone, role, status, cv_uploaded, created_at) VALUES
('Sarah Johnson', 'sarah.johnson@demo.example.com', '+44 7700 900001', 'Engineering', 'active', TRUE, CURRENT_TIMESTAMP),
('Michael Chen', 'michael.chen@demo.example.com', '+44 7700 900002', 'Engineering', 'active', TRUE, CURRENT_TIMESTAMP),
('Emma Williams', 'emma.williams@demo.example.com', '+44 7700 900003', 'Compliance', 'active', TRUE, CURRENT_TIMESTAMP),
('James Patel', 'james.patel@demo.example.com', '+44 7700 900004', 'Healthcare IT', 'active', TRUE, CURRENT_TIMESTAMP),
('Sophie Martinez', 'sophie.martinez@demo.example.com', '+44 7700 900005', 'Engineering', 'screening', TRUE, CURRENT_TIMESTAMP);

-- Create demo applications
-- Get job IDs (assuming they were just inserted)
DO $$
DECLARE
    fullstack_job_id INT;
    devops_job_id INT;
    compliance_job_id INT;
    clinical_job_id INT;
    sarah_id INT;
    michael_id INT;
    emma_id INT;
    james_id INT;
    sophie_id INT;
BEGIN
    -- Get job IDs
    SELECT id INTO fullstack_job_id FROM jobs WHERE public_token = 'demo-fullstack-dev-2024';
    SELECT id INTO devops_job_id FROM jobs WHERE public_token = 'demo-devops-2024';
    SELECT id INTO compliance_job_id FROM jobs WHERE public_token = 'demo-compliance-mgr-2024';
    SELECT id INTO clinical_job_id FROM jobs WHERE public_token = 'demo-clinical-analyst-2024';
    
    -- Get candidate IDs
    SELECT id INTO sarah_id FROM candidates WHERE email = 'sarah.johnson@demo.example.com';
    SELECT id INTO michael_id FROM candidates WHERE email = 'michael.chen@demo.example.com';
    SELECT id INTO emma_id FROM candidates WHERE email = 'emma.williams@demo.example.com';
    SELECT id INTO james_id FROM candidates WHERE email = 'james.patel@demo.example.com';
    SELECT id INTO sophie_id FROM candidates WHERE email = 'sophie.martinez@demo.example.com';
    
    -- Create applications
    INSERT INTO applications (candidate_id, job_id, status, applied_at, notes) VALUES
    (sarah_id, fullstack_job_id, 'shortlisted', CURRENT_TIMESTAMP - INTERVAL '5 days', 'Strong React and Node.js experience. Excellent cultural fit.'),
    (michael_id, devops_job_id, 'interview_scheduled', CURRENT_TIMESTAMP - INTERVAL '3 days', 'AWS certified. Available for interview next week.'),
    (emma_id, compliance_job_id, 'screening', CURRENT_TIMESTAMP - INTERVAL '2 days', 'FCA Part 4A approved. Currently reviewing application.'),
    (james_id, clinical_job_id, 'applied', CURRENT_TIMESTAMP - INTERVAL '1 day', 'NHS experience. Awaiting initial screening.'),
    (sophie_id, fullstack_job_id, 'applied', CURRENT_TIMESTAMP, 'Recent applicant. Portfolio looks promising.');
END $$;

-- Add some demo taxonomy categories
INSERT INTO taxonomy_categories (name, type, description, created_at) VALUES
('React.js', 'skill', 'Frontend JavaScript framework', CURRENT_TIMESTAMP),
('Node.js', 'skill', 'Backend JavaScript runtime', CURRENT_TIMESTAMP),
('AWS', 'skill', 'Amazon Web Services cloud platform', CURRENT_TIMESTAMP),
('Docker', 'skill', 'Container platform', CURRENT_TIMESTAMP),
('FCA Regulations', 'skill', 'UK Financial Conduct Authority compliance', CURRENT_TIMESTAMP),
('EPR Systems', 'skill', 'Electronic Patient Records', CURRENT_TIMESTAMP);

-- Create demo taxonomy tags
INSERT INTO taxonomy_tags (category_id, name, description, created_at)
SELECT id, name, description, created_at
FROM taxonomy_categories
WHERE type = 'skill';

COMMIT;

-- Verification query (uncomment to check)
-- SELECT 'Users' as table_name, COUNT(*) as count FROM users WHERE email LIKE '%demo.example.com'
-- UNION ALL
-- SELECT 'Engagements', COUNT(*) FROM engagements WHERE client_name LIKE 'Demo%'
-- UNION ALL
-- SELECT 'Jobs', COUNT(*) FROM jobs WHERE company_name LIKE 'Demo%'
-- UNION ALL
-- SELECT 'Candidates', COUNT(*) FROM candidates WHERE email LIKE '%demo.example.com'
-- UNION ALL
-- SELECT 'Applications', COUNT(*) FROM applications WHERE candidate_id IN (SELECT id FROM candidates WHERE email LIKE '%demo.example.com');
