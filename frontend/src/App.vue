<template>
  <div id="app">
    <header class="header">
      <div class="container">
        <h1>E-Shield 反爬蟲排隊系統</h1>
      </div>
    </header>
    
    <main class="main">
      <div class="container">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style scoped>
.header {
  background: #007bff;
  color: white;
  padding: 20px 0;
  margin-bottom: 30px;
}

.header h1 {
  font-size: 24px;
  font-weight: 600;
}

.main {
  min-height: calc(100vh - 100px);
}
</style>
