-- ==========================================================
-- 「内容优化体验官」增量建表脚本（可重复执行）
-- 只新增表，不动 posts / users 等已有结构
--   post_audits  : 每次体检的快照，用来画“可引用度”走势
--   citations    : AI 引用追踪，记录哪天真被引用、引用了哪句
-- 执行：mysql -u root -p little_home < migrate_studio.sql
-- ==========================================================

USE little_home;

CREATE TABLE IF NOT EXISTS post_audits (
  id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  post_id    BIGINT UNSIGNED NOT NULL COMMENT '文章 id',
  score      TINYINT UNSIGNED NOT NULL COMMENT '可引用度总分 0-100',
  grade      VARCHAR(8)  NOT NULL COMMENT '等级 A/B/C/D',
  detail     LONGTEXT    DEFAULT NULL COMMENT '逐段体检结果(JSON)',
  created_at DATETIME    DEFAULT CURRENT_TIMESTAMP COMMENT '体检时间',
  INDEX idx_post_created (post_id, created_at),
  CONSTRAINT fk_audit_post FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '文章可引用度体检快照';

CREATE TABLE IF NOT EXISTS citations (
  id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  post_id     BIGINT UNSIGNED DEFAULT NULL COMMENT '被引用的文章',
  ai_name     VARCHAR(40)  NOT NULL COMMENT '哪个助手：豆包/元宝/Kimi/ChatGPT…',
  question    VARCHAR(255) DEFAULT NULL COMMENT '当时问的问题',
  quoted_text TEXT         DEFAULT NULL COMMENT '被引用的那句话',
  url         VARCHAR(500) DEFAULT NULL COMMENT '引用时带的链接',
  cited       TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '1=被引用 0=问了但没提我们',
  found_at    DATE         DEFAULT NULL COMMENT '发现日期',
  note        VARCHAR(255) DEFAULT NULL COMMENT '备注',
  created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_found (found_at),
  INDEX idx_post (post_id),
  CONSTRAINT fk_citation_post FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE SET NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = 'AI 引用追踪';
