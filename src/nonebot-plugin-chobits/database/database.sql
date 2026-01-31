-- 创建数据库 chobits
CREATE DATABASE IF NOT EXISTS `chobits` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `chobits`;

-- 设置表
DROP TABLE IF EXISTS `settings`;
CREATE TABLE IF NOT EXISTS `settings`
(
    `id`           bigint UNSIGNED                                                            NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `key`          varchar(24) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci               NOT NULL DEFAULT '' COMMENT '键',
    `value`        text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci                      NULL     DEFAULT NULL COMMENT '值',
    `description`  text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci                      NULL     DEFAULT NULL COMMENT '描述',
    `status`       enum ('normal','disable') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'normal' COMMENT '状态',
    `created_time` timestamp                                                                  NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` timestamp                                                                  NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted_time` timestamp                                                                  NULL     DEFAULT NULL COMMENT '删除时间',
    PRIMARY KEY (`id`),
    KEY `users_key_index` (`key`) USING BTREE COMMENT '键索引',
    KEY `users_created_time_index` (`created_time`) USING BTREE COMMENT '创建时间索引',
    KEY `users_updated_time_index` (`updated_time`) USING BTREE COMMENT '更新时间索引'
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci COMMENT ='设置表';

-- 用户表
DROP TABLE IF EXISTS `users`;
CREATE TABLE IF NOT EXISTS `users`
(
    `id`            bigint UNSIGNED                                                        NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `qq`            varchar(24) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci           NOT NULL DEFAULT '' COMMENT 'QQ号',
    `avatar`        text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci                  NULL     DEFAULT NULL COMMENT '头像',
    `register_time` timestamp                                                              NULL     DEFAULT NULL COMMENT 'QQ注册时间',
    `status`        enum ('normal','ban') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'normal' COMMENT '状态',
    `token`         varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci           NOT NULL DEFAULT '' COMMENT 'token',
    `created_time`  timestamp                                                              NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time`  timestamp                                                              NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted_time`  timestamp                                                              NULL     DEFAULT NULL COMMENT '删除时间',
    PRIMARY KEY (`id`),
    KEY `users_qq_index` (`qq`) USING BTREE COMMENT 'QQ索引',
    KEY `users_register_time_index` (`register_time`) USING BTREE COMMENT 'QQ注册时间索引',
    KEY `users_created_time_index` (`created_time`) USING BTREE COMMENT '创建时间索引',
    KEY `users_updated_time_index` (`updated_time`) USING BTREE COMMENT '更新时间索引'
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci COMMENT ='用户表';

-- 功能表
DROP TABLE IF EXISTS `functions`;
CREATE TABLE IF NOT EXISTS `functions`
(
    `id`           bigint UNSIGNED                                                            NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `name`         varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci               NOT NULL DEFAULT '' COMMENT '功能名称',
    `description`  text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci                      NULL     DEFAULT NULL COMMENT '功能描述',
    `status`       enum ('normal','disable') CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'normal' COMMENT '状态',
    `created_time` timestamp                                                                  NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` timestamp                                                                  NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted_time` timestamp                                                                  NULL     DEFAULT NULL COMMENT '删除时间',
    PRIMARY KEY (`id`),
    KEY `functions_name_index` (`name`) USING BTREE COMMENT '功能名称索引',
    KEY `functions_status_index` (`status`) USING BTREE COMMENT '状态索引',
    KEY `functions_created_time_index` (`created_time`) USING BTREE COMMENT '创建时间索引',
    KEY `functions_updated_time_index` (`updated_time`) USING BTREE COMMENT '更新时间索引'
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci COMMENT ='功能表';

-- 权限表
DROP TABLE IF EXISTS `permissions`;
CREATE TABLE IF NOT EXISTS `permissions`
(
    `id`           bigint UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `users_id`     int unsigned    NOT NULL DEFAULT 0 COMMENT '用户 ID',
    `functions_id` int unsigned    NOT NULL DEFAULT 0 COMMENT '功能 ID',
    `created_time` timestamp       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` timestamp       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted_time` timestamp       NULL     DEFAULT NULL COMMENT '删除时间',
    PRIMARY KEY (`id`),
    KEY `permissions_created_time_index` (`created_time`) USING BTREE COMMENT '创建时间索引',
    KEY `permissions_updated_time_index` (`updated_time`) USING BTREE COMMENT '更新时间索引'
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci COMMENT ='权限表';