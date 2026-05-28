from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `health_logs` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `log_date` DATE NOT NULL,
    `pain_score` INT NOT NULL,
    `mood` VARCHAR(8) NOT NULL COMMENT 'GREAT: GREAT\nGOOD: GOOD\nNORMAL: NORMAL\nBAD: BAD\nTERRIBLE: TERRIBLE',
    `symptoms_text` LONGTEXT NOT NULL,
    `notes` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `patient_id` BIGINT NOT NULL,
    `record_id` BIGINT,
    CONSTRAINT `fk_health_l_users_patient` FOREIGN KEY (`patient_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_health_l_medical_record` FOREIGN KEY (`record_id`) REFERENCES `medical_records` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `health_log_analyses` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `analysis_text` LONGTEXT,
    `status` VARCHAR(10) NOT NULL COMMENT 'PENDING: PENDING\nGENERATING: GENERATING\nCOMPLETED: COMPLETED\nFAILED: FAILED' DEFAULT 'PENDING',
    `error_message` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `patient_id` BIGINT NOT NULL,
    `record_id` BIGINT,
    CONSTRAINT `fk_health_a_users_patient` FOREIGN KEY (`patient_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_health_a_medical_record` FOREIGN KEY (`record_id`) REFERENCES `medical_records` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `health_log_analyses`;
        DROP TABLE IF EXISTS `health_logs`;"""