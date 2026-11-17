-- ==========================================================
-- 「我的小窝」MySQL 建库建表脚本
-- 使用方法（任选其一）：
--   1) 命令行:  mysql -u root -p < init.sql
--   2) Navicat/phpMyAdmin 中直接整段执行
-- ==========================================================

CREATE DATABASE IF NOT EXISTS little_home
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE little_home;

-- ----------------------------------------------------------
-- 用户表（登录账号）
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  username      VARCHAR(20)  NOT NULL UNIQUE COMMENT '用户名',
  password_hash VARCHAR(200) NOT NULL COMMENT 'PBKDF2 哈希: salt$hash',
  nickname      VARCHAR(30)  DEFAULT NULL COMMENT '昵称',
  is_admin      TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否管理员',
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
  INDEX idx_username (username)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '用户表';

-- ----------------------------------------------------------
-- 分类表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
  id   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(30) NOT NULL UNIQUE COMMENT '分类名',
  INDEX idx_name (name)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '文章分类';

-- ----------------------------------------------------------
-- 标签表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS tags (
  id   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(30) NOT NULL UNIQUE COMMENT '标签名',
  INDEX idx_name (name)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '文章标签';

-- ----------------------------------------------------------
-- 文章表（博客 / 学习总结）
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS posts (
  id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  title       VARCHAR(120) NOT NULL COMMENT '标题',
  content     MEDIUMTEXT   NOT NULL COMMENT '正文(Markdown/纯文本)',
  summary     VARCHAR(500) DEFAULT NULL COMMENT '手动摘要',
  cover       VARCHAR(300) DEFAULT NULL COMMENT '封面图访问路径',
  featured    TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否精选',
  status      VARCHAR(10) NOT NULL DEFAULT 'published' COMMENT '状态: published/draft',
  category_id INT UNSIGNED DEFAULT NULL COMMENT '分类',
  user_id     INT UNSIGNED DEFAULT NULL COMMENT '作者',
  views       INT UNSIGNED   DEFAULT 0 COMMENT '浏览量',
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间',
  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX idx_created (created_at),
  INDEX idx_featured (featured),
  INDEX idx_status (status),
  CONSTRAINT fk_posts_category FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL,
  CONSTRAINT fk_posts_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL,
  FULLTEXT KEY ft_title_content (title, content) WITH PARSER ngram COMMENT '中文全文搜索'
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '文章表';

-- ----------------------------------------------------------
-- 文章-标签 关联表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS post_tags (
  post_id BIGINT UNSIGNED NOT NULL,
  tag_id  INT UNSIGNED    NOT NULL,
  PRIMARY KEY (post_id, tag_id),
  CONSTRAINT fk_pt_post FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
  CONSTRAINT fk_pt_tag FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '文章标签关联';

-- ----------------------------------------------------------
-- 日记表（独立于文章，随手记录心情）
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS diaries (
  id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  title      VARCHAR(120) DEFAULT NULL COMMENT '标题(可空)',
  content    MEDIUMTEXT   NOT NULL COMMENT '日记内容',
  kind       VARCHAR(20)  NOT NULL DEFAULT 'diary' COMMENT '类型: diary/journal/essay/note',
  mood       VARCHAR(20)  DEFAULT NULL COMMENT '心情: 开心/难过/平静...',
  weather    VARCHAR(20)  DEFAULT NULL COMMENT '天气: 晴/雨/阴...',
  user_id    INT UNSIGNED DEFAULT NULL COMMENT '作者',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
  INDEX idx_created (created_at),
  INDEX idx_kind (kind),
  CONSTRAINT fk_diaries_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '日记表';

-- ----------------------------------------------------------
-- 相册照片表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS photos (
  id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  title       VARCHAR(120) DEFAULT NULL COMMENT '照片标题',
  filename    VARCHAR(300) NOT NULL COMMENT '访问路径 /uploads/photos/xxx.jpg',
  description VARCHAR(300) DEFAULT NULL COMMENT '描述',
  user_id     INT UNSIGNED DEFAULT NULL,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  CONSTRAINT fk_photos_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '相册照片';

-- ----------------------------------------------------------
-- 留言板
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
  id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nickname   VARCHAR(30)  NOT NULL COMMENT '留言人昵称',
  content    VARCHAR(500) NOT NULL COMMENT '留言内容',
  user_id    INT UNSIGNED DEFAULT NULL COMMENT '注册用户(可空)',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_messages_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '留言板';

-- ----------------------------------------------------------
-- 友情链接
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS friend_links (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(50)  NOT NULL COMMENT '站点名',
  url         VARCHAR(200) NOT NULL COMMENT '站点链接',
  avatar      VARCHAR(300) DEFAULT NULL COMMENT '头像/图标URL',
  description VARCHAR(200) DEFAULT NULL,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '友情链接';

-- ----------------------------------------------------------
-- 站点统计表（单行: id=1）
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS site_stats (
  id        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  total_pv  BIGINT UNSIGNED DEFAULT 0 COMMENT '总访问量',
  today_pv  BIGINT UNSIGNED DEFAULT 0 COMMENT '今日访问量',
  last_date DATE NOT NULL DEFAULT '2000-01-01' COMMENT '最后访问日期',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '站点统计';

-- 初始化统计行
INSERT INTO site_stats (id, total_pv)
SELECT 1, 0
WHERE NOT EXISTS (SELECT 1 FROM site_stats WHERE id = 1);

-- ----------------------------------------------------------
-- 站点设置表（单行: id=1，前台「关于我 / 页脚」从这里读）
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS site_settings (
  id           TINYINT UNSIGNED PRIMARY KEY COMMENT '固定为 1',
  site_name    VARCHAR(60)  DEFAULT '我的小窝' COMMENT '站点名称',
  site_desc    VARCHAR(200) DEFAULT NULL COMMENT '站点描述',
  author_name  VARCHAR(30)  DEFAULT NULL COMMENT '作者名',
  author_title VARCHAR(60)  DEFAULT NULL COMMENT '一句话身份',
  author_bio   TEXT         DEFAULT NULL COMMENT '个人简介（支持 Markdown）',
  location     VARCHAR(60)  DEFAULT NULL COMMENT '所在地',
  email        VARCHAR(120) DEFAULT NULL COMMENT '邮箱',
  github       VARCHAR(200) DEFAULT NULL COMMENT 'GitHub 主页',
  footer_text  VARCHAR(200) DEFAULT NULL COMMENT '页脚文字',
  updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '站点设置';

INSERT INTO site_settings (id)
SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM site_settings WHERE id = 1);
