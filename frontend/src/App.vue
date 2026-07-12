<template>
  <n-config-provider :theme="darkTheme">
    <n-message-provider>
      <n-layout position="absolute">
        <n-layout-header bordered class="app-header">
          <div class="header-content">
            <div class="logo" @click="$router.push('/')">FongMi TV</div>
            <nav class="nav-links">
              <router-link to="/">首页</router-link>
              <router-link to="/live">直播</router-link>
              <router-link to="/search">搜索</router-link>
              <router-link to="/history">历史</router-link>
              <router-link to="/keep">收藏</router-link>
              <router-link to="/setting">设置</router-link>
            </nav>
          </div>
        </n-layout-header>
        <n-layout-content content-style="padding: 0;">
          <router-view />
        </n-layout-content>
      </n-layout>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { NConfigProvider, NMessageProvider, NLayout, NLayoutHeader, NLayoutContent, darkTheme } from 'naive-ui'
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f13; color: #e0e0e0; }
a { text-decoration: none; color: inherit; }

.app-header { height: 56px; display: flex; align-items: center; background: rgba(15,15,20,0.95); backdrop-filter: blur(10px); }
.header-content { max-width: 1600px; width: 100%; margin: 0 auto; padding: 0 20px; display: flex; align-items: center; gap: 32px; }
.logo { font-size: 20px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 8px; }
.nav-links { display: flex; gap: 20px; }
.nav-links a { font-size: 14px; color: #888; transition: color 0.2s; padding: 6px 12px; border-radius: 6px; }
.nav-links a:hover, .nav-links a.router-link-active { color: #e0e0e0; background: rgba(255,255,255,0.05); }
</style>
