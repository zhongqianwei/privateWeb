/** TailwindCSS 设计令牌 —— 颜色全部指向 CSS 变量，主题切换零成本 */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  darkMode: ['selector', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        ink: 'rgb(var(--text-rgb) / <alpha-value>)',
        muted: 'rgb(var(--text-2-rgb) / <alpha-value>)',
        faint: 'rgb(var(--text-3-rgb) / <alpha-value>)',
        line: 'rgb(var(--border-rgb) / <alpha-value>)',
        'line-strong': 'rgb(var(--border-strong-rgb) / <alpha-value>)',
        surface: 'rgb(var(--glass-rgb) / <alpha-value>)',
        'surface-strong': 'rgb(var(--glass-strong-rgb) / <alpha-value>)',
        canvas: 'rgb(var(--bg-rgb) / <alpha-value>)',
        elevated: 'rgb(var(--bg-elev-rgb) / <alpha-value>)',
        accent: {
          DEFAULT: 'rgb(var(--accent-rgb) / <alpha-value>)',
          soft: 'rgb(var(--accent-rgb) / 0.18)',
          purple: 'rgb(var(--accent-2-rgb) / <alpha-value>)',
          cyan: 'rgb(var(--accent-3-rgb) / <alpha-value>)',
          3: 'rgb(var(--accent-3-rgb) / <alpha-value>)',
        },
        danger: 'rgb(var(--danger-rgb) / <alpha-value>)',
        success: 'rgb(var(--success-rgb) / <alpha-value>)',
      },
      fontFamily: {
        sans: ['Inter', 'SF Pro Display', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', 'sans-serif'],
        mono: ['JetBrains Mono', 'SFMono-Regular', 'Consolas', 'Menlo', 'monospace'],
      },
      maxWidth: {
        content: '1180px',
        prose: '760px',
      },
      borderRadius: {
        '2xl': '1.25rem',
        '3xl': '1.75rem',
      },
      boxShadow: {
        glass: 'var(--shadow)',
        glow: '0 0 0 1px var(--accent-soft), 0 12px 40px rgba(80, 120, 200, 0.18)',
      },
      keyframes: {
        rise: {
          '0%': { opacity: '0', transform: 'translate3d(0, 12px, 0) scale(.994)' },
          '100%': { opacity: '1', transform: 'translate3d(0, 0, 0) scale(1)' },
        },
      },
      animation: {
        /* 收尾极缓的曲线 + 极轻微缩放，落位自然不僵硬；translate3d 走 GPU 合成 */
        rise: 'rise .5s cubic-bezier(.22, 1, .36, 1) both',
      },
    },
  },
  plugins: [],
}
