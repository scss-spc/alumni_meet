-- SC&SS JNU Alumni Meet Platform — Database Schema (TiDB)

CREATE TABLE IF NOT EXISTS `alumni` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `full_name` VARCHAR(200) NOT NULL,
    `graduation_year` SMALLINT NULL,
    `course` VARCHAR(100) NULL,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `phone` VARCHAR(30) NULL,
    `organization` VARCHAR(255) NULL,
    `designation` VARCHAR(255) NULL,
    `current_location` VARCHAR(255) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `meets` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `description` TEXT NULL,
    `event_date` DATETIME NULL,
    `venue` VARCHAR(500) NULL,
    `status` VARCHAR(30) NOT NULL DEFAULT 'planning',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `meet_responses` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `meet_id` BIGINT NOT NULL,
    `alumni_id` BIGINT NOT NULL,
    `attending` BOOLEAN NOT NULL DEFAULT TRUE,
    `guest_count` INT NOT NULL DEFAULT 0,
    `total_attendees` INT NOT NULL DEFAULT 1,
    `dietary_preferences` TEXT NULL,
    `suggestions` TEXT NULL,
    `submitted_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_mr_meet` FOREIGN KEY (`meet_id`) REFERENCES `meets`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_mr_alumni` FOREIGN KEY (`alumni_id`) REFERENCES `alumni`(`id`) ON DELETE CASCADE,
    CONSTRAINT `uk_meet_alumni` UNIQUE (`meet_id`, `alumni_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `contributions` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `meet_id` BIGINT NOT NULL,
    `alumni_id` BIGINT NOT NULL,
    `amount` DECIMAL(12,2) NOT NULL,
    `currency` CHAR(3) NOT NULL DEFAULT 'INR',
    `transaction_reference` VARCHAR(255) NULL,
    `payment_screenshot_path` VARCHAR(1000) NULL,
    `payment_status` VARCHAR(30) NOT NULL DEFAULT 'submitted',
    `submitted_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `paid_at` DATETIME NULL,
    `verified_at` DATETIME NULL,
    `verified_by` BIGINT NULL,
    `notes` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_contrib_meet` FOREIGN KEY (`meet_id`) REFERENCES `meets`(`id`) ON DELETE RESTRICT,
    CONSTRAINT `fk_contrib_alumni` FOREIGN KEY (`alumni_id`) REFERENCES `alumni`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `recognition_preferences` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `meet_id` BIGINT NOT NULL,
    `alumni_id` BIGINT NOT NULL,
    `recognition_type` VARCHAR(50) NOT NULL DEFAULT 'name_only',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_recog_meet` FOREIGN KEY (`meet_id`) REFERENCES `meets`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_recog_alumni` FOREIGN KEY (`alumni_id`) REFERENCES `alumni`(`id`) ON DELETE CASCADE,
    CONSTRAINT `uk_meet_alumni_recog` UNIQUE (`meet_id`, `alumni_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `volunteers` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `full_name` VARCHAR(200) NOT NULL,
    `email` VARCHAR(255) NULL,
    `phone` VARCHAR(30) NULL,
    `role` VARCHAR(100) NULL,
    `status` VARCHAR(30) NOT NULL DEFAULT 'active',
    `notes` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `activities` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `meet_id` BIGINT NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `description` TEXT NULL,
    `status` VARCHAR(30) NOT NULL DEFAULT 'planned',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_act_meet` FOREIGN KEY (`meet_id`) REFERENCES `meets`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `volunteer_assignments` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `activity_id` BIGINT NOT NULL,
    `volunteer_id` BIGINT NOT NULL,
    `responsibility` TEXT NULL,
    `status` VARCHAR(30) NOT NULL DEFAULT 'assigned',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_va_activity` FOREIGN KEY (`activity_id`) REFERENCES `activities`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_va_volunteer` FOREIGN KEY (`volunteer_id`) REFERENCES `volunteers`(`id`) ON DELETE CASCADE,
    CONSTRAINT `uk_activity_volunteer` UNIQUE (`activity_id`, `volunteer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `users` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `full_name` VARCHAR(200) NOT NULL,
    `role` VARCHAR(50) NOT NULL DEFAULT 'organizer',
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `audit_logs` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` BIGINT NULL,
    `action` VARCHAR(100) NOT NULL,
    `entity_type` VARCHAR(50) NOT NULL,
    `entity_id` BIGINT NULL,
    `old_value` TEXT NULL,
    `new_value` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
