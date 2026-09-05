-- SC&SS JNU Alumni Meet Platform — Indexes

-- Alumni performance indexes
CREATE INDEX `idx_alumni_grad_year` ON `alumni` (`graduation_year`);
CREATE INDEX `idx_alumni_course` ON `alumni` (`course`);
CREATE INDEX `idx_alumni_name` ON `alumni` (`full_name`);

-- Meet Responses indexes
CREATE INDEX `idx_mr_attending` ON `meet_responses` (`meet_id`, `attending`);

-- Contributions indexes
CREATE INDEX `idx_contrib_status` ON `contributions` (`meet_id`, `payment_status`);
CREATE INDEX `idx_contrib_alumni` ON `contributions` (`alumni_id`);
CREATE INDEX `idx_contrib_tx_ref` ON `contributions` (`transaction_reference`);

-- Volunteer & Activity indexes
CREATE INDEX `idx_vol_status` ON `volunteers` (`status`);
CREATE INDEX `idx_act_meet_status` ON `activities` (`meet_id`, `status`);
CREATE INDEX `idx_va_volunteer` ON `volunteer_assignments` (`volunteer_id`);

-- Users & Audit Logs
CREATE INDEX `idx_audit_entity` ON `audit_logs` (`entity_type`, `entity_id`);
CREATE INDEX `idx_audit_user` ON `audit_logs` (`user_id`);
