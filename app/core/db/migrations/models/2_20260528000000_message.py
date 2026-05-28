from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `messages` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `content` LONGTEXT NOT NULL,
    `is_read` BOOL NOT NULL DEFAULT 0,
    `read_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `sender_id` BIGINT NOT NULL,
    `receiver_id` BIGINT NOT NULL,
    `record_id` BIGINT,
    CONSTRAINT `fk_messages_users_sender` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_messages_users_receiver` FOREIGN KEY (`receiver_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_messages_medical_record` FOREIGN KEY (`record_id`) REFERENCES `medical_records` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `messages`;"""
