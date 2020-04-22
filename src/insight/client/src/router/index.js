import Vue from "vue";
import VueRouter from "vue-router";
import Home from "@/views/Home.vue";
// import { default as features } from "@/utils/features";

Vue.use(VueRouter);

var routes = new Array();

// DEFINING Routes:
// (2 methods)
// 1. webpack's route level code-splitting for lazy-loading
//    this generates a separate chunk (about.[hash].js) for this route
//    if and only if the route is visited, then the chunk is loaded.
// 2. Import at top of this page and then directly specify the component
//    example is "Home" below.

routes.push({
    path: "/",
    name: "home",
    component: Home
});


// Automatic route registration
const requireRoute = require.context(".", false, /\w\.js$/);
requireRoute.keys().forEach(fileName => {
    // Don't match this file as a route module
    if (fileName === "./index.js") return;
    
    // Get component config
    const routeDefinitions = requireRoute(fileName)["routes"];
    if (Array.isArray(routeDefinitions)) {
      // Register component globally
      routes.splice(routes.length,0, ...routeDefinitions)
    }
});

const router = new VueRouter({
  routes
});

export default router;

