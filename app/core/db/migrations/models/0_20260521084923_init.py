from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `users` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `email` VARCHAR(40) NOT NULL,
    `hashed_password` VARCHAR(128) NOT NULL,
    `name` VARCHAR(20) NOT NULL,
    `gender` VARCHAR(6) NOT NULL COMMENT 'MALE: MALE\nFEMALE: FEMALE',
    `birthday` DATE NOT NULL,
    `phone_number` VARCHAR(11) NOT NULL,
    `role` VARCHAR(7) NOT NULL COMMENT 'DOCTOR: DOCTOR\nPATIENT: PATIENT' DEFAULT 'PATIENT',
    `is_active` BOOL NOT NULL DEFAULT 1,
    `is_admin` BOOL NOT NULL DEFAULT 0,
    `last_login` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `medical_records` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `diagnosis` LONGTEXT NOT NULL,
    `symptoms` LONGTEXT NOT NULL,
    `notes` LONGTEXT,
    `visited_at` DATETIME(6) NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `doctor_id` BIGINT NOT NULL,
    `patient_id` BIGINT NOT NULL,
    CONSTRAINT `fk_medical__users_b81426d6` FOREIGN KEY (`doctor_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_medical__users_18037853` FOREIGN KEY (`patient_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `prescriptions` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `medication_name` VARCHAR(100) NOT NULL,
    `dosage` VARCHAR(50) NOT NULL,
    `frequency` VARCHAR(50) NOT NULL,
    `duration_days` INT NOT NULL,
    `instructions` LONGTEXT,
    `record_id` BIGINT NOT NULL,
    CONSTRAINT `fk_prescrip_medical__f8cad27c` FOREIGN KEY (`record_id`) REFERENCES `medical_records` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `guides` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `medication_guide` LONGTEXT,
    `lifestyle_guide` LONGTEXT,
    `status` VARCHAR(10) NOT NULL COMMENT 'PENDING: PENDING\nGENERATING: GENERATING\nCOMPLETED: COMPLETED\nFAILED: FAILED' DEFAULT 'PENDING',
    `error_message` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `record_id` BIGINT NOT NULL,
    CONSTRAINT `fk_guides_medical__532b52ea` FOREIGN KEY (`record_id`) REFERENCES `medical_records` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)
