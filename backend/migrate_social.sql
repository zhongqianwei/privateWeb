-- ==========================================================
-- 「我的小窝」社交化升级迁移（可重复执行，安全幂等）
-- 用途：给已有库 upgrade 到支持「头像 / 管理员 / 个人空间 / 说说」
-- 用法：mysql -u root -p < migrate_social.sql
-- ==========================================================

USE little_home;

-- 1) users 增加头像字段（MySQL 5.7+ 用 IF NOT EXISTS 的存储过程兜底）
SET @dbname = DATABASE();
SET @has_avatar = (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'users' AND COLUMN_NAME = 'avatar'
);
SET @sql = IF(@has_avatar = 0,
  'ALTER TABLE users ADD COLUMN avatar VARCHAR(300) DEFAULT NULL COMMENT ''头像URL'' AFTER nickname',
  'SELECT ''avatar 字段已存在，跳过'' AS msg'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2) 把指定管理员账号的 is_admin 置为 1
--    用户名来自 .env 的 ADMIN_USERNAME，默认 960660626
--    同时兼容库里已有的站主账号 admin，避免升级后把自己锁在门外
UPDATE users SET is_admin = 1 WHERE username IN ('960660626', 'admin');

-- 3) diaries.kind 追加 '说说' 支持（VARCHAR 类型无需改表，仅更新注释）
ALTER TABLE diaries
  MODIFY COLUMN kind VARCHAR(20) NOT NULL DEFAULT 'diary'
  COMMENT '类型: diary日记/journal/essay随笔/note笔记/saying说说';

-- 4) 为常用查询补索引（个人空间按用户聚合）
SET @has_idx = (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = 'posts' AND INDEX_NAME = 'idx_posts_user'
);
SET @sql2 = IF(@has_idx = 0,
  'ALTER TABLE posts ADD INDEX idx_posts_user (user_id)',
  'SELECT ''idx_posts_user 已存在，跳过'' AS msg'
);
PREPARE stmt2 FROM @sql2;
EXECUTE stmt2;
DEALLOCATE PREPARE stmt2;

SELECT '迁移完成 ✅' AS result;
