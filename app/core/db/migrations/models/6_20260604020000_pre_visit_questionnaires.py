from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `pre_visit_questionnaires` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `symptoms` LONGTEXT NOT NULL,
    `onset` VARCHAR(100),
    `severity` INT,
    `medications` LONGTEXT,
    `history` LONGTEXT,
    `questions` LONGTEXT,
    `ai_summary` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `appointment_id` BIGINT NOT NULL,
    `patient_id` BIGINT NOT NULL,
    CONSTRAINT `fk_previsit_appointments` FOREIGN KEY (`appointment_id`) REFERENCES `appointments` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_previsit_users_patient` FOREIGN KEY (`patient_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `pre_visit_questionnaires`;"""
