<script setup lang="ts">
import { ref, computed } from 'vue'
const mix = ref(50)
const label = computed(() => mix.value < 50 ? 'Source domain' : 'Unseen domain')
</script>
<template>
  <main>
    <span>CONCEPT DEMO · NOT EXPERIMENTAL RESULTS</span>
    <h1>Across imaging domains</h1>
    <div class="sample" :style="{ filter: `contrast(${0.7 + mix / 100})` }"><i /><b /></div>
    <label>Appearance shift · {{ label }}<input v-model.number="mix" type="range" min="0" max="100" /></label>
    <p>Replace this illustration with your own research visualization.</p>
  </main>
</template>
<style scoped>
main { padding:24px; text-align:center; background:#edf1f2; color:#243c51; font-family:system-ui,sans-serif; min-height:100vh; }span { font-size:10px; letter-spacing:1px; }h1 { font-size:24px; }.sample { width:130px; height:130px; margin:18px auto; border-radius:48%; background:radial-gradient(ellipse,#8e9ba5 30%,#263a48 65%,#bed0d6 68%,#425c70 73%); position:relative; }.sample i,.sample b { position:absolute; top:35%; height:30%; width:18%; border-radius:45%; background:#182c3b; }.sample i { left:28%; }.sample b { right:28%; }label { display:block; font-size:13px; }input { display:block; width:80%; margin:12px auto; }p { font-size:12px; color:#6d7f89; }
</style>
