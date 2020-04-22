import Vue from "vue";
import Vuex from "vuex";
import modules from "./modules";

// Load Vuex
Vue.use(Vuex);

// Create Store from modules array (generated during import)
export default new Vuex.Store({
    modules
});
