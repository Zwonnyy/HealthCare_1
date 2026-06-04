from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `appointments` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `requested_at` DATETIME(6) NOT NULL,
    `status` VARCHAR(9) NOT NULL COMMENT 'PENDING: PENDING\nCONFIRMED: CONFIRMED\nCANCELLED: CANCELLED\nCOMPLETED: COMPLETED' DEFAULT 'PENDING',
    `patient_notes` LONGTEXT,
    `doctor_notes` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `doctor_id` BIGINT NOT NULL,
    `patient_id` BIGINT NOT NULL,
    CONSTRAINT `fk_appointm_users_doctor` FOREIGN KEY (`doctor_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_appointm_users_patient` FOREIGN KEY (`patient_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;

        CREATE TABLE IF NOT EXISTS `health_goals` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `goal_type` VARCHAR(20) NOT NULL COMMENT 'WEIGHT: WEIGHT\nBLOOD_PRESSURE: BLOOD_PRESSURE\nEXERCISE_DAYS: EXERCISE_DAYS\nPAIN_SCORE: PAIN_SCORE\nCUSTOM: CUSTOM',
    `title` VARCHAR(100) NOT NULL,
    `target_value` DOUBLE NOT NULL,
    `current_value` DOUBLE,
    `unit` VARCHAR(20) NOT NULL,
    `deadline` DATE,
    `achieved` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `patient_id` BIGINT NOT NULL,
    CONSTRAINT `fk_healthgo_users_patient` FOREIGN KEY (`patient_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;

        CREATE TABLE IF NOT EXISTS `health_goal_history` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `recorded_value` DOUBLE NOT NULL,
    `recorded_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `goal_id` BIGINT NOT NULL,
    `patient_id` BIGINT NOT NULL,
    CONSTRAINT `fk_goalhist_healthgo_goal` FOREIGN KEY (`goal_id`) REFERENCES `health_goals` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_goalhist_users_patient` FOREIGN KEY (`patient_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;

        CREATE TABLE IF NOT EXISTS `drug_interactions` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `status` VARCHAR(10) NOT NULL COMMENT 'PENDING: PENDING\nCOMPLETED: COMPLETED\nFAILED: FAILED' DEFAULT 'PENDING',
    `result_text` LONGTEXT,
    `has_warning` BOOL NOT NULL DEFAULT 0,
    `error_message` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `record_id` BIGINT NOT NULL,
    CONSTRAINT `fk_drugint_medical_record` FOREIGN KEY (`record_id`) REFERENCES `medical_records` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;

        CREATE TABLE IF NOT EXISTS `health_reports` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `year` INT NOT NULL,
    `month` INT NOT NULL,
    `report_text` LONGTEXT,
    `status` VARCHAR(20) NOT NULL COMMENT 'PENDING: PENDING\nCOMPLETED: COMPLETED\nFAILED: FAILED' DEFAULT 'PENDING',
    `error_message` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `patient_id` BIGINT NOT NULL,
    CONSTRAINT `fk_healthrep_users_patient` FOREIGN KEY (`patient_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;

        CREATE TABLE IF NOT EXISTS `medication_checks` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `check_date` DATE NOT NULL,
    `checked_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `patient_id` BIGINT NOT NULL,
    `prescription_id` BIGINT NOT NULL,
    CONSTRAINT `fk_medcheck_users_patient` FOREIGN KEY (`patient_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_medcheck_prescrip_prescription` FOREIGN KEY (`prescription_id`) REFERENCES `prescriptions` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uid_med_check_prescription_date` (`prescription_id`, `check_date`)
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `medication_checks`;
        DROP TABLE IF EXISTS `health_reports`;
        DROP TABLE IF EXISTS `drug_interactions`;
        DROP TABLE IF EXISTS `health_goal_history`;
        DROP TABLE IF EXISTS `health_goals`;
        DROP TABLE IF EXISTS `appointments`;"""
