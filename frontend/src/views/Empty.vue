<template>
  <div class="empty-page">
    <var-space justify="center" direction="column">
      <div class="empty-text" style="font-size: 40px;">ಥ_ಥ</div>
      <div class="empty-text">{{ $t('empty.page_missing', { menu: menuKey }) }}</div>
    </var-space>
  </div>
</template>

<script setup>
// 空页面占位组件

// 从父组件注入当前菜单 key
const menuKey = inject('activeMenu', '')
</script>

<style scoped>
.empty-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #999;
}

.empty-text {
  margin-top: 16px;
  font-size: 16px;
  display: block;
  text-align: center;
}
</style>