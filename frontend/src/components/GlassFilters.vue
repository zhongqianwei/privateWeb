<script setup>
/**
 * 全局玻璃滤镜定义（不渲染可见内容）。
 *
 * 每种形状一条 SVG 滤镜链（作用于 backdrop 背景）：
 *  1) 位移折射：feDisplacementMap 按导航图 R/G 通道逐点取色偏移。
 *     导航图由真实玻璃截面函数 + Snell 定律生成（见 scripts/gen-glass-maps.mjs）：
 *     超椭圆倒角剖面 (1-(1-t)^p)^(1/p)，外沿垂直、中心水平，C1 连续无棱角；
 *     位移量 = 厚度·tan(θs-θr)·Fresnel，边缘最强、向内平滑收敛。
 *  2) 曲面高光：用贴图 B 通道(厚度场)重建法线，斜向平行光照射，
 *     只有倒角最陡的一圈受光，因此各边缘明暗不同。
 *
 * ⚠️ feImage 必须使用内联 data URI。引用外部 URL 时 Chromium 在
 *    CSS backdrop-filter 里会静默输出空图，整条折射链失效。
 */
import { panel as panelMap, pill as pillMap, circle as circleMap } from '../assets/glass-maps.js'

const maps = { panel: panelMap, pill: pillMap, circle: circleMap }
const shapes = ['panel', 'pill', 'circle']
</script>

<template>
  <svg class="glass-defs" width="0" height="0" aria-hidden="true" focusable="false">
    <defs>
      <template v-for="shape in shapes" :key="shape">
        <filter
          :id="`glass-${shape}`"
          filterUnits="objectBoundingBox"
          primitiveUnits="objectBoundingBox"
          x="0" y="0" width="1" height="1"
          color-interpolation-filters="sRGB"
        >
          <!-- 导航图：R 横偏移 / G 纵偏移 / B 玻璃厚度，128 = 零偏移。
               用 objectBoundingBox 单位铺满元素包围盒——用百分比时 Chromium 会
               按图片固有尺寸(256px)绘制，贴图与元素错位，折射整体失效。 -->
          <feImage
            :href="maps[shape]"
            x="0" y="0" width="1" height="1"
            preserveAspectRatio="none"
            result="MAP"
          />

          <!-- 折射：Snell 定律逐点位移，边缘最强、向内平滑收敛 -->
          <feDisplacementMap
            data-glass-displace
            in="SourceGraphic" in2="MAP"
            scale="0.03" xChannelSelector="R" yChannelSelector="G"
            result="REFRACT"
          />

          <!-- 从厚度场提取曲面：把 B 通道(倒角高度)搬进 alpha，RGB 清零 -->
          <feColorMatrix
            in="MAP" type="matrix"
            values="0 0 0 0 0
                    0 0 0 0 0
                    0 0 0 0 0
                    0 0 1 0 0"
            result="HEIGHT"
          />
          <feGaussianBlur in="HEIGHT" stdDeviation="0.0035" result="HEIGHT_SOFT" />

          <!-- 曲面高光：只在倒角最陡的一圈出光，平整中心完全不受光 -->
          <feSpecularLighting
            data-glass-specular
            in="HEIGHT_SOFT"
            surfaceScale="0.02" specularConstant="1.1" specularExponent="260"
            lighting-color="#f7faff" result="SPEC"
          >
            <feDistantLight azimuth="225" elevation="44" />
          </feSpecularLighting>

          <!-- 高光以 screen 叠加，保留折射细节不发灰 -->
          <feBlend in="SPEC" in2="REFRACT" mode="screen" result="OUT" />
        </filter>
      </template>
    </defs>
  </svg>
</template>

<style scoped>
.glass-defs {
  position: absolute;
  width: 0;
  height: 0;
  overflow: hidden;
  pointer-events: none;
}
</style>
