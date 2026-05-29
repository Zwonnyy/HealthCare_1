from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `notifications` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `notification_type` VARCHAR(30) NOT NULL,
    `title` VARCHAR(100) NOT NULL,
    `body` LONGTEXT NOT NULL,
    `is_read` BOOL NOT NULL DEFAULT 0,
    `read_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` BIGINT NOT NULL,
    CONSTRAINT `fk_notifica_users_xxxxxxxx` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `notifications`;"""
