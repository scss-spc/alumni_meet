-- SC&SS JNU Alumni Meet Platform — Initial Seed Data

-- Insert Primary Meet: SC&SS JNU Alumni Meet 2026
INSERT INTO `meets` (`id`, `name`, `description`, `event_date`, `venue`, `status`)
VALUES (
    1,
    'Continuum — SC&SS JNU Alumni Meet 2026',
    'A gathering of the alumni, faculty, and scholars of the School of Computer and Systems Sciences (SC&SS), Jawaharlal Nehru University.',
    '2026-08-29 10:00:00',
    'Convention Centre, Jawaharlal Nehru University, New Delhi',
    'registration_open'
)
ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);
