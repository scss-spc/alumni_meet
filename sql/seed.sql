-- SC&SS JNU Alumni Meet Platform — Initial Seed Data

-- Insert Primary Meet: SC&SS JNU Alumni Meet 2026
INSERT INTO `meets` (`id`, `name`, `description`, `event_date`, `venue`, `status`)
VALUES (
    1,
    'SC&SS JNU Alumni Meet 2026',
    'A gathering of the alumni, faculty, and scholars of the School of Computer and Systems Sciences (SC&SS), Jawaharlal Nehru University.',
    '2026-08-29 10:00:00',
    'Convention Centre / SC&SS Auditorium, Jawaharlal Nehru University, New Delhi',
    'registration_open'
)
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);

-- Insert Initial Organizing Activities for Meet 1
INSERT INTO `activities` (`meet_id`, `name`, `description`, `status`)
VALUES 
    (1, 'Registration & Welcome Desk', 'Managing on-spot arrivals, badge collection, and alumni kit distribution.', 'planned'),
    (1, 'Catering & Hospitality', 'Lunch, tea, high-tea arrangements, and dietary preference coordination.', 'planned'),
    (1, 'Stage & Cultural Coordination', 'Keynote address, felicitation of senior professors, and cultural presentations.', 'planned'),
    (1, 'Photography & Memory Archive', 'Documenting the gathering, photo booth, and batch group photo sessions.', 'planned'),
    (1, 'Alumni Outreach & Communication', 'Coordination with batch representatives, invitations, and attendee assistance.', 'planned'),
    (1, 'Technical & Venue Support', 'Audio-visual setup, projection, Wi-Fi support, and hybrid participation link.', 'planned')
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);
