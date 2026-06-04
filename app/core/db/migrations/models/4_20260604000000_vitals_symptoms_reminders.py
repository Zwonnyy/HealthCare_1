from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `vital_records` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `systolic` INT,
    `diastolic` INT,
    `blood_sugar` DOUBLE,
    `weight` DOUBLE,
    `heart_rate` INT,
    `notes` LONGTEXT,
    `alert_message` LONGTEXT,
    `recorded_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `patient_id` BIGINT NOT NULL,
    CONSTRAINT `fk_vital_re_users_xxxxxxxx` FOREIGN KEY (`patient_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;

        CREATE TABLE IF NOT EXISTS `symptom_checks` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `symptom_text` LONGTEXT NOT NULL,
    `ai_assessment` LONGTEXT,
    `urgency` VARCHAR(10),
    `suggest_appointment` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `patient_id` BIGINT NOT NULL,
    CONSTRAINT `fk_symptom_users_xxxxxxxx` FOREIGN KEY (`patient_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;

        CREATE TABLE IF NOT EXISTS `medication_reminders` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `reminder_time` VARCHAR(5) NOT NULL,
    `enabled` BOOL NOT NULL DEFAULT 1,
    `last_notified_date` DATE,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `patient_id` BIGINT NOT NULL,
    CONSTRAINT `fk_medicati_users_xxxxxxxx` FOREIGN KEY (`patient_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `medication_reminders`;
        DROP TABLE IF EXISTS `symptom_checks`;
        DROP TABLE IF EXISTS `vital_records`;"""